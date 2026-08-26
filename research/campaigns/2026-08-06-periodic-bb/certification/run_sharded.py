"""Process-sharded wrapper around the unmodified stock exact predicate.

Each worker calls ``verify/certify.py::_exists_lighter`` for exactly one side
and one logical-basis row.  Results are written atomically as soon as the
corresponding future completes.  Definitive results from earlier stages may be
reused; timeouts and runner errors remain eligible for a larger later budget.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import multiprocessing as mp
import os
import re
import resource
import subprocess
import sys
import time
import traceback
import warnings
from pathlib import Path
from typing import Any, Iterator


for _thread_var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_thread_var] = "1"

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
VERIFY = REPO / "verify"
RESULTS = HERE / "results"
MANIFEST_PATH = HERE / "targets.json"
PRIORITY_IDS = (60702, 56213, 58579, 60754, 50584, 48487, 49220, 45113, 20168, 20283)
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

sys.path.insert(0, str(VERIFY))
import certify  # noqa: E402
import gf2  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def array_sha256(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def validate_artifact_name(value: str, *, label: str = "stage") -> str:
    """Require a single, unambiguous filename component for result artifacts."""
    if not SAFE_NAME.fullmatch(value) or value.endswith("-start"):
        raise ValueError(
            f"invalid {label} {value!r}; use 1-128 alphanumeric/._- characters "
            "and do not end it with '-start'"
        )
    return value


def fsync_directory(path: Path) -> None:
    """Make a completed atomic rename durable on POSIX filesystems."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish_new_file(temporary: Path, path: Path) -> None:
    """Atomically publish ``temporary`` without ever replacing ``path``."""
    try:
        os.link(temporary, path)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite {path}") from exc
    fsync_directory(path.parent)
    temporary.unlink()
    fsync_directory(path.parent)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with temporary.open("x") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        publish_new_file(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def proc_memory_bytes() -> dict[str, int | None]:
    values: dict[str, int | None] = {"rss": None, "high_water": None}
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                values["rss"] = int(line.split()[1]) * 1024
            elif line.startswith("VmHWM:"):
                values["high_water"] = int(line.split()[1]) * 1024
    except OSError:
        pass
    return values


def serialize_solver_result(
    result: Any,
    n: int,
    H: np.ndarray,
    logical: np.ndarray,
    cap: int,
) -> dict:
    def scalar(name: str) -> Any:
        value = getattr(result, name, None)
        if isinstance(value, np.generic):
            return value.item()
        return value

    x = getattr(result, "x", None)
    serialized = {
        "success": bool(getattr(result, "success", False)),
        "status": int(getattr(result, "status", -1)),
        "message": str(getattr(result, "message", "")),
        "fun": scalar("fun"),
        "mip_node_count": scalar("mip_node_count"),
        "mip_dual_bound": scalar("mip_dual_bound"),
        "mip_gap": scalar("mip_gap"),
        "nit": scalar("nit"),
    }
    if x is not None:
        raw = np.asarray(x)
        bits = np.rint(raw[:n]).astype(np.uint8)
        support = np.flatnonzero(bits).astype(int).tolist()
        serialized["x"] = raw.tolist()
        serialized["logical_witness"] = {
            "support": support,
            "weight": len(support),
            "within_cutoff": len(support) <= cap,
            "zero_syndrome": bool(np.all((H @ bits) % 2 == 0)),
            "anticommutes_with_logical_row": bool(int(logical @ bits) % 2 == 1),
        }
    else:
        serialized["x"] = None
        serialized["logical_witness"] = None
    return serialized


def logical_support(logical: np.ndarray) -> list[int]:
    return np.flatnonzero(logical).astype(int).tolist()


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def valid_solver_witnesses(record: dict, task: dict | None = None) -> list[dict]:
    """Return captured incumbents that independently prove a refutation.

    Older task records only contain the three precomputed validation booleans.
    When the task matrices are available, recompute every property from the
    persisted support instead of trusting those booleans.
    """
    valid = []
    for call in record.get("solver_calls", []):
        witness = call.get("logical_witness")
        if not isinstance(witness, dict):
            continue
        support = witness.get("support")
        if (
            not isinstance(support, list)
            or not support
            or any(type(qubit) is not int for qubit in support)
            or len(set(support)) != len(support)
            or witness.get("weight") != len(support)
        ):
            continue
        if task is None:
            if all(
                witness.get(key) is True
                for key in (
                    "within_cutoff",
                    "zero_syndrome",
                    "anticommutes_with_logical_row",
                )
            ):
                valid.append(witness)
            continue

        H = task["H"]
        logical = task["logical"]
        n = int(H.shape[1])
        if any(qubit < 0 or qubit >= n for qubit in support):
            continue
        bits = np.zeros(n, dtype=np.int8)
        bits[support] = 1
        if (
            len(support) <= int(task["cutoff"])
            and bool(np.all((H @ bits) % 2 == 0))
            and int(logical @ bits) % 2 == 1
        ):
            valid.append(witness)
    return valid


def has_valid_witness(record: dict, task: dict | None = None) -> bool:
    """Whether captured solver output contains a directly checkable logical."""
    return bool(valid_solver_witnesses(record, task))


def evidence_status(record: dict, task: dict | None = None) -> str:
    """Promote a validated incumbent even when HiGHS stopped at its limit."""
    if has_valid_witness(record, task):
        return "feasible_refutation"
    return record.get("status", "missing")


def task_descriptor(task: dict) -> dict:
    return {
        "task_id": task["task_id"],
        "side": task["side"],
        "logical_row_index": task["logical_row_index"],
        "cutoff": task["cutoff"],
        "check_matrix_sha256": array_sha256(task["H"]),
        "logical_generator_sha256": array_sha256(task["logical"]),
        "logical_generator_support": logical_support(task["logical"]),
    }


def validate_task_record(
    record: dict,
    task: dict,
    *,
    require_runtime_identity: bool,
) -> str:
    """Validate a task record before resume, reuse, aggregation, or recovery."""
    schema_version = record.get("schema_version")
    if type(schema_version) is not int or schema_version not in {1, 2}:
        raise RuntimeError(f"unsupported task schema for {task['task_id']}")
    if require_runtime_identity and schema_version != 2:
        raise RuntimeError(f"resume requires task schema 2: {task['task_id']}")
    expected = {
        "candidate_key": task["candidate_key"],
        "candidate_path": task["candidate_path"],
        "candidate_sha256": task["candidate_sha256"],
        "certifier_sha256": task["certifier_sha256"],
        "task_id": task["task_id"],
        "side": task["side"],
        "logical_row_index": task["logical_row_index"],
        "logical_generator_support": logical_support(task["logical"]),
        "cutoff": task["cutoff"],
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"task record mismatch for {task['task_id']}: {key}")

    derived_expected = {
        "gf2_sha256": task["gf2_sha256"],
        "logical_generator_sha256": array_sha256(task["logical"]),
        "check_matrix_sha256": array_sha256(task["H"]),
    }
    if schema_version == 2:
        for key, value in derived_expected.items():
            if record.get(key) != value:
                raise RuntimeError(f"task record mismatch for {task['task_id']}: {key}")
        if not is_sha256(record.get("runner_sha256")):
            raise RuntimeError(f"invalid runner provenance for {task['task_id']}")
        time_limit = record.get("time_limit_seconds")
        if (
            not isinstance(time_limit, (int, float))
            or isinstance(time_limit, bool)
            or not np.isfinite(time_limit)
            or time_limit <= 0
        ):
            raise RuntimeError(f"invalid time limit provenance for {task['task_id']}")
        if require_runtime_identity:
            if record["runner_sha256"] != task["runner_sha256"]:
                raise RuntimeError(
                    f"task record mismatch for {task['task_id']}: runner_sha256"
                )
            if time_limit != task["time_limit_seconds"]:
                raise RuntimeError(
                    f"task record mismatch for {task['task_id']}: time_limit_seconds"
                )
    else:
        # Older immutable evidence predates these hashes. If present, it must
        # still agree with the task reconstructed from current trusted files.
        for key, value in derived_expected.items():
            if key in record and record[key] != value:
                raise RuntimeError(f"task record mismatch for {task['task_id']}: {key}")

    status = evidence_status(record, task)
    if record.get("status") not in {
        "feasible_refutation",
        "proven_infeasible",
        "unknown",
        "runner_error",
    }:
        raise RuntimeError(f"invalid task status for {task['task_id']}")
    if record.get("status") == "feasible_refutation" and not has_valid_witness(record, task):
        raise RuntimeError(f"refutation task has no valid witness: {task['task_id']}")
    if record.get("status") == "proven_infeasible":
        solver_statuses = [call.get("status") for call in record.get("solver_calls", [])]
        if record.get("stock_predicate_return") is not False or 2 not in solver_statuses:
            raise RuntimeError(f"invalid infeasibility evidence: {task['task_id']}")
    return status


def run_one_task(task: dict) -> dict:
    """Worker entry point: call the stock predicate on one logical row."""
    started_at = utc_now()
    wall_start = time.monotonic()
    cpu_start = time.process_time()
    memory_before = proc_memory_bytes()
    solver_calls: list[dict] = []
    original_milp = certify.milp
    original_rref = certify.gf2.rref
    H = task["H"]
    logical = task["logical"]

    def cached_rref(matrix: np.ndarray) -> tuple[np.ndarray, list[int]]:
        if matrix.shape != H.shape or not np.array_equal(matrix, H):
            return original_rref(matrix)
        return task["H_rref"].copy(), list(task["H_pivots"])

    def recording_milp(*args: Any, **kwargs: Any) -> Any:
        solver_start = time.monotonic()
        # SciPy passes unrecognized options through to HiGHS.  The stock
        # predicate supplies the formulation and cutoff; this instrumentation
        # adds only a concurrency cap so a process pool cannot oversubscribe
        # the host with one HiGHS thread pool per worker.
        kwargs["options"] = {**(kwargs.get("options") or {}), "threads": 1}
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="Unrecognized options detected", category=RuntimeWarning
            )
            result = original_milp(*args, **kwargs)
        serialized = serialize_solver_result(
            result, H.shape[1], H, logical, task["cutoff"]
        )
        serialized["duration_seconds"] = time.monotonic() - solver_start
        solver_calls.append(serialized)
        return result

    try:
        certify.milp = recording_milp
        certify.gf2.rref = cached_rref
        lighter = certify._exists_lighter(
            H, logical.reshape(1, -1), task["cutoff"], task["time_limit_seconds"]
        )
        validated_witness = has_valid_witness({"solver_calls": solver_calls}, task)
        if validated_witness:
            status = "feasible_refutation"
            status_basis = (
                "stock_predicate_feasible"
                if lighter is True
                else "validated_time_limit_incumbent"
            )
            error = None
        elif lighter is True:
            status = "runner_error"
            status_basis = "stock_predicate_feasible_without_valid_witness"
            error = {
                "type": "MissingValidWitness",
                "message": "stock predicate returned true without a valid captured witness",
                "traceback": None,
            }
        elif lighter is False:
            status = "proven_infeasible"
            status_basis = "stock_predicate_infeasible"
            error = None
        else:
            status = "unknown"
            status_basis = "stock_predicate_unknown_without_valid_incumbent"
            error = None
    except BaseException as exc:  # preserve unexpected worker failures as data
        lighter = None
        status = "runner_error"
        status_basis = "runner_exception"
        error = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        certify.milp = original_milp
        certify.gf2.rref = original_rref

    memory_after = proc_memory_bytes()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "schema_version": 2,
        "candidate_key": task["candidate_key"],
        "candidate_path": task["candidate_path"],
        "candidate_sha256": task["candidate_sha256"],
        "certifier_sha256": task["certifier_sha256"],
        "gf2_sha256": task["gf2_sha256"],
        "runner_sha256": task["runner_sha256"],
        "task_id": task["task_id"],
        "side": task["side"],
        "logical_row_index": task["logical_row_index"],
        "check_matrix_sha256": array_sha256(H),
        "logical_generator_sha256": array_sha256(logical),
        "logical_generator_support": logical_support(logical),
        "cutoff": task["cutoff"],
        "time_limit_seconds": task["time_limit_seconds"],
        "seed": None,
        "started_at_utc": started_at,
        "finished_at_utc": utc_now(),
        "duration_seconds": time.monotonic() - wall_start,
        "process_cpu_seconds": time.process_time() - cpu_start,
        "worker_pid": os.getpid(),
        "memory_bytes": {
            "before": memory_before,
            "after": memory_after,
            "ru_maxrss": int(usage.ru_maxrss) * 1024,
        },
        "status": status,
        "status_basis": status_basis,
        "stock_predicate_return": lighter,
        "solver": "scipy/HiGHS MILP via verify/certify.py::_exists_lighter",
        "preprocessing": {
            "method": "parent-cached result of verify/gf2.py::rref",
            "rref_sha256": array_sha256(task["H_rref"]),
            "pivot_count": len(task["H_pivots"]),
        },
        "solver_options": {"time_limit": task["time_limit_seconds"], "threads": 1},
        "solver_calls": solver_calls,
        "error": error,
    }


def load_manifest() -> tuple[dict, dict[int, dict]]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    return manifest, {item["candidate_id"]: item for item in manifest["targets"]}


def candidate_specs(args: argparse.Namespace) -> list[dict]:
    manifest, by_id = load_manifest()
    specs = []
    if args.fixture:
        for stem in args.fixture:
            validate_artifact_name(stem, label="fixture")
            path = REPO / "codes" / f"{stem}.json"
            if not path.is_file():
                raise FileNotFoundError(path)
            specs.append(
                {
                    "candidate_key": stem,
                    "candidate_id": None,
                    "candidate": path.relative_to(REPO).as_posix(),
                    "candidate_sha256": sha256(path),
                    "board_advancing": None,
                    "result_root": RESULTS / "calibration" / "sharded" / stem,
                }
            )
        return specs

    requested: list[int]
    if args.all_board:
        advancing = [
            item["candidate_id"] for item in manifest["targets"] if item["board_advancing"]
        ]
        requested = [item for item in PRIORITY_IDS if item in advancing]
        requested.extend(item for item in advancing if item not in requested)
    else:
        requested = args.target_id or []
    if not requested:
        raise ValueError("select --fixture, --target-id, or --all-board")
    if len(requested) != len(set(requested)):
        raise ValueError("duplicate target IDs")
    for candidate_id in requested:
        target = by_id.get(candidate_id)
        if target is None:
            raise ValueError(f"target ID not in manifest: {candidate_id}")
        candidate = REPO / target["candidate"]
        actual_hash = sha256(candidate)
        if actual_hash != target["candidate_sha256"]:
            raise RuntimeError(f"candidate hash mismatch: {candidate_id}")
        specs.append(
            {
                **target,
                "candidate_key": f"c{candidate_id:07d}",
                "candidate_sha256": actual_hash,
                "result_root": RESULTS / f"c{candidate_id:07d}",
            }
        )
    return specs


def prior_evidence(
    spec: dict, task: dict, *, exclude_stage: str | None = None
) -> dict | None:
    evidence = []
    attempts = spec["result_root"] / "attempts"
    if not attempts.is_dir():
        return None
    for path in attempts.glob(f"*/tasks/{task['task_id']}.json"):
        if exclude_stage is not None and path.parents[1].name == exclude_stage:
            continue
        record = json.loads(path.read_text())
        if record.get("candidate_sha256") != spec["candidate_sha256"]:
            continue
        if record.get("certifier_sha256") != task["certifier_sha256"]:
            continue
        validate_task_record(record, task, require_runtime_identity=False)
        evidence.append((path, record))
    definitive = [
        item
        for item in evidence
        if evidence_status(item[1], task) in {"feasible_refutation", "proven_infeasible"}
    ]
    statuses = {evidence_status(item[1], task) for item in definitive}
    if len(statuses) > 1:
        raise RuntimeError(
            f"contradictory definitive evidence for {spec['candidate_key']} {task['task_id']}"
        )
    choices = definitive or evidence
    if not choices:
        return None
    path, record = max(choices, key=lambda item: item[1].get("finished_at_utc", ""))
    return {"path": path.relative_to(REPO).as_posix(), "record": record}


def atomic_submission(doc: dict, path: Path, submit_module: Any) -> str:
    """Save a submission through the kit without exposing a partial final file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"unreadable existing refutation witness: {path}") from exc
        if existing != doc:
            raise FileExistsError(f"conflicting refutation witness: {path}")
        return sha256(path)

    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        errors = submit_module.save_submission(doc, str(temporary))
        if errors:
            raise RuntimeError(f"schema errors saving refutation witness {path}: {errors}")
        if json.loads(temporary.read_text()) != doc:
            raise RuntimeError(f"submission changed while saving refutation witness: {path}")
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        publish_new_file(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    return sha256(path)


def refutation_paths(task: dict, stage: str, doc: dict) -> tuple[Path, Path, Path]:
    validate_artifact_name(stage)
    stem = (
        f"{doc['n']}-{doc['k']}-{doc['distance']['d']}-"
        f"{task['candidate_key']}-{stage}-{task['task_id']}"
    )
    root = RESULTS / task["candidate_key"] / "refutation"
    return (
        root / f"{stage}-{task['task_id']}.submission.json",
        REPO / "research" / "candidates" / f"{stem}.json",
        root / f"{stage}-{task['task_id']}.json",
    )


def refutation_verification_path(result_path: Path) -> Path:
    suffix = ".submission.json"
    if not result_path.name.endswith(suffix):
        raise RuntimeError(f"invalid refutation submission path: {result_path}")
    return result_path.with_name(
        result_path.name.removesuffix(suffix) + ".verification.json"
    )


def _source_task_path(task: dict, stage: str) -> Path:
    source = task.get("source_task_result")
    if not isinstance(source, str):
        raise RuntimeError(f"missing source task result for {task['task_id']}")
    path = (REPO / source).resolve()
    try:
        path.relative_to(REPO.resolve())
    except ValueError as exc:
        raise RuntimeError(f"source task result escapes repository: {source}") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.parent.name != "tasks" or path.parent.parent.name != stage:
        raise RuntimeError(f"source task stage mismatch: {source}")
    return path


def validate_refutation_report(
    report: dict, doc: dict, task: dict, location: Path | str
) -> None:
    if report.get("ok") is not True or report.get("name") != doc.get("name"):
        raise RuntimeError(f"invalid refutation verifier report: {location}")
    computed = report.get("computed")
    if (
        not isinstance(computed, dict)
        or computed.get("n") != doc.get("n")
        or computed.get("k") != doc.get("k")
    ):
        raise RuntimeError(f"refutation verifier parameter mismatch: {location}")
    witness_check = f"distance_{task['side']}_witness"
    checks = report.get("checks")
    if not isinstance(checks, list) or not any(
        isinstance(item, dict)
        and item.get("check") == witness_check
        and item.get("ok") is True
        for item in checks
    ):
        raise RuntimeError(
            f"refutation verifier report lacks passing {witness_check}: {location}"
        )


def persist_refutation_report(doc: dict, path: Path, task: dict) -> str:
    if path.exists():
        if path.is_symlink():
            raise RuntimeError(f"refusing symlink verifier report: {path}")
        report = json.loads(path.read_text())
        validate_refutation_report(report, doc, task, path)
        return sha256(path)

    import qldpc_verify

    report = qldpc_verify.verify(doc, refute=False, seed=0)
    validate_refutation_report(report, doc, task, path)
    atomic_json(path, report)
    return sha256(path)


def validate_refutation_index(
    index_path: Path, expected: dict, doc: dict, task: dict
) -> dict:
    """Validate a complete legacy-v1 or current-v2 refutation bundle."""
    if index_path.is_symlink():
        raise RuntimeError(f"refusing symlink refutation index: {index_path}")
    try:
        existing = json.loads(index_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"unreadable refutation index: {index_path}") from exc
    legacy_required = (
        "candidate_key",
        "candidate_path",
        "candidate_sha256",
        "certifier_sha256",
        "task_id",
        "side",
        "weight",
        "support",
        "source_task_result",
        "result_submission",
        "local_staging_submission",
        "result_submission_sha256",
        "local_staging_submission_sha256",
    )
    current_required = (
        "persisted_at_utc",
        "stage",
        "gf2_sha256",
        "persistence_runner_sha256",
        "source_runner_sha256",
        "logical_row_index",
        "logical_generator_sha256",
        "cutoff",
        "source_task_result_sha256",
        "source_task_status",
        "source_task_effective_status",
        "verification",
        "verification_sha256",
    )
    schema_version = existing.get("schema_version")
    if type(schema_version) is not int:
        raise RuntimeError(f"unsupported refutation index schema: {index_path}")
    if schema_version == 1:
        required = legacy_required
    elif schema_version == 2:
        required = legacy_required + current_required
    else:
        raise RuntimeError(f"unsupported refutation index schema: {index_path}")
    missing = [key for key in required if key not in existing]
    if missing:
        raise RuntimeError(f"incomplete refutation index {index_path}: missing {missing}")
    for key in (
        "candidate_key",
        "candidate_path",
        "candidate_sha256",
        "certifier_sha256",
        "task_id",
        "side",
        "weight",
        "support",
        "source_task_result",
        "result_submission",
        "local_staging_submission",
    ):
        if existing.get(key) != expected.get(key):
            raise RuntimeError(f"conflicting refutation index {index_path}: {key}")
    for key in ("result_submission_sha256", "local_staging_submission_sha256"):
        if not is_sha256(existing.get(key)):
            raise RuntimeError(f"invalid artifact hash in {index_path}: {key}")

    if schema_version == 2:
        for key in (
            "stage",
            "gf2_sha256",
            "source_runner_sha256",
            "logical_row_index",
            "logical_generator_sha256",
            "cutoff",
            "source_task_result_sha256",
            "source_task_status",
            "source_task_effective_status",
            "verification",
        ):
            if existing.get(key) != expected.get(key):
                raise RuntimeError(f"conflicting refutation index {index_path}: {key}")
        if not isinstance(existing["persisted_at_utc"], str):
            raise RuntimeError(f"invalid persistence timestamp in {index_path}")
        if not is_sha256(existing["persistence_runner_sha256"]):
            raise RuntimeError(f"invalid persistence runner provenance in {index_path}")
        source_runner_hash = existing["source_runner_sha256"]
        if source_runner_hash is not None and not is_sha256(source_runner_hash):
            raise RuntimeError(f"invalid source runner provenance in {index_path}")
        if not is_sha256(existing["verification_sha256"]):
            raise RuntimeError(f"invalid verifier-report hash in {index_path}")

    result_path = REPO / existing["result_submission"]
    if result_path.is_symlink() or not result_path.is_file():
        raise RuntimeError(f"missing tracked refutation witness: {result_path}")
    result_hash = sha256(result_path)
    if result_hash != existing["result_submission_sha256"]:
        raise RuntimeError(f"changed tracked refutation witness: {result_path}")
    if json.loads(result_path.read_text()) != doc:
        raise RuntimeError(f"refutation witness content mismatch: {result_path}")

    verification_path = refutation_verification_path(result_path)
    if verification_path.is_symlink() or not verification_path.is_file():
        raise RuntimeError(f"missing tracked refutation verifier report: {verification_path}")
    verification_hash = sha256(verification_path)
    if schema_version == 2 and verification_hash != existing["verification_sha256"]:
        raise RuntimeError(f"changed refutation verifier report: {verification_path}")
    report = json.loads(verification_path.read_text())
    validate_refutation_report(report, doc, task, verification_path)

    staging_path = REPO / existing["local_staging_submission"]
    if staging_path.exists():
        if staging_path.is_symlink() or not staging_path.is_file():
            raise RuntimeError(f"invalid local staging witness: {staging_path}")
        if sha256(staging_path) != existing["local_staging_submission_sha256"]:
            raise RuntimeError(f"changed local staging witness: {staging_path}")
        if json.loads(staging_path.read_text()) != doc:
            raise RuntimeError(f"local staging witness content mismatch: {staging_path}")
    return existing


def persist_refutation(
    task: dict, record: dict, stage: str, *, check_only: bool = False
) -> dict:
    """Persist a feasible MILP witness through make_submission/save_submission.

    The solver witness replaces the corresponding side of the original
    candidate; the other submitted witness is retained.  ``make_submission``
    rechecks both witnesses against the repository GF(2) criteria before either
    copy is saved.
    """
    validate_artifact_name(stage)
    validate_task_record(record, task, require_runtime_identity=False)
    solver_witnesses = valid_solver_witnesses(record, task)
    if not solver_witnesses:
        raise RuntimeError(f"feasible task has no captured witness: {task['task_id']}")
    witness_record = solver_witnesses[0]

    candidate_path = REPO / task["candidate_path"]
    if sha256(candidate_path) != task["candidate_sha256"]:
        raise RuntimeError(f"candidate hash mismatch while persisting {task['task_id']}")
    source_task_path = _source_task_path(task, stage)
    source_record = json.loads(source_task_path.read_text())
    if source_record != record:
        raise RuntimeError(f"source task content mismatch: {source_task_path}")
    source_task_hash = sha256(source_task_path)
    original = json.loads(candidate_path.read_text())
    witnesses = {
        side: list(original["distance"][side]["witness"])
        for side in ("X", "Z")
    }
    witnesses[task["side"]] = list(witness_record["support"])
    weights = {side: len(witnesses[side]) for side in ("X", "Z")}

    kit = REPO / "research" / "kit"
    sys.path.insert(0, str(kit))
    import submit as submit_module

    n = int(original["n"])
    HX = certify._matrix(original["checks"]["X"], n)
    HZ = certify._matrix(original["checks"]["Z"], n)
    supplied = iter(
        ((weights["X"], witnesses["X"]), (weights["Z"], witnesses["Z"]))
    )
    original_search = submit_module.lightest_logical
    try:
        submit_module.lightest_logical = lambda *_args, **_kwargs: next(supplied)
        provenance = original.get("provenance", {})
        locality = original.get("locality") or {}
        doc = submit_module.make_submission(
            HX,
            HZ,
            name=f"{original.get('name', task['candidate_key'])} MILP refutation witness",
            construction=provenance.get("construction", "periodic BB campaign candidate"),
            authors=provenance.get("authors", ["autoresearch"]),
            family=original.get("family"),
            references=provenance.get("references", []),
            notes=(
                f"Explicit lighter {task['side']}-logical found by the stock cutoff MILP "
                f"for {task['candidate_key']} task {task['task_id']}; local staging evidence."
            ),
            date=provenance.get("date"),
            confidence="upper_bound",
            coordinates=locality.get("coordinates"),
            layers=locality.get("layers"),
        )
    finally:
        submit_module.lightest_logical = original_search

    result_path, staging_path, index_path = refutation_paths(task, stage, doc)
    verification_path = refutation_verification_path(result_path)
    index = {
        "schema_version": 2,
        "persisted_at_utc": utc_now(),
        "stage": stage,
        "candidate_key": task["candidate_key"],
        "candidate_path": task["candidate_path"],
        "candidate_sha256": task["candidate_sha256"],
        "certifier_sha256": record["certifier_sha256"],
        "gf2_sha256": task["gf2_sha256"],
        "persistence_runner_sha256": task["runner_sha256"],
        "source_runner_sha256": record.get("runner_sha256"),
        "task_id": task["task_id"],
        "side": task["side"],
        "logical_row_index": task["logical_row_index"],
        "logical_generator_sha256": array_sha256(task["logical"]),
        "cutoff": task["cutoff"],
        "weight": witness_record["weight"],
        "support": witness_record["support"],
        "source_task_result": source_task_path.relative_to(REPO).as_posix(),
        "source_task_result_sha256": source_task_hash,
        "source_task_status": record.get("status"),
        "source_task_effective_status": evidence_status(record, task),
        "result_submission": result_path.relative_to(REPO).as_posix(),
        "local_staging_submission": staging_path.relative_to(REPO).as_posix(),
        "verification": verification_path.relative_to(REPO).as_posix(),
    }
    if index_path.exists():
        return validate_refutation_index(index_path, index, doc, task)
    if check_only:
        raise RuntimeError(f"unpersisted refutation index: {index_path}")
    result_hash = atomic_submission(doc, result_path, submit_module)
    staging_hash = atomic_submission(doc, staging_path, submit_module)
    verification_hash = persist_refutation_report(doc, verification_path, task)
    index.update(
        {
            "result_submission_sha256": result_hash,
            "local_staging_submission_sha256": staging_hash,
            "verification_sha256": verification_hash,
        }
    )
    atomic_json(index_path, index)
    return index


def prepare_candidate(
    spec: dict,
    args: argparse.Namespace,
    certifier_hash: str,
    gf2_hash: str,
    runner_hash: str,
) -> tuple[list[dict], dict]:
    candidate_path = REPO / spec["candidate"]
    doc = json.loads(candidate_path.read_text())
    n = int(doc["n"])
    HX = certify._matrix(doc["checks"]["X"], n)
    HZ = certify._matrix(doc["checks"]["Z"], n)
    x_rref, x_pivots = gf2.rref(HZ)
    z_rref, z_pivots = gf2.rref(HX)
    sides = {
        "X": (HZ, gf2.logical_basis(HX, HZ), x_rref, x_pivots),
        "Z": (HX, gf2.logical_basis(HZ, HX), z_rref, z_pivots),
    }
    run_dir = spec["result_root"] / "attempts" / args.stage
    start_path = run_dir / "run-start.json"
    existing_start = None
    stored_descriptors: dict[str, dict] = {}
    if start_path.exists():
        if not args.resume:
            raise FileExistsError(f"stage exists; pass --resume: {run_dir}")
        existing_start = json.loads(start_path.read_text())
        stored_tasks = existing_start.get("tasks")
        if not isinstance(stored_tasks, list):
            raise RuntimeError(f"resume metadata has no task list: {start_path}")
        for descriptor in stored_tasks:
            if not isinstance(descriptor, dict):
                raise RuntimeError(f"invalid stored task descriptor: {start_path}")
            task_id = descriptor.get("task_id")
            if not isinstance(task_id, str) or task_id in stored_descriptors:
                raise RuntimeError(f"invalid stored task ID in {start_path}: {task_id!r}")
            stored_descriptors[task_id] = descriptor

    task_descriptors = []
    tasks_by_id = {}
    new_tasks = []
    for side in ("X", "Z"):
        if side not in doc["distance"]:
            continue
        H, logical_basis, H_rref, H_pivots = sides[side]
        value = int(doc["distance"][side]["value"])
        for row_index, logical in enumerate(logical_basis):
            task_id = f"{side}-{row_index:04d}"
            task = {
                "candidate_key": spec["candidate_key"],
                "candidate_path": spec["candidate"],
                "candidate_sha256": spec["candidate_sha256"],
                "certifier_sha256": certifier_hash,
                "gf2_sha256": gf2_hash,
                "runner_sha256": runner_hash,
                "task_id": task_id,
                "side": side,
                "logical_row_index": row_index,
                "cutoff": value - 1,
                "time_limit_seconds": args.tlim,
                "H": H,
                "H_rref": H_rref,
                "H_pivots": H_pivots,
                "logical": logical,
            }
            tasks_by_id[task_id] = task
            base_descriptor = task_descriptor(task)
            if existing_start is not None:
                descriptor = stored_descriptors.get(task_id)
                expected_keys = set(base_descriptor) | {
                    "inherited",
                    "evidence_path",
                    "evidence_sha256",
                }
                if descriptor is None or set(descriptor) != expected_keys:
                    raise RuntimeError(
                        f"stored task descriptor mismatch for {task_id}: keys"
                    )
                for key, value in base_descriptor.items():
                    if descriptor.get(key) != value:
                        raise RuntimeError(
                            f"stored task descriptor mismatch for {task_id}: {key}"
                        )
                if type(descriptor.get("inherited")) is not bool:
                    raise RuntimeError(
                        f"stored task descriptor mismatch for {task_id}: inherited"
                    )
                inherited = descriptor["inherited"]
                evidence_path = descriptor.get("evidence_path")
                evidence_hash = descriptor.get("evidence_sha256")
                if inherited:
                    if not isinstance(evidence_path, str) or not isinstance(
                        evidence_hash, str
                    ):
                        raise RuntimeError(
                            f"stored task descriptor lacks evidence for {task_id}"
                        )
                    source_path = (REPO / evidence_path).resolve()
                    try:
                        source_path.relative_to(
                            (spec["result_root"] / "attempts").resolve()
                        )
                    except ValueError as exc:
                        raise RuntimeError(
                            f"stored evidence path escapes candidate attempts: {evidence_path}"
                        ) from exc
                    if (
                        source_path.parent.name != "tasks"
                        or source_path.name != f"{task_id}.json"
                        or source_path.parents[1].name == args.stage
                    ):
                        raise RuntimeError(
                            f"stored evidence path mismatch for {task_id}: {evidence_path}"
                        )
                    if not source_path.is_file() or sha256(source_path) != evidence_hash:
                        raise RuntimeError(
                            f"stored evidence missing or changed for {task_id}: {evidence_path}"
                        )
                    prior_record = json.loads(source_path.read_text())
                    validate_task_record(
                        prior_record, task, require_runtime_identity=False
                    )
                    if evidence_status(prior_record, task) not in {
                        "feasible_refutation",
                        "proven_infeasible",
                    }:
                        raise RuntimeError(
                            f"stored evidence is not definitive for {task_id}: {evidence_path}"
                        )
                    prior = {"path": evidence_path, "record": prior_record}
                else:
                    if evidence_path is not None or evidence_hash is not None:
                        raise RuntimeError(
                            f"non-inherited task has stored evidence for {task_id}"
                        )
                    prior = None
            else:
                prior = (
                    prior_evidence(spec, task, exclude_stage=args.stage)
                    if args.reuse_definitive
                    else None
                )
                inherited = bool(
                    prior
                    and evidence_status(prior["record"], task)
                    in {"feasible_refutation", "proven_infeasible"}
                )
                descriptor = {
                    **base_descriptor,
                    "inherited": inherited,
                    "evidence_path": prior["path"] if inherited else None,
                    "evidence_sha256": (
                        sha256(REPO / prior["path"]) if inherited else None
                    ),
                }
            task_descriptors.append(descriptor)
            if inherited:
                if (
                    evidence_status(prior["record"], task) == "feasible_refutation"
                    and task["candidate_key"].startswith("c")
                ):
                    source_path = REPO / prior["path"]
                    persist_refutation(
                        {**task, "source_task_result": prior["path"]},
                        prior["record"],
                        source_path.parents[1].name,
                    )
                continue
            new_tasks.append(task)

    expected_tasks = 2 * int(doc["k"])
    if len(task_descriptors) != expected_tasks:
        raise RuntimeError(
            f"{spec['candidate_key']}: expected {expected_tasks} logical tasks, "
            f"got {len(task_descriptors)}"
        )
    start_record = {
        "schema_version": 2,
        "stage": args.stage,
        "started_at_utc": utc_now(),
        "candidate_key": spec["candidate_key"],
        "candidate_path": spec["candidate"],
        "candidate_sha256": spec["candidate_sha256"],
        "certifier_sha256": certifier_hash,
        "gf2_sha256": gf2_hash,
        "runner_sha256": runner_hash,
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "parameters": {
            "n": doc["n"],
            "k": doc["k"],
            "d": doc["distance"]["d"],
            "d_x_upper": doc["distance"].get("X", {}).get("value"),
            "d_z_upper": doc["distance"].get("Z", {}).get("value"),
        },
        "matrix_sha256": {"HX": array_sha256(HX), "HZ": array_sha256(HZ)},
        "logical_basis_sha256": {
            side: array_sha256(basis) for side, (_, basis, _, _) in sides.items()
        },
        "rref_sha256": {
            side: array_sha256(rref) for side, (_, _, rref, _) in sides.items()
        },
        "worker_limit": args.workers,
        "task_time_limit_seconds": args.tlim,
        "thread_limits": {
            name: os.environ.get(name)
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "expected_task_count": len(task_descriptors),
        "new_task_count": len(new_tasks),
        "inherited_definitive_task_count": len(task_descriptors) - len(new_tasks),
        "tasks": task_descriptors,
    }
    if existing_start is not None:
        for key in (
            "stage",
            "candidate_key",
            "candidate_path",
            "candidate_sha256",
            "certifier_sha256",
            "gf2_sha256",
            "runner_sha256",
            "parameters",
            "matrix_sha256",
            "logical_basis_sha256",
            "rref_sha256",
            "worker_limit",
            "task_time_limit_seconds",
            "thread_limits",
            "expected_task_count",
            "new_task_count",
            "inherited_definitive_task_count",
            "tasks",
        ):
            if existing_start.get(key) != start_record.get(key):
                raise RuntimeError(f"resume metadata mismatch in {start_path}: {key}")
    else:
        atomic_json(start_path, start_record)
    tasks_path = run_dir / "tasks"
    tasks_path.mkdir(parents=True, exist_ok=True)
    if args.resume:
        remaining = []
        for task in new_tasks:
            task_path = tasks_path / f"{task['task_id']}.json"
            if not task_path.exists():
                remaining.append(task)
                continue
            record = json.loads(task_path.read_text())
            validate_task_record(record, task, require_runtime_identity=True)
            if has_valid_witness(record, task) and task["candidate_key"].startswith("c"):
                task_with_source = {
                    **task,
                    "source_task_result": task_path.relative_to(REPO).as_posix(),
                }
                persist_refutation(task_with_source, record, args.stage)
        new_tasks = remaining
    context = {
        "spec": spec,
        "doc": doc,
        "run_dir": run_dir,
        "gf2_sha256": gf2_hash,
        "runner_sha256": runner_hash,
        "task_descriptors": task_descriptors,
        "tasks_by_id": tasks_by_id,
        "new_task_count": len(new_tasks),
    }
    return new_tasks, context


def aggregate_candidate(context: dict, certifier_hash: str) -> dict:
    spec = context["spec"]
    run_dir = context["run_dir"]
    tasks = []
    for descriptor in context["task_descriptors"]:
        expected_task = context["tasks_by_id"][descriptor["task_id"]]
        current = run_dir / "tasks" / f"{descriptor['task_id']}.json"
        if current.is_file():
            record = json.loads(current.read_text())
            validate_task_record(record, expected_task, require_runtime_identity=True)
            path = current
            inherited = False
        elif descriptor["inherited"]:
            path = REPO / descriptor["evidence_path"]
            if not path.is_file():
                raise RuntimeError(f"missing inherited evidence: {path}")
            if sha256(path) != descriptor["evidence_sha256"]:
                raise RuntimeError(f"changed inherited evidence: {path}")
            record = json.loads(path.read_text())
            validate_task_record(record, expected_task, require_runtime_identity=False)
            inherited = True
        else:
            record = {
                "task_id": descriptor["task_id"],
                "side": descriptor["side"],
                "status": "missing",
                "duration_seconds": 0.0,
                "process_cpu_seconds": 0.0,
            }
            path = None
            inherited = False
        tasks.append(
            {
                "task_id": descriptor["task_id"],
                "side": descriptor["side"],
                "status": evidence_status(record, expected_task),
                "evidence_path": path.relative_to(REPO).as_posix() if path else None,
                "inherited": inherited,
                "duration_seconds": record.get("duration_seconds", 0.0),
                "process_cpu_seconds": record.get("process_cpu_seconds", 0.0),
            }
        )
    sides = {}
    for side in ("X", "Z"):
        selected = [task for task in tasks if task["side"] == side]
        counts = {
            status: sum(task["status"] == status for task in selected)
            for status in (
                "proven_infeasible",
                "feasible_refutation",
                "unknown",
                "runner_error",
                "missing",
            )
        }
        if counts["feasible_refutation"]:
            status = "refuted"
        elif selected and counts["proven_infeasible"] == len(selected):
            status = "exact"
        else:
            status = "timeout"
        sides[side] = {"status": status, "task_count": len(selected), "counts": counts}
    if any(side["status"] == "refuted" for side in sides.values()):
        aggregate_status = "refuted"
    elif sides and all(side["status"] == "exact" for side in sides.values()):
        aggregate_status = "apparent_exact_requires_serial_confirmation"
    else:
        aggregate_status = "timeout"
    return {
        "schema_version": 2,
        "stage": run_dir.name,
        "finished_at_utc": utc_now(),
        "candidate_key": spec["candidate_key"],
        "candidate_path": spec["candidate"],
        "candidate_sha256": spec["candidate_sha256"],
        "certifier_sha256": certifier_hash,
        "gf2_sha256": context["gf2_sha256"],
        "runner_sha256": context["runner_sha256"],
        "parameters": {
            "n": context["doc"]["n"],
            "k": context["doc"]["k"],
            "d": context["doc"]["distance"]["d"],
            "d_x_upper": context["doc"]["distance"].get("X", {}).get("value"),
            "d_z_upper": context["doc"]["distance"].get("Z", {}).get("value"),
        },
        "aggregate_status": aggregate_status,
        "sides": sides,
        "task_count": len(tasks),
        "task_wall_seconds_sum": sum(
            task["duration_seconds"] for task in tasks if not task["inherited"]
        ),
        "task_cpu_seconds_sum": sum(
            task["process_cpu_seconds"] for task in tasks if not task["inherited"]
        ),
        "tasks": tasks,
    }


def task_stream(
    specs: list[dict],
    args: argparse.Namespace,
    certifier_hash: str,
    gf2_hash: str,
    runner_hash: str,
    contexts: list[dict],
) -> Iterator[tuple[dict, Path]]:
    work: list[tuple[dict, Path]] = []
    for spec in specs:
        new_tasks, context = prepare_candidate(
            spec, args, certifier_hash, gf2_hash, runner_hash
        )
        contexts.append(context)
        for task in new_tasks:
            work.append(
                (task, context["run_dir"] / "tasks" / f"{task['task_id']}.json")
            )
    yield from work


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="append", help="codes/<stem>.json exact fixture")
    parser.add_argument("--target-id", action="append", type=int)
    parser.add_argument("--all-board", action="store_true")
    parser.add_argument("--stage", required=True)
    parser.add_argument("--tlim", type=float, required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--reuse-definitive", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    validate_artifact_name(args.stage)
    worker_ceiling = min(64, os.cpu_count() or 1)
    if not 1 <= args.workers <= worker_ceiling:
        raise ValueError(f"workers must be in [1, {worker_ceiling}]")
    if args.tlim <= 0:
        raise ValueError("--tlim must be positive")

    specs = candidate_specs(args)
    certifier_hash = sha256(VERIFY / "certify.py")
    gf2_hash = sha256(VERIFY / "gf2.py")
    runner_hash = sha256(Path(__file__))
    batch_dir = RESULTS / "batches"
    batch_start_path = batch_dir / f"{args.stage}-start.json"
    batch_output_path = batch_dir / f"{args.stage}.json"
    if batch_output_path.exists():
        raise FileExistsError(batch_output_path)
    batch_started = utc_now()
    batch_wall_start = time.monotonic()
    start_record = {
        "schema_version": 2,
        "stage": args.stage,
        "started_at_utc": batch_started,
        "certifier_sha256": certifier_hash,
        "gf2_sha256": gf2_hash,
        "runner_sha256": runner_hash,
        "workers": args.workers,
        "task_time_limit_seconds": args.tlim,
        "reuse_definitive": args.reuse_definitive,
        "candidate_keys": [spec["candidate_key"] for spec in specs],
        "candidate_inputs": [
            {
                "candidate_key": spec["candidate_key"],
                "candidate_path": spec["candidate"],
                "candidate_sha256": spec["candidate_sha256"],
            }
            for spec in specs
        ],
        "thread_limits": {
            name: os.environ.get(name)
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }
    if not batch_start_path.exists():
        atomic_json(batch_start_path, start_record)
        persisted_start_record = start_record
    else:
        if not args.resume:
            raise FileExistsError(batch_start_path)
        existing_batch = json.loads(batch_start_path.read_text())
        for key in (
            "schema_version",
            "stage",
            "certifier_sha256",
            "gf2_sha256",
            "runner_sha256",
            "workers",
            "task_time_limit_seconds",
            "reuse_definitive",
            "candidate_keys",
            "candidate_inputs",
            "thread_limits",
        ):
            if existing_batch.get(key) != start_record.get(key):
                raise RuntimeError(f"resume batch metadata mismatch: {key}")
        persisted_start_record = existing_batch

    contexts: list[dict] = []
    stream = iter(
        task_stream(specs, args, certifier_hash, gf2_hash, runner_hash, contexts)
    )
    submitted = completed = 0
    mp_context = mp.get_context("spawn")
    with cf.ProcessPoolExecutor(max_workers=args.workers, mp_context=mp_context) as executor:
        pending: dict[cf.Future, tuple[dict, Path]] = {}

        def fill() -> None:
            nonlocal submitted
            while len(pending) < 2 * args.workers:
                try:
                    task, output_path = next(stream)
                except StopIteration:
                    break
                future = executor.submit(run_one_task, task)
                pending[future] = (task, output_path)
                submitted += 1

        fill()
        while pending:
            done, _ = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
            for future in done:
                task, output_path = pending.pop(future)
                try:
                    record = future.result()
                except BaseException as exc:
                    record = {
                        "schema_version": 2,
                        "candidate_key": task["candidate_key"],
                        "candidate_path": task["candidate_path"],
                        "candidate_sha256": task["candidate_sha256"],
                        "certifier_sha256": task["certifier_sha256"],
                        "gf2_sha256": task["gf2_sha256"],
                        "runner_sha256": task["runner_sha256"],
                        "task_id": task["task_id"],
                        "side": task["side"],
                        "logical_row_index": task["logical_row_index"],
                        "check_matrix_sha256": array_sha256(task["H"]),
                        "logical_generator_sha256": array_sha256(task["logical"]),
                        "logical_generator_support": logical_support(task["logical"]),
                        "cutoff": task["cutoff"],
                        "time_limit_seconds": task["time_limit_seconds"],
                        "seed": None,
                        "finished_at_utc": utc_now(),
                        "duration_seconds": 0.0,
                        "process_cpu_seconds": 0.0,
                        "status": "runner_error",
                        "status_basis": "future_exception",
                        "stock_predicate_return": None,
                        "solver_calls": [],
                        "error": {
                            "type": type(exc).__name__,
                            "message": str(exc),
                            "traceback": "".join(traceback.format_exception(exc)),
                        },
                    }
                atomic_json(output_path, record)
                validate_task_record(record, task, require_runtime_identity=True)
                if has_valid_witness(record, task) and task["candidate_key"].startswith("c"):
                    task_with_source = {
                        **task,
                        "source_task_result": output_path.relative_to(REPO).as_posix(),
                    }
                    persisted = persist_refutation(task_with_source, record, args.stage)
                    print(
                        f"persisted witness {persisted['result_submission']} ",
                        f"weight={persisted['weight']}",
                        flush=True,
                    )
                completed += 1
                print(
                    f"{completed}/{submitted} {task['candidate_key']} {task['task_id']} "
                    f"{record['status']} {record.get('duration_seconds', 0.0):.3f}s",
                    flush=True,
                )
            fill()

    aggregates = []
    for context in contexts:
        aggregate = aggregate_candidate(context, certifier_hash)
        aggregate_path = context["run_dir"] / "aggregate.json"
        if aggregate_path.exists():
            if not args.resume:
                raise FileExistsError(aggregate_path)
            existing = json.loads(aggregate_path.read_text())
            keys = set(aggregate) - {"finished_at_utc"}
            if any(existing.get(key) != aggregate.get(key) for key in keys):
                raise RuntimeError(f"resume aggregate mismatch: {aggregate_path}")
            aggregate = existing
        else:
            atomic_json(aggregate_path, aggregate)
        aggregates.append(aggregate)
    status_counts = {
        status: sum(item["aggregate_status"] == status for item in aggregates)
        for status in ("apparent_exact_requires_serial_confirmation", "refuted", "timeout")
    }
    batch = {
        **persisted_start_record,
        "finished_at_utc": utc_now(),
        "invocation_started_at_utc": batch_started,
        "invocation_wall_seconds": time.monotonic() - batch_wall_start,
        "invocation_submitted_task_count": submitted,
        "invocation_completed_task_count": completed,
        # Retain the v1 names for downstream readers.  On a resume they cover
        # this invocation only; scheduled/persisted counts cover the full stage.
        "wall_seconds": time.monotonic() - batch_wall_start,
        "submitted_task_count": submitted,
        "completed_task_count": completed,
        "scheduled_task_count": sum(
            not descriptor["inherited"]
            for context in contexts
            for descriptor in context["task_descriptors"]
        ),
        "persisted_task_count": sum(
            (context["run_dir"] / "tasks" / f"{descriptor['task_id']}.json").is_file()
            for context in contexts
            for descriptor in context["task_descriptors"]
            if not descriptor["inherited"]
        ),
        "candidate_count": len(aggregates),
        "status_counts": status_counts,
        "task_wall_seconds_sum": sum(item["task_wall_seconds_sum"] for item in aggregates),
        "task_cpu_seconds_sum": sum(item["task_cpu_seconds_sum"] for item in aggregates),
        "aggregates": [
            {
                "candidate_key": item["candidate_key"],
                "aggregate_status": item["aggregate_status"],
                "sides": item["sides"],
                "aggregate_path": (
                    next(
                        context["run_dir"]
                        for context in contexts
                        if context["spec"]["candidate_key"] == item["candidate_key"]
                    )
                    / "aggregate.json"
                ).relative_to(REPO).as_posix(),
            }
            for item in aggregates
        ],
    }
    atomic_json(batch_output_path, batch)
    print(json.dumps({"stage": args.stage, "status_counts": status_counts}, indent=2))


if __name__ == "__main__":
    main()
