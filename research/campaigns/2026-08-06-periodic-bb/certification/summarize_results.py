"""Validate immutable campaign evidence and build the maintained summary.

The summary is deliberately derived from task files, not trusted aggregate
labels. A sharded closure remains pending until an unmodified stock serial
run says ``d_exact: true``. Conversely, a feasible MILP incumbent counts as
a refutation only after its exact source task is joined to a persisted,
verifier-checked submission.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RESULTS = HERE / "results"
TARGETS = HERE / "targets.json"
ENVIRONMENT = RESULTS / "environment.json"
TARGET_KEY_RE = re.compile(r"c\d{7}")
SIDES = ("X", "Z")
TASK_STATUSES = {"proven_infeasible", "feasible_refutation", "unknown", "runner_error"}
SUMMARY_STATUSES = (
    "exact",
    "refuted",
    "sharded_closed_pending_serial",
    "timeout",
    "pending",
)

sys.path.insert(0, str(REPO / "verify"))
import gf2  # noqa: E402

sys.path.insert(0, str(HERE))
import confirm_serial as serial_protocol  # noqa: E402


class EvidenceError(RuntimeError):
    """An actionable inconsistency in persisted certification evidence."""


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return str(path)


def fail(path: Path, message: str) -> None:
    raise EvidenceError(f"{repo_relative(path)}: {message}")


def require(condition: bool, path: Path, message: str) -> None:
    if not condition:
        fail(path, message)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(path, f"cannot read JSON ({exc})")
    require(isinstance(value, dict), path, "top-level JSON value must be an object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        fail(path, f"cannot hash file ({exc})")
    return digest.hexdigest()


def array_sha256(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_nonnegative_number(record: dict, field: str, path: Path) -> float:
    value = record.get(field)
    require(
        is_number(value) and math.isfinite(value) and value >= 0,
        path,
        f"{field} must be finite and non-negative",
    )
    return float(value)


def load_trust_anchor() -> tuple[str, str]:
    environment = read_json(ENVIRONMENT)
    trust = environment.get("trust_anchor")
    require(isinstance(trust, dict), ENVIRONMENT, "missing trust_anchor")

    certifier = REPO / "verify" / "certify.py"
    gf2_path = REPO / "verify" / "gf2.py"
    certifier_hash = sha256(certifier)
    gf2_hash = sha256(gf2_path)
    check_field(trust, "certify_path", "verify/certify.py", ENVIRONMENT)
    check_field(trust, "certify_sha256", certifier_hash, ENVIRONMENT)
    check_field(trust, "gf2_path", "verify/gf2.py", ENVIRONMENT)
    check_field(trust, "gf2_sha256", gf2_hash, ENVIRONMENT)

    recorded_manifest = environment.get("manifest")
    require(isinstance(recorded_manifest, dict), ENVIRONMENT, "missing manifest record")
    check_field(
        recorded_manifest,
        "path",
        repo_relative(TARGETS),
        ENVIRONMENT,
    )
    check_field(recorded_manifest, "sha256", sha256(TARGETS), ENVIRONMENT)
    return certifier_hash, gf2_hash


def binary_matrix(rows: Any, n: int, path: Path, label: str) -> np.ndarray:
    require(isinstance(rows, list), path, f"{label} must be a list")
    matrix = np.zeros((len(rows), n), dtype=np.int8)
    for row_index, support in enumerate(rows):
        require(
            isinstance(support, list),
            path,
            f"{label}[{row_index}] must be a list",
        )
        require(
            all(
                isinstance(q, int)
                and not isinstance(q, bool)
                and 0 <= q < n
                for q in support
            ),
            path,
            f"{label}[{row_index}] contains an invalid qubit",
        )
        require(
            len(support) == len(set(support)),
            path,
            f"{label}[{row_index}] contains duplicate qubits",
        )
        for q in support:
            matrix[row_index, q] ^= 1
    return matrix


def canonical_geometry(target: dict, doc: dict, candidate_path: Path) -> dict:
    n = target["n"]
    checks = doc.get("checks")
    require(isinstance(checks, dict), candidate_path, "checks must be an object")
    hx = binary_matrix(checks.get("X"), n, candidate_path, "checks.X")
    hz = binary_matrix(checks.get("Z"), n, candidate_path, "checks.Z")
    bases = {
        "X": gf2.logical_basis(hx, hz),
        "Z": gf2.logical_basis(hz, hx),
    }
    for side, basis in bases.items():
        require(
            basis.shape == (target["k"], n),
            candidate_path,
            f"stock {side} logical basis has shape {basis.shape}, "
            f"expected {(target['k'], n)}",
        )
    rrefs = {
        "X": gf2.rref(hz)[0],
        "Z": gf2.rref(hx)[0],
    }
    matrix_hashes = {"HX": array_sha256(hx), "HZ": array_sha256(hz)}
    basis_hashes = {side: array_sha256(basis) for side, basis in bases.items()}
    rref_hashes = {side: array_sha256(rref) for side, rref in rrefs.items()}
    tasks = {}
    for side in SIDES:
        check_hash = matrix_hashes["HZ" if side == "X" else "HX"]
        for index, logical in enumerate(bases[side]):
            task_id = f"{side}-{index:04d}"
            tasks[task_id] = {
                "support": np.flatnonzero(logical).tolist(),
                "logical_generator_sha256": array_sha256(logical),
                "check_matrix_sha256": check_hash,
                "rref_sha256": rref_hashes[side],
            }
    return {
        "matrix_sha256": matrix_hashes,
        "logical_basis_sha256": basis_hashes,
        "rref_sha256": rref_hashes,
        "tasks": tasks,
    }


def resolve_evidence_path(raw: Any, owner: Path, field: str) -> Path:
    require(isinstance(raw, str) and raw, owner, f"{field} must be a non-empty repo path")
    path = (REPO / raw).resolve()
    try:
        path.relative_to(REPO.resolve())
    except ValueError:
        fail(owner, f"{field} escapes the repository: {raw!r}")
    return path


def check_field(record: dict, field: str, expected: Any, path: Path) -> None:
    require(
        record.get(field) == expected,
        path,
        f"{field} mismatch: expected {expected!r}, got {record.get(field)!r}",
    )


def validate_manifest(manifest: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    source = resolve_evidence_path(manifest.get("source_ledger"), TARGETS, "source_ledger")
    require(source.is_file(), TARGETS, f"source ledger is missing: {repo_relative(source)}")
    check_field(manifest, "source_ledger_sha256", sha256(source), TARGETS)

    targets = manifest.get("targets")
    require(isinstance(targets, list), TARGETS, "targets must be a list")
    check_field(manifest, "target_count", len(targets), TARGETS)
    advancing_count = sum(item.get("board_advancing") is True for item in targets)
    check_field(manifest, "board_advancing_target_count", advancing_count, TARGETS)

    by_key: dict[str, dict] = {}
    docs: dict[str, dict] = {}
    for target in targets:
        require(isinstance(target, dict), TARGETS, "each target must be an object")
        key = f"c{int(target['candidate_id']):07d}"
        require(key not in by_key, TARGETS, f"duplicate target key {key}")
        candidate = resolve_evidence_path(target.get("candidate"), TARGETS, f"{key} candidate")
        verdict = resolve_evidence_path(target.get("verdict"), TARGETS, f"{key} verdict")
        require(candidate.is_file(), TARGETS, f"{key} candidate is missing: {repo_relative(candidate)}")
        require(verdict.is_file(), TARGETS, f"{key} verdict is missing: {repo_relative(verdict)}")
        check_field(target, "candidate_sha256", sha256(candidate), TARGETS)
        check_field(target, "verdict_sha256", sha256(verdict), TARGETS)
        doc = read_json(candidate)
        expected = (target["n"], target["k"], target["d"])
        observed = (doc.get("n"), doc.get("k"), doc.get("distance", {}).get("d"))
        require(observed == expected, candidate, f"parameter mismatch: expected {expected}, got {observed}")
        for side in SIDES:
            check_field(
                target,
                f"d_{side.lower()}_upper",
                doc.get("distance", {}).get(side, {}).get("value"),
                TARGETS,
            )
        by_key[key] = target
        docs[key] = doc
    return by_key, docs


def parse_utc(raw: Any, path: Path, field: str) -> dt.datetime:
    require(isinstance(raw, str), path, f"{field} must be an ISO timestamp")
    try:
        value = dt.datetime.fromisoformat(raw)
    except ValueError as exc:
        fail(path, f"invalid {field} ({exc})")
    require(value.tzinfo is not None, path, f"{field} must be timezone-aware")
    return value


def collect_campaign_batches(
    targets: dict[str, dict], certifier_hash: str
) -> tuple[dict[str, dict], list[str]]:
    """Load completed campaign batches and identify unclosed batch starts."""
    batches: dict[str, dict] = {}
    batch_dir = RESULTS / "batches"
    for path in sorted(batch_dir.glob("*.json")):
        if path.name.endswith("-start.json"):
            continue
        record = read_json(path)
        keys = record.get("candidate_keys")
        if not isinstance(keys, list) or not any(TARGET_KEY_RE.fullmatch(str(key)) for key in keys):
            # Calibration and timeout-recovery ledgers are separate evidence,
            # not solver batches with independently measured wall time.
            continue
        require(
            all(isinstance(key, str) and TARGET_KEY_RE.fullmatch(key) for key in keys),
            path,
            "campaign batch mixes malformed/non-campaign candidate keys",
        )
        require(len(keys) == len(set(keys)), path, "candidate_keys contains duplicates")
        unknown = sorted(set(keys) - set(targets))
        require(not unknown, path, f"unknown candidate keys: {unknown}")
        stage = record.get("stage")
        require(isinstance(stage, str) and stage, path, "missing stage")
        require(path.name == f"{stage}.json", path, "filename does not match stage")
        require(stage not in batches, path, f"duplicate completed batch stage {stage}")
        check_field(record, "certifier_sha256", certifier_hash, path)
        check_field(record, "candidate_count", len(keys), path)
        require(
            record.get("submitted_task_count") == record.get("completed_task_count"),
            path,
            "submitted/completed task counts differ",
        )
        aggregates = record.get("aggregates")
        require(
            isinstance(aggregates, list) and len(aggregates) == len(keys),
            path,
            "aggregate count does not match candidate_count",
        )
        aggregate_by_key = {}
        for item in aggregates:
            require(isinstance(item, dict), path, "aggregate entry must be an object")
            key = item.get("candidate_key")
            require(key in keys, path, f"aggregate has unexpected candidate {key!r}")
            require(key not in aggregate_by_key, path, f"duplicate aggregate for {key}")
            aggregate_by_key[key] = item
        require(set(aggregate_by_key) == set(keys), path, "aggregate candidate set mismatch")
        expected_status_counts = {
            status: sum(
                item.get("aggregate_status") == status for item in aggregate_by_key.values()
            )
            for status in (
                "apparent_exact_requires_serial_confirmation",
                "refuted",
                "timeout",
            )
        }
        check_field(record, "status_counts", expected_status_counts, path)

        start_path = batch_dir / f"{stage}-start.json"
        require(start_path.is_file(), path, f"missing batch start record {repo_relative(start_path)}")
        start = read_json(start_path)
        for field in (
            "stage",
            "certifier_sha256",
            "workers",
            "task_time_limit_seconds",
            "candidate_keys",
        ):
            check_field(start, field, record.get(field), start_path)
        start_time = parse_utc(record.get("started_at_utc"), path, "started_at_utc")
        finish_time = parse_utc(record.get("finished_at_utc"), path, "finished_at_utc")
        require(finish_time >= start_time, path, "finished_at_utc precedes started_at_utc")
        wall = record.get("wall_seconds")
        require(
            isinstance(wall, (int, float)) and wall >= 0 and math.isfinite(wall),
            path,
            "wall_seconds must be finite and non-negative",
        )
        batches[stage] = {
            "path": path,
            "start_path": start_path,
            "record": record,
            "candidate_keys": set(keys),
            "aggregate_by_key": aggregate_by_key,
            "started": start_time,
            "finished": finish_time,
        }

    orphan_starts = []
    for path in sorted(batch_dir.glob("*-start.json")):
        record = read_json(path)
        keys = record.get("candidate_keys")
        if not isinstance(keys, list) or not any(TARGET_KEY_RE.fullmatch(str(key)) for key in keys):
            continue
        stage = record.get("stage")
        if stage not in batches:
            orphan_starts.append(repo_relative(path))
    return batches, orphan_starts


def witness_candidates(record: dict, doc: dict, path: Path) -> list[dict]:
    """Return independently checked logical incumbents captured by a task."""
    side = record["side"]
    n = int(doc["n"])
    cutoff = int(record["cutoff"])
    logical_raw = record.get("logical_generator_support")
    require(isinstance(logical_raw, list), path, "logical_generator_support must be a list")
    require(
        all(isinstance(q, int) and 0 <= q < n for q in logical_raw),
        path,
        "logical_generator_support contains an invalid qubit",
    )
    require(
        len(logical_raw) == len(set(logical_raw)),
        path,
        "logical_generator_support contains duplicates",
    )
    logical = set(logical_raw)
    checks = doc["checks"]["Z" if side == "X" else "X"]
    valid = []
    calls = record.get("solver_calls", [])
    require(isinstance(calls, list), path, "solver_calls must be a list")
    for call_index, call in enumerate(calls):
        require(isinstance(call, dict), path, f"solver_calls[{call_index}] must be an object")
        witness = call.get("logical_witness")
        if witness is None:
            continue
        require(
            isinstance(witness, dict),
            path,
            f"solver_calls[{call_index}] witness is malformed",
        )
        support_raw = witness.get("support")
        require(
            isinstance(support_raw, list),
            path,
            f"solver_calls[{call_index}] support is malformed",
        )
        require(
            all(isinstance(q, int) and 0 <= q < n for q in support_raw),
            path,
            f"solver_calls[{call_index}] support contains an invalid qubit",
        )
        require(
            len(support_raw) == len(set(support_raw)),
            path,
            f"solver_calls[{call_index}] support contains duplicates",
        )
        support = set(support_raw)
        weight = len(support)
        within_cutoff = weight <= cutoff
        zero_syndrome = all(sum(q in support for q in row) % 2 == 0 for row in checks)
        anticommutes = sum(q in support for q in logical) % 2 == 1
        check_field(witness, "weight", weight, path)
        check_field(witness, "within_cutoff", within_cutoff, path)
        check_field(witness, "zero_syndrome", zero_syndrome, path)
        check_field(witness, "anticommutes_with_logical_row", anticommutes, path)

        raw_x = call.get("x")
        if raw_x is not None:
            require(
                isinstance(raw_x, list) and len(raw_x) >= n,
                path,
                f"solver_calls[{call_index}] x is shorter than n",
            )
            rounded_support = set()
            integral = True
            for q, value in enumerate(raw_x[:n]):
                require(
                    isinstance(value, (int, float)) and math.isfinite(value),
                    path,
                    f"solver_calls[{call_index}] x contains a non-finite value",
                )
                bit = round(value)
                integral = integral and bit in (0, 1) and abs(value - bit) <= 1e-6
                if bit == 1:
                    rounded_support.add(q)
            require(
                rounded_support == support,
                path,
                f"solver_calls[{call_index}] x/support mismatch",
            )
        else:
            integral = False
        fun = call.get("fun")
        objective_matches = (
            isinstance(fun, (int, float))
            and math.isfinite(fun)
            and abs(fun - weight) <= 1e-6
        )
        if (
            integral
            and weight > 0
            and within_cutoff
            and zero_syndrome
            and anticommutes
            and objective_matches
        ):
            valid.append(
                {
                    "call_index": call_index,
                    "support": support_raw,
                    "weight": weight,
                }
            )
    return valid


def validate_task_record(
    path: Path,
    target: dict,
    doc: dict,
    certifier_hash: str,
    gf2_hash: str,
    geometry: dict,
    expected_stage: str,
) -> dict:
    record = read_json(path)
    key = f"c{target['candidate_id']:07d}"
    check_field(record, "candidate_key", key, path)
    check_field(record, "candidate_path", target["candidate"], path)
    check_field(record, "candidate_sha256", target["candidate_sha256"], path)
    check_field(record, "certifier_sha256", certifier_hash, path)
    side = record.get("side")
    require(side in SIDES, path, f"invalid side {side!r}")
    index = record.get("logical_row_index")
    require(
        isinstance(index, int) and 0 <= index < target["k"],
        path,
        f"invalid logical_row_index {index!r}",
    )
    task_id = f"{side}-{index:04d}"
    check_field(record, "task_id", task_id, path)
    require(path.name == f"{task_id}.json", path, "filename/task_id mismatch")
    require(path.parent.parent.name == expected_stage, path, "task is under the wrong stage")
    check_field(record, "cutoff", target[f"d_{side.lower()}_upper"] - 1, path)
    canonical = geometry["tasks"][task_id]
    check_field(record, "logical_generator_support", canonical["support"], path)
    for field in ("logical_generator_sha256", "check_matrix_sha256"):
        if field in record:
            check_field(record, field, canonical[field], path)
    if "gf2_sha256" in record:
        check_field(record, "gf2_sha256", gf2_hash, path)
    preprocessing = record.get("preprocessing")
    if isinstance(preprocessing, dict) and "rref_sha256" in preprocessing:
        check_field(
            preprocessing,
            "rref_sha256",
            canonical["rref_sha256"],
            path,
        )
    budget = record.get("time_limit_seconds")
    require(
        isinstance(budget, (int, float)) and budget > 0 and math.isfinite(budget),
        path,
        "time_limit_seconds must be finite and positive",
    )
    status = record.get("status")
    require(status in TASK_STATUSES, path, f"unknown task status {status!r}")
    valid_witnesses = witness_candidates(record, doc, path)
    stock = record.get("stock_predicate_return")
    if status == "proven_infeasible":
        require(stock is False, path, "proven_infeasible requires stock_predicate_return=false")
        require(not valid_witnesses, path, "infeasibility record also contains a valid incumbent")
    elif status == "feasible_refutation":
        require(valid_witnesses, path, "feasible_refutation has no valid incumbent")
        require(
            stock is True or record.get("status_basis") == "validated_time_limit_incumbent",
            path,
            "feasible_refutation is neither a stock success nor a validated timeout incumbent",
        )
    elif status == "unknown":
        require(stock is None, path, "unknown task has a definitive stock predicate result")
    elif status == "runner_error":
        require(record.get("error") is not None, path, "runner_error has no error payload")
    record["_path"] = path.resolve()
    record["_valid_witnesses"] = valid_witnesses
    return record


def load_attempts(
    target: dict, doc: dict, certifier_hash: str, gf2_hash: str, geometry: dict
) -> tuple[dict, dict[Path, dict]]:
    key = f"c{target['candidate_id']:07d}"
    root = RESULTS / key
    attempts_root = root / "attempts"
    attempts: dict[str, dict] = {}
    tasks_by_path: dict[Path, dict] = {}
    if not attempts_root.is_dir():
        return attempts, tasks_by_path
    for directory in sorted(path for path in attempts_root.iterdir() if path.is_dir()):
        start_path = directory / "run-start.json"
        require(start_path.is_file(), directory, "attempt directory has no run-start.json")
        start = read_json(start_path)
        stage = directory.name
        check_field(start, "stage", stage, start_path)
        check_field(start, "candidate_key", key, start_path)
        check_field(start, "candidate_path", target["candidate"], start_path)
        check_field(start, "candidate_sha256", target["candidate_sha256"], start_path)
        check_field(start, "certifier_sha256", certifier_hash, start_path)
        if "gf2_sha256" in start:
            check_field(start, "gf2_sha256", gf2_hash, start_path)
        check_field(start, "matrix_sha256", geometry["matrix_sha256"], start_path)
        check_field(
            start,
            "logical_basis_sha256",
            geometry["logical_basis_sha256"],
            start_path,
        )
        if "rref_sha256" in start:
            check_field(start, "rref_sha256", geometry["rref_sha256"], start_path)
        check_field(start, "expected_task_count", 2 * target["k"], start_path)
        parameters = start.get("parameters", {})
        for field, expected in (
            ("n", target["n"]),
            ("k", target["k"]),
            ("d", target["d"]),
            ("d_x_upper", target["d_x_upper"]),
            ("d_z_upper", target["d_z_upper"]),
        ):
            check_field(parameters, field, expected, start_path)
        descriptors_raw = start.get("tasks")
        require(isinstance(descriptors_raw, list), start_path, "tasks must be a list")
        descriptors = {}
        for descriptor in descriptors_raw:
            require(isinstance(descriptor, dict), start_path, "task descriptor must be an object")
            task_id = descriptor.get("task_id")
            require(
                isinstance(task_id, str) and task_id not in descriptors,
                start_path,
                f"duplicate/malformed task descriptor {task_id!r}",
            )
            side = descriptor.get("side")
            index = descriptor.get("logical_row_index")
            require(
                side in SIDES and isinstance(index, int),
                start_path,
                f"malformed descriptor {task_id}",
            )
            check_field(descriptor, "task_id", f"{side}-{index:04d}", start_path)
            check_field(
                descriptor,
                "cutoff",
                target[f"d_{side.lower()}_upper"] - 1,
                start_path,
            )
            canonical = geometry["tasks"].get(task_id)
            require(canonical is not None, start_path, f"unknown canonical task {task_id}")
            for field, canonical_field in (
                ("logical_generator_support", "support"),
                ("logical_generator_sha256", "logical_generator_sha256"),
                ("check_matrix_sha256", "check_matrix_sha256"),
            ):
                if field in descriptor:
                    check_field(
                        descriptor,
                        field,
                        canonical[canonical_field],
                        start_path,
                    )
            descriptors[task_id] = descriptor
        expected_ids = {
            f"{side}-{index:04d}" for side in SIDES for index in range(target["k"])
        }
        require(set(descriptors) == expected_ids, start_path, "task descriptor set is incomplete")
        inherited = sum(item.get("inherited") is True for item in descriptors.values())
        check_field(start, "inherited_definitive_task_count", inherited, start_path)
        check_field(start, "new_task_count", len(descriptors) - inherited, start_path)

        task_dir = directory / "tasks"
        physical = {}
        if task_dir.is_dir():
            for task_path in sorted(task_dir.glob("*.json")):
                task = validate_task_record(
                    task_path,
                    target,
                    doc,
                    certifier_hash,
                    gf2_hash,
                    geometry,
                    stage,
                )
                require(task["task_id"] in descriptors, task_path, "task has no run-start descriptor")
                require(task["task_id"] not in physical, task_path, "duplicate physical task result")
                require(
                    descriptors[task["task_id"]].get("inherited") is not True,
                    task_path,
                    "physical result exists for a descriptor marked inherited",
                )
                check_field(
                    task,
                    "time_limit_seconds",
                    start.get("task_time_limit_seconds"),
                    task_path,
                )
                physical[task["task_id"]] = task
                tasks_by_path[task_path.resolve()] = task
        attempts[stage] = {
            "stage": stage,
            "path": directory,
            "start_path": start_path,
            "start": start,
            "descriptors": descriptors,
            "physical": physical,
            "aggregate_path": directory / "aggregate.json",
        }
    return attempts, tasks_by_path


def validate_refutations(
    target: dict,
    doc: dict,
    certifier_hash: str,
    tasks_by_path: dict[Path, dict],
) -> tuple[list[dict], dict[Path, dict]]:
    key = f"c{target['candidate_id']:07d}"
    root = RESULTS / key
    details = []
    by_source: dict[Path, dict] = {}
    refutation_dir = root / "refutation"
    if not refutation_dir.is_dir():
        return details, by_source
    for path in sorted(refutation_dir.glob("*.json")):
        if path.name.endswith((".submission.json", ".verification.json")):
            continue
        index = read_json(path)
        for field, expected in (
            ("candidate_key", key),
            ("candidate_path", target["candidate"]),
            ("candidate_sha256", target["candidate_sha256"]),
            ("certifier_sha256", certifier_hash),
        ):
            check_field(index, field, expected, path)
        side = index.get("side")
        require(side in SIDES, path, f"invalid side {side!r}")
        source = resolve_evidence_path(index.get("source_task_result"), path, "source_task_result")
        require(
            source in tasks_by_path,
            path,
            f"source_task_result is not an exact task record for {key}: {repo_relative(source)}",
        )
        require(source not in by_source, path, f"duplicate refutation index for {repo_relative(source)}")
        source_record = tasks_by_path[source]
        for field in (
            "candidate_key",
            "candidate_path",
            "candidate_sha256",
            "certifier_sha256",
            "task_id",
            "side",
        ):
            check_field(index, field, source_record.get(field), path)
        support = index.get("support")
        weight = index.get("weight")
        matches = [
            witness
            for witness in source_record["_valid_witnesses"]
            if witness["support"] == support and witness["weight"] == weight
        ]
        require(matches, path, "index support/weight does not match a valid source-task incumbent")
        optional_source_hash = index.get("source_task_result_sha256")
        if optional_source_hash is not None:
            check_field(index, "source_task_result_sha256", sha256(source), path)

        submission = resolve_evidence_path(index.get("result_submission"), path, "result_submission")
        require(
            submission.is_file(),
            path,
            f"result submission is missing: {repo_relative(submission)}",
        )
        require(
            submission.parent == refutation_dir.resolve(),
            path,
            "result submission is outside this candidate's refutation directory",
        )
        check_field(index, "result_submission_sha256", sha256(submission), path)
        submitted = read_json(submission)
        for field in ("n", "k", "family", "checks"):
            check_field(submitted, field, doc.get(field), submission)
        submitted_side = submitted.get("distance", {}).get(side, {})
        check_field(submitted_side, "value", weight, submission)
        check_field(submitted_side, "witness", support, submission)
        require(
            weight <= source_record["cutoff"],
            submission,
            "persisted witness exceeds the source task cutoff",
        )

        verification = path.with_name(path.stem + ".verification.json")
        require(
            verification.is_file(),
            path,
            f"missing verifier report; run validate_refutations.py: {repo_relative(verification)}",
        )
        report = read_json(verification)
        require(report.get("ok") is True, verification, "persisted submission did not pass qldpc_verify")
        checks = report.get("checks", [])
        witness_check = f"distance_{side}_witness"
        require(
            any(
                item.get("check") == witness_check and item.get("ok") is True
                for item in checks
            ),
            verification,
            f"verifier report lacks passing {witness_check}",
        )
        computed = report.get("computed", {})
        check_field(computed, "n", target["n"], verification)
        check_field(computed, "k", target["k"], verification)

        by_source[source] = {"path": path, "index": index}
        details.append(
            {
                "index": repo_relative(path),
                "source_task_result": repo_relative(source),
                "source_task_result_sha256": sha256(source),
                "submission": repo_relative(submission),
                "submission_sha256": sha256(submission),
                "verification": repo_relative(verification),
                "verification_sha256": sha256(verification),
                "task_id": index["task_id"],
                "side": side,
                "weight": weight,
            }
        )

    for source, task in tasks_by_path.items():
        if task["_valid_witnesses"] and source not in by_source:
            fail(source, "valid solver incumbent has no exact persisted refutation index/submission")
        if task.get("status") == "feasible_refutation" and source not in by_source:
            fail(source, "feasible_refutation lacks persistence evidence")
    return details, by_source


def effective_task_status(task: dict, refutations_by_source: dict[Path, dict]) -> str:
    if task["_path"] in refutations_by_source:
        return "feasible_refutation"
    return task["status"]


def resolve_attempts(
    target: dict,
    attempts: dict,
    tasks_by_path: dict[Path, dict],
    refutations_by_source: dict[Path, dict],
    batches: dict[str, dict],
    certifier_hash: str,
) -> tuple[list[dict], set[Path]]:
    key = f"c{target['candidate_id']:07d}"
    output = []
    completed_evidence_paths: set[Path] = set()
    for stage, attempt in sorted(attempts.items()):
        resolved = {}
        missing = []
        for task_id, descriptor in attempt["descriptors"].items():
            if task_id in attempt["physical"]:
                task = attempt["physical"][task_id]
            elif descriptor.get("inherited") is True:
                source = resolve_evidence_path(
                    descriptor.get("evidence_path"),
                    attempt["start_path"],
                    f"{task_id} evidence_path",
                )
                require(
                    source in tasks_by_path,
                    attempt["start_path"],
                    f"{task_id} inherited evidence is not a validated task: {repo_relative(source)}",
                )
                task = tasks_by_path[source]
                check_field(task, "task_id", task_id, source)
                require(
                    effective_task_status(task, refutations_by_source)
                    in {"proven_infeasible", "feasible_refutation"},
                    attempt["start_path"],
                    f"{task_id} inherited evidence is not definitive",
                )
            else:
                missing.append(task_id)
                continue
            resolved[task_id] = task

        in_complete_batch = stage in batches and key in batches[stage]["candidate_keys"]
        aggregate_path = attempt["aggregate_path"]
        aggregate_exists = aggregate_path.is_file()
        if in_complete_batch:
            require(
                not missing,
                attempt["start_path"],
                f"completed batch is missing task evidence: {missing[:8]}",
            )
            require(aggregate_exists, attempt["start_path"], "completed batch has no aggregate.json")
            check_field(
                attempt["start"],
                "new_task_count",
                len(attempt["physical"]),
                attempt["start_path"],
            )
        else:
            require(
                len(attempt["physical"]) <= attempt["start"]["new_task_count"],
                attempt["start_path"],
                "incomplete attempt has more physical tasks than new_task_count",
            )

        if aggregate_exists:
            aggregate = read_json(aggregate_path)
            for field, expected in (
                ("stage", stage),
                ("candidate_key", key),
                ("candidate_path", target["candidate"]),
                ("candidate_sha256", target["candidate_sha256"]),
                ("certifier_sha256", certifier_hash),
                ("task_count", 2 * target["k"]),
            ):
                check_field(aggregate, field, expected, aggregate_path)
            require(not missing, aggregate_path, "aggregate exists but task evidence is missing")
            aggregate_tasks = aggregate.get("tasks")
            require(
                isinstance(aggregate_tasks, list)
                and len(aggregate_tasks) == 2 * target["k"],
                aggregate_path,
                "aggregate task list has wrong length",
            )
            observed = {}
            for item in aggregate_tasks:
                task_id = item.get("task_id")
                require(
                    task_id in resolved and task_id not in observed,
                    aggregate_path,
                    f"duplicate/unexpected aggregate task {task_id!r}",
                )
                task = resolved[task_id]
                raw_status = task["status"]
                effective_status = effective_task_status(task, refutations_by_source)
                status = item.get("status")
                # Older aggregates predate timeout-incumbent recovery and
                # correctly preserve the source task's then-unknown status.
                # Newer aggregates promote the same joined evidence.  Both
                # are valid immutable historical snapshots; the maintained
                # summary below always uses effective_status.
                require(
                    status in {raw_status, effective_status},
                    aggregate_path,
                    f"status mismatch for {task_id}: expected one of "
                    f"{sorted({raw_status, effective_status})}, got {status!r}",
                )
                check_field(item, "side", task["side"], aggregate_path)
                check_field(item, "evidence_path", repo_relative(task["_path"]), aggregate_path)
                observed[task_id] = status
            require(set(observed) == set(resolved), aggregate_path, "aggregate task set mismatch")
            expected_sides = {}
            for side in SIDES:
                statuses = [
                    observed[f"{side}-{index:04d}"] for index in range(target["k"])
                ]
                counts = {
                    status: statuses.count(status)
                    for status in (
                        "proven_infeasible",
                        "feasible_refutation",
                        "unknown",
                        "runner_error",
                        "missing",
                    )
                }
                if counts["feasible_refutation"]:
                    side_status = "refuted"
                elif counts["proven_infeasible"] == len(statuses):
                    side_status = "exact"
                else:
                    side_status = "timeout"
                expected_sides[side] = {
                    "status": side_status,
                    "task_count": len(statuses),
                    "counts": counts,
                }
            check_field(aggregate, "sides", expected_sides, aggregate_path)
            if any(value["status"] == "refuted" for value in expected_sides.values()):
                expected_aggregate = "refuted"
            elif all(value["status"] == "exact" for value in expected_sides.values()):
                expected_aggregate = "apparent_exact_requires_serial_confirmation"
            else:
                expected_aggregate = "timeout"
            check_field(aggregate, "aggregate_status", expected_aggregate, aggregate_path)

            if in_complete_batch:
                entry = batches[stage]["aggregate_by_key"][key]
                check_field(
                    entry,
                    "aggregate_path",
                    repo_relative(aggregate_path),
                    batches[stage]["path"],
                )
                check_field(
                    entry,
                    "aggregate_status",
                    aggregate["aggregate_status"],
                    batches[stage]["path"],
                )
                check_field(entry, "sides", aggregate["sides"], batches[stage]["path"])

        complete = in_complete_batch and aggregate_exists and not missing
        if complete:
            completed_evidence_paths.update(task["_path"] for task in resolved.values())

        output.append(
            {
                "stage": stage,
                "run_start": repo_relative(attempt["start_path"]),
                "aggregate": repo_relative(aggregate_path) if aggregate_exists else None,
                "complete": complete,
                "orphan_incomplete": not in_complete_batch,
                "expected_task_count": 2 * target["k"],
                "new_task_count": attempt["start"]["new_task_count"],
                "persisted_new_task_count": len(attempt["physical"]),
                "inherited_definitive_task_count": attempt["start"][
                    "inherited_definitive_task_count"
                ],
                "task_time_limit_seconds": attempt["start"].get("task_time_limit_seconds"),
                "missing_task_count": len(missing),
            }
        )
    return output, completed_evidence_paths


def validate_serial_records(
    target: dict, doc: dict, certifier_hash: str, gf2_hash: str
) -> list[dict]:
    key = f"c{target['candidate_id']:07d}"
    root = RESULTS / key
    exact_records = []
    serial_root = root / "serial-confirmation"
    if not serial_root.exists():
        return exact_records
    require(serial_root.is_dir(), serial_root, "serial-confirmation is not a directory")
    for directory in sorted(serial_root.iterdir()):
        require(
            directory.is_dir() and not directory.is_symlink(),
            directory,
            "unexpected non-directory serial-confirmation artifact",
        )
        stage = directory.name
        start_path = directory / "run-start.json"
        path = directory / "record.json"
        authoritative_path = directory / "authoritative-output.json"
        require(start_path.is_file(), directory, "serial attempt has no run-start.json")
        require(not start_path.is_symlink(), start_path, "run-start.json is a symlink")
        start = read_json(start_path)
        check_field(start, "schema_version", 1, start_path)
        check_field(start, "confirmation_stage", stage, start_path)
        check_field(start, "candidate_id", target["candidate_id"], start_path)
        check_field(start, "candidate", target["candidate"], start_path)
        check_field(start, "candidate_sha256", target["candidate_sha256"], start_path)
        check_field(start, "certifier_sha256", certifier_hash, start_path)
        check_field(start, "gf2_sha256", gf2_hash, start_path)
        budget = start.get("per_task_time_limit_seconds")
        require(
            is_number(budget) and math.isfinite(budget) and budget > 0,
            start_path,
            "per_task_time_limit_seconds must be finite and positive",
        )
        command = start.get("command")
        require(
            isinstance(command, list)
            and len(command) == 5
            and isinstance(command[0], str)
            and Path(command[0]).is_absolute()
            and command[1:] == [
                "verify/certify.py",
                target["candidate"],
                "--tlim",
                str(budget),
            ],
            start_path,
            "serial command is not the exact stock verify/certify.py invocation",
        )
        parse_utc(start.get("started_at_utc"), start_path, "started_at_utc")

        if not path.exists():
            require(
                not authoritative_path.exists(),
                authoritative_path,
                "authoritative output exists before the serial record",
            )
            continue
        require(
            path.is_file() and not path.is_symlink(),
            path,
            "record.json is not a regular file",
        )
        record = read_json(path)
        require(
            serial_protocol.stable_start_fields(record)
            == serial_protocol.stable_start_fields(start),
            path,
            "serial record identity differs from run-start.json",
        )

        stdout = record.get("stdout")
        parsed: Any = None
        parse_error = None
        if isinstance(stdout, str) and stdout:
            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError as exc:
                parse_error = str(exc)
        else:
            parse_error = "stdout was empty or not a string"
        validation_errors, _, _ = serial_protocol.validate_certifier_output(
            parsed, doc
        )
        if parse_error:
            validation_errors.insert(0, f"invalid JSON: {parse_error}")
        identity_after = record.get("identity_after")
        require(isinstance(identity_after, dict), path, "serial record has no post-run identity")
        expected_identity = {
            "candidate_sha256": target["candidate_sha256"],
            "certifier_sha256": certifier_hash,
            "gf2_sha256": gf2_hash,
        }
        identity_errors = [
            field
            for field, expected in expected_identity.items()
            if identity_after.get(field) != expected
        ]
        should_have_authoritative = (
            record.get("returncode") == 0
            and not validation_errors
            and not identity_errors
        )
        if should_have_authoritative:
            require(
                authoritative_path.is_file() and not authoritative_path.is_symlink(),
                authoritative_path,
                "valid serial record lacks a regular authoritative-output.json",
            )
        else:
            require(
                not authoritative_path.exists(),
                authoritative_path,
                "invalid serial record has an authoritative output",
            )
        try:
            record = serial_protocol.validate_completed_record(
                path, authoritative_path, start, doc
            )
        except RuntimeError as exc:
            fail(path, f"invalid completed serial record ({exc})")

        started = parse_utc(record.get("started_at_utc"), path, "started_at_utc")
        finished = parse_utc(record.get("finished_at_utc"), path, "finished_at_utc")
        require(finished >= started, path, "finished_at_utc precedes started_at_utc")
        validate_nonnegative_number(record, "duration_seconds", path)
        validate_nonnegative_number(record, "parent_process_cpu_seconds", path)
        validate_nonnegative_number(record, "child_process_user_seconds", path)
        validate_nonnegative_number(record, "child_process_system_seconds", path)
        validate_nonnegative_number(record, "child_process_cpu_seconds", path)

        claims_exact = record.get("d_exact") is True
        if claims_exact:
            require(
                record.get("returncode") == 0,
                path,
                "d_exact record has nonzero returncode",
            )
            check_field(record, "status", "exact", path)
            check_field(record, "identity_errors", [], path)
            check_field(record, "execution_error", None, path)
            authoritative = read_json(authoritative_path)
            check_field(record, "certifier_output", authoritative, path)
            require(
                parsed == authoritative,
                path,
                "stdout does not match authoritative-output.json",
            )
            exact_records.append(
                {
                    "record": repo_relative(path),
                    "record_sha256": sha256(path),
                    "authoritative_output": repo_relative(authoritative_path),
                    "authoritative_output_sha256": sha256(authoritative_path),
                    "finished_at_utc": record.get("finished_at_utc"),
                }
            )
    return exact_records


def summarize_target(
    target: dict,
    doc: dict,
    certifier_hash: str,
    gf2_hash: str,
    batches: dict[str, dict],
) -> tuple[dict, dict[Path, dict]]:
    key = f"c{target['candidate_id']:07d}"
    candidate_path = resolve_evidence_path(
        target["candidate"], TARGETS, f"{key} candidate"
    )
    geometry = canonical_geometry(target, doc, candidate_path)
    attempts, tasks_by_path = load_attempts(
        target, doc, certifier_hash, gf2_hash, geometry
    )
    refutation_details, refutations_by_source = validate_refutations(
        target, doc, certifier_hash, tasks_by_path
    )
    attempt_details, completed_evidence_paths = resolve_attempts(
        target,
        attempts,
        tasks_by_path,
        refutations_by_source,
        batches,
        certifier_hash,
    )
    serial_records = validate_serial_records(
        target, doc, certifier_hash, gf2_hash
    )

    by_task: dict[str, list[dict]] = {
        f"{side}-{index:04d}": []
        for side in SIDES
        for index in range(target["k"])
    }
    for task in tasks_by_path.values():
        by_task[task["task_id"]].append(task)
    for task_id, records in by_task.items():
        logical_rows = {tuple(record["logical_generator_support"]) for record in records}
        require(
            len(logical_rows) <= 1,
            RESULTS / key,
            f"logical generator changed across attempts for {task_id}",
        )
        statuses = {
            effective_task_status(record, refutations_by_source) for record in records
        }
        if "proven_infeasible" in statuses and "feasible_refutation" in statuses:
            paths = [repo_relative(record["_path"]) for record in records]
            fail(RESULTS / key, f"contradictory definitive evidence for {task_id}: {paths}")

    exact = bool(serial_records)
    refuted_sides = {detail["side"] for detail in refutation_details}
    require(
        not (exact and refuted_sides),
        RESULTS / key,
        "valid stock exact confirmation contradicts a persisted refutation",
    )
    has_complete_attempt = any(item["complete"] for item in attempt_details)
    side_status = {}
    side_evidence = {}
    for side in SIDES:
        task_ids = [f"{side}-{index:04d}" for index in range(target["k"])]
        proven_ids = [
            task_id
            for task_id in task_ids
            if any(
                effective_task_status(record, refutations_by_source)
                == "proven_infeasible"
                for record in by_task[task_id]
                if record["_path"] in completed_evidence_paths
            )
        ]
        all_persisted_proven_ids = [
            task_id
            for task_id in task_ids
            if any(
                effective_task_status(record, refutations_by_source)
                == "proven_infeasible"
                for record in by_task[task_id]
            )
        ]
        if exact:
            status = "exact"
        elif side in refuted_sides:
            status = "refuted"
        elif len(proven_ids) == target["k"]:
            status = "sharded_closed_pending_serial"
        elif has_complete_attempt:
            status = "timeout"
        else:
            status = "pending"
        side_status[side] = status
        side_evidence[side] = {
            "required_task_count": target["k"],
            "proven_infeasible_task_count": len(proven_ids),
            "all_persisted_proven_infeasible_task_count": len(
                all_persisted_proven_ids
            ),
            "persisted_refutation_count": sum(
                detail["side"] == side for detail in refutation_details
            ),
        }

    if exact:
        status = "exact"
    elif refuted_sides:
        status = "refuted"
    elif all(
        value == "sharded_closed_pending_serial" for value in side_status.values()
    ):
        status = "sharded_closed_pending_serial"
    elif any(value == "timeout" for value in side_status.values()):
        status = "timeout"
    else:
        status = "pending"

    task_records = list(tasks_by_path.values())
    budgets = sorted({record["time_limit_seconds"] for record in task_records})
    orphan_attempts = [
        item["stage"] for item in attempt_details if item["orphan_incomplete"]
    ]
    row = {
        "candidate_id": target["candidate_id"],
        "candidate_key": key,
        "n": target["n"],
        "k": target["k"],
        "d": target["d"],
        "status": status,
        "side_status": side_status,
        "side_evidence": side_evidence,
        "timeout_budgets_seconds": budgets,
        "solver_wall_seconds": sum(
            record.get("duration_seconds", 0.0) for record in task_records
        ),
        "solver_cpu_seconds": sum(
            record.get("process_cpu_seconds", 0.0) for record in task_records
        ),
        "task_result_count": len(task_records),
        "attempts": attempt_details,
        "orphan_incomplete_attempts": orphan_attempts,
        "serial_confirmation": serial_records[-1]["record"] if serial_records else None,
        "serial_confirmations": serial_records,
        "refutation_evidence": [detail["index"] for detail in refutation_details],
        "refutation_details": refutation_details,
    }
    return row, tasks_by_path


def interval_union_seconds(intervals: list[tuple[dt.datetime, dt.datetime]]) -> float:
    if not intervals:
        return 0.0
    ordered = sorted(intervals)
    start, end = ordered[0]
    total = 0.0
    for next_start, next_end in ordered[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += (end - start).total_seconds()
            start, end = next_start, next_end
    return total + (end - start).total_seconds()


def finalize_batch_accounting(
    batches: dict[str, dict], all_tasks: dict[Path, dict]
) -> tuple[list[dict], dict]:
    details = []
    counted_paths: set[Path] = set()
    for stage, batch in sorted(batches.items(), key=lambda item: item[1]["started"]):
        record = batch["record"]
        task_paths = set()
        inherited = 0
        for key in batch["candidate_keys"]:
            attempt_root = RESULTS / key / "attempts" / stage
            start = read_json(attempt_root / "run-start.json")
            inherited += int(start["inherited_definitive_task_count"])
            task_paths.update(
                path.resolve() for path in (attempt_root / "tasks").glob("*.json")
            )
        require(
            len(task_paths) == record["submitted_task_count"],
            batch["path"],
            f"submitted_task_count={record['submitted_task_count']} but found {len(task_paths)} new task files",
        )
        overlap = task_paths & counted_paths
        require(
            not overlap,
            batch["path"],
            "new task files were already counted by another batch: "
            f"{[repo_relative(path) for path in sorted(overlap)[:5]]}",
        )
        missing = task_paths - set(all_tasks)
        require(
            not missing,
            batch["path"],
            "batch contains unvalidated task files: "
            f"{[repo_relative(path) for path in sorted(missing)[:5]]}",
        )
        counted_paths.update(task_paths)
        task_records = [all_tasks[path] for path in sorted(task_paths)]
        new_cpu = sum(item.get("process_cpu_seconds", 0.0) for item in task_records)
        new_wall = sum(item.get("duration_seconds", 0.0) for item in task_records)
        budgets = sorted({item["time_limit_seconds"] for item in task_records})
        if task_records:
            require(
                budgets == [record["task_time_limit_seconds"]],
                batch["path"],
                f"new task budgets {budgets} disagree with batch budget",
            )
        details.append(
            {
                "stage": stage,
                "batch_result": repo_relative(batch["path"]),
                "batch_start": repo_relative(batch["start_path"]),
                "candidate_count": len(batch["candidate_keys"]),
                "workers": record["workers"],
                "task_time_limit_seconds": record["task_time_limit_seconds"],
                "wall_seconds": record["wall_seconds"],
                "new_task_count": len(task_paths),
                "inherited_definitive_task_count": inherited,
                "new_task_wall_seconds": new_wall,
                "new_task_cpu_seconds": new_cpu,
                "reported_task_wall_seconds_sum": record.get("task_wall_seconds_sum"),
                "reported_task_cpu_seconds_sum": record.get("task_cpu_seconds_sum"),
            }
        )
    accounting = {
        "batch_wall_seconds": interval_union_seconds(
            [(batch["started"], batch["finished"]) for batch in batches.values()]
        ),
        "batch_wall_seconds_reported_sum": sum(
            batch["record"]["wall_seconds"] for batch in batches.values()
        ),
        "new_task_wall_seconds": sum(
            item["new_task_wall_seconds"] for item in details
        ),
        "new_task_cpu_seconds": sum(item["new_task_cpu_seconds"] for item in details),
        "new_task_count": sum(item["new_task_count"] for item in details),
        "inherited_definitive_task_count": sum(
            item["inherited_definitive_task_count"] for item in details
        ),
        "task_time_budgets_seconds": sorted(
            {item["task_time_limit_seconds"] for item in details}
        ),
    }
    orphan_paths = set(all_tasks) - counted_paths
    accounting.update(
        {
            "orphan_new_task_count": len(orphan_paths),
            "orphan_new_task_wall_seconds": sum(
                all_tasks[path].get("duration_seconds", 0.0)
                for path in sorted(orphan_paths)
            ),
            "orphan_new_task_cpu_seconds": sum(
                all_tasks[path].get("process_cpu_seconds", 0.0)
                for path in sorted(orphan_paths)
            ),
        }
    )
    return details, accounting


def atomic_write(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(content)
    os.replace(temporary, path)


def main() -> None:
    manifest = read_json(TARGETS)
    targets, docs = validate_manifest(manifest)
    certifier_hash, gf2_hash = load_trust_anchor()
    batches, orphan_batch_starts = collect_campaign_batches(targets, certifier_hash)

    rows = []
    all_tasks: dict[Path, dict] = {}
    for key, target in targets.items():
        if target["board_advancing"] is not True:
            continue
        row, target_tasks = summarize_target(
            target, docs[key], certifier_hash, gf2_hash, batches
        )
        overlap = set(all_tasks) & set(target_tasks)
        require(not overlap, RESULTS, "task result was assigned to more than one candidate")
        all_tasks.update(target_tasks)
        rows.append(row)
    rows.sort(key=lambda item: item["candidate_id"])

    batch_details, accounting = finalize_batch_accounting(batches, all_tasks)
    counts = {
        status: sum(row["status"] == status for row in rows)
        for status in SUMMARY_STATUSES
    }
    summary = {
        "schema_version": 2,
        "evidence_validation": {
            "passed": True,
            "manifest_sha256": sha256(TARGETS),
            "source_ledger_sha256": manifest["source_ledger_sha256"],
            "certifier_sha256": certifier_hash,
            "gf2_sha256": gf2_hash,
            "candidate_hashes_verified": len(targets),
            "task_records_verified": len(all_tasks),
            "canonical_logical_rows_verified": len(all_tasks),
            "refutation_indexes_verified": sum(
                len(row["refutation_details"]) for row in rows
            ),
            "stock_serial_exact_records_verified": sum(
                len(row["serial_confirmations"]) for row in rows
            ),
        },
        "target_count": len(rows),
        "counts": counts,
        "batch_wall_seconds": accounting["batch_wall_seconds"],
        "batch_wall_seconds_reported_sum": accounting[
            "batch_wall_seconds_reported_sum"
        ],
        "new_task_wall_seconds": accounting["new_task_wall_seconds"],
        "new_task_cpu_seconds": accounting["new_task_cpu_seconds"],
        # Backward-compatible aliases; these now explicitly count physical
        # task files once rather than inherited aggregate references.
        "solver_wall_seconds": accounting["new_task_wall_seconds"],
        "solver_cpu_seconds": accounting["new_task_cpu_seconds"],
        "new_task_count": accounting["new_task_count"],
        "inherited_definitive_task_count": accounting[
            "inherited_definitive_task_count"
        ],
        "orphan_new_task_count": accounting["orphan_new_task_count"],
        "orphan_new_task_wall_seconds": accounting["orphan_new_task_wall_seconds"],
        "orphan_new_task_cpu_seconds": accounting["orphan_new_task_cpu_seconds"],
        "task_time_budgets_seconds": accounting["task_time_budgets_seconds"],
        "batches": [item["stage"] for item in batch_details],
        "batch_details": batch_details,
        "orphan_incomplete_batch_starts": orphan_batch_starts,
        "targets": rows,
    }
    atomic_write(RESULTS / "summary.json", json.dumps(summary, indent=2) + "\n")

    lines = [
        "# Periodic BB exact-certification summary",
        "",
        (
            f"Targets: {len(rows)}; exact: {counts['exact']}; refuted: {counts['refuted']}; "
            f"sharded closed pending serial: {counts['sharded_closed_pending_serial']}; "
            f"timeout: {counts['timeout']}; pending: {counts['pending']}."
        ),
        "",
        (
            f"Non-overlapping batch wall time: {accounting['batch_wall_seconds']:.1f} s; "
            f"summed new-task wall time: {accounting['new_task_wall_seconds']:.1f} s; "
            f"summed new-task CPU time: {accounting['new_task_cpu_seconds']:.1f} s."
        ),
        "",
        (
            "A side marked `sharded_closed_pending_serial` has all logical-row cutoff MILPs "
            "proven infeasible, but the candidate is `exact` only after a hash-matched, persisted "
            "stock `verify/certify.py` result has `d_exact: true`."
        ),
        "",
        "## Completed batches",
        "",
        "| stage | budget (s) | workers | candidates | new tasks | inherited | wall (s) | new-task CPU (s) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in batch_details:
        lines.append(
            f"| {item['stage']} | {item['task_time_limit_seconds']:g} | {item['workers']} | "
            f"{item['candidate_count']} | {item['new_task_count']} | "
            f"{item['inherited_definitive_task_count']} | {item['wall_seconds']:.1f} | "
            f"{item['new_task_cpu_seconds']:.1f} |"
        )
    if orphan_batch_starts:
        lines.extend(["", "Incomplete batch starts (not counted as timeouts):"])
        lines.extend(f"- `{path}`" for path in orphan_batch_starts)
    if accounting["orphan_new_task_count"]:
        lines.extend(
            [
                "",
                (
                    f"Persisted tasks outside completed batches: "
                    f"{accounting['orphan_new_task_count']} "
                    f"({accounting['orphan_new_task_cpu_seconds']:.1f} CPU s); "
                    "retained as evidence but not counted as completed-batch timeouts."
                ),
            ]
        )
    lines.extend(
        [
            "",
            "## Targets",
            "",
            "| target | parameters | X | Z | overall | budgets (s) | new-task wall (s) | CPU (s) |",
            "|---|---:|---|---|---|---:|---:|---:|",
        ]
    )
    for row in rows:
        budgets = ",".join(
            f"{value:g}" for value in row["timeout_budgets_seconds"]
        ) or "—"
        lines.append(
            f"| {row['candidate_key']} | [[{row['n']},{row['k']},{row['d']}]] | "
            f"{row['side_status']['X']} | {row['side_status']['Z']} | {row['status']} | "
            f"{budgets} | {row['solver_wall_seconds']:.1f} | {row['solver_cpu_seconds']:.1f} |"
        )
    atomic_write(RESULTS / "SUMMARY.md", "\n".join(lines) + "\n")
    print(json.dumps({"counts": counts, "accounting": accounting}, indent=2))


if __name__ == "__main__":
    main()
