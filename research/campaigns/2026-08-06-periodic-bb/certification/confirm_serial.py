"""Persist authoritative stock-serial confirmations for apparent closures.

The subprocess is deliberately the unmodified ``verify/certify.py``. This
wrapper only checks its inputs and output, and makes the resulting audit trail
crash-safe. A completed record is immutable; ``--resume`` only skips a
validated completed record or continues from a matching ``run-start.json``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RESULTS = HERE / "results"
TARGETS = HERE / "targets.json"
ENVIRONMENT = RESULTS / "environment.json"
SERIAL_BATCHES = RESULTS / "serial-confirmation-batches"
STDOUT_ISOLATOR = HERE / "serial_stdout_isolation" / "sitecustomize.py"
STDOUT_ISOLATOR_PYCACHE_PREFIX = STDOUT_ISOLATOR.parent / ".disabled-pycache"
STDOUT_ISOLATOR_MARKER_PREFIX = "QLDPC_STDOUT_ISOLATION_V1:"
STDOUT_ISOLATOR_HASH_ENV = "QLDPC_STDOUT_ISOLATOR_EXPECTED_SHA256"
STAGE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
SIDES = ("X", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object in {path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    """Create *path* atomically and never replace an existing result."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite {path}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with temporary.open("x") as handle:
            json.dump(value, handle, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        # A hard link publishes the fully-written inode atomically and, unlike
        # os.replace(), fails if another process created the destination after
        # the check above.
        os.link(temporary, path)
        temporary.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def safe_stage(value: str, option: str) -> str:
    if value in {".", ".."} or STAGE_RE.fullmatch(value) is None:
        raise ValueError(
            f"{option} must be a single 1-128 character path-safe component "
            "using letters, digits, '.', '_', or '-'"
        )
    return value


def require_under(path: Path, parent: Path, description: str) -> None:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise RuntimeError(f"{description} escapes {parent}: {path}") from exc


def child_usage() -> tuple[float, float]:
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(usage.ru_utime), float(usage.ru_stime)


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_certifier_output(
    value: Any, candidate: dict[str, Any]
) -> tuple[list[str], list[str], list[str]]:
    """Validate the exact stock output contract and classify non-exact sides."""
    errors: list[str] = []
    refutation_signals: list[str] = []
    timed_out: list[str] = []
    if not isinstance(value, dict):
        return ["top-level output is not a JSON object"], refutation_signals, timed_out

    required_keys = {"name", "d", "solver", "sides", "d_exact"}
    missing = sorted(required_keys - set(value))
    if missing:
        errors.append(f"missing output keys: {missing}")
    if value.get("name") != candidate.get("name"):
        errors.append("output name does not match candidate")
    if not is_int(value.get("d")) or value.get("d") != candidate.get("distance", {}).get("d"):
        errors.append("output d does not match candidate distance.d")
    if value.get("solver") != "scipy/HiGHS MILP":
        errors.append("unexpected solver identifier")
    if not isinstance(value.get("d_exact"), bool):
        errors.append("d_exact is not boolean")

    expected_sides = [side for side in SIDES if side in candidate.get("distance", {})]
    sides = value.get("sides")
    if not isinstance(sides, dict):
        errors.append("sides is not an object")
        sides = {}
    if set(sides) != set(expected_sides):
        errors.append(
            f"output sides {sorted(sides)} do not match candidate sides {expected_sides}"
        )

    exact_flags: list[bool] = []
    for side in expected_sides:
        item = sides.get(side)
        if not isinstance(item, dict):
            errors.append(f"side {side} is not an object")
            continue
        expected_value = candidate["distance"][side].get("value")
        if not is_int(item.get("value")) or item.get("value") != expected_value:
            errors.append(f"side {side} value does not match candidate")
        exact = item.get("exact")
        if not isinstance(exact, bool):
            errors.append(f"side {side} exact is not boolean")
            continue
        exact_flags.append(exact)
        note = item.get("note")
        if not isinstance(note, str):
            errors.append(f"side {side} note is not a string")
            continue
        if exact:
            if note != f"no logical < {expected_value} exists":
                errors.append(f"side {side} exact note is unexpected")
        elif note == "REFUTED: a lighter logical exists":
            refutation_signals.append(side)
        elif note == "time limit; remains upper bound":
            timed_out.append(side)
        else:
            errors.append(f"side {side} non-exact note is unexpected")

    expected_exact = (
        bool(expected_sides)
        and len(exact_flags) == len(expected_sides)
        and all(exact_flags)
    )
    if isinstance(value.get("d_exact"), bool) and value["d_exact"] != expected_exact:
        errors.append("d_exact is inconsistent with per-side exact flags")
    return errors, refutation_signals, timed_out


def stable_start_fields(value: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "schema_version",
        "confirmation_stage",
        "candidate_id",
        "candidate",
        "candidate_sha256",
        "certifier_sha256",
        "gf2_sha256",
        "per_task_time_limit_seconds",
        "command",
        "stdout_isolation",
    )
    return {key: value.get(key) for key in keys}


def stdout_isolation_directory_clean() -> bool:
    """Require the injected PYTHONPATH directory to contain only pinned source."""
    try:
        entries = list(STDOUT_ISOLATOR.parent.iterdir())
    except OSError:
        return False
    return (
        len(entries) == 1
        and entries[0] == STDOUT_ISOLATOR
        and entries[0].is_file()
        and not entries[0].is_symlink()
    )


def configure_stdout_isolation(
    enabled: bool, env: dict[str, str]
) -> dict[str, Any] | None:
    """Optionally separate Python stdout from native writes to file descriptor 1.

    SciPy's bundled HiGHS can emit an unconditional native ``puts`` after a
    successful solve.  The stock certifier writes its JSON through
    ``sys.stdout``; the hash-pinned sitecustomize module gives that stream a
    duplicate of the original stdout descriptor and redirects subsequent
    native fd-1 writes to stderr.  Only the child environment is changed.
    """
    if not enabled:
        return None
    require_under(STDOUT_ISOLATOR, HERE, "stdout isolator")
    if (
        STDOUT_ISOLATOR.parent.is_symlink()
        or STDOUT_ISOLATOR.is_symlink()
        or not STDOUT_ISOLATOR.is_file()
    ):
        raise RuntimeError(f"stdout isolator is not a regular file: {STDOUT_ISOLATOR}")
    if not stdout_isolation_directory_clean():
        raise RuntimeError(
            "stdout-isolation PYTHONPATH must contain only regular sitecustomize.py"
        )
    isolator_hash = sha256(STDOUT_ISOLATOR)
    isolator_rel = STDOUT_ISOLATOR.relative_to(REPO).as_posix()
    child_pythonpath = STDOUT_ISOLATOR.parent.relative_to(REPO).as_posix()
    pycache_prefix = STDOUT_ISOLATOR_PYCACHE_PREFIX.relative_to(REPO).as_posix()
    activation_marker = f"{STDOUT_ISOLATOR_MARKER_PREFIX}{isolator_hash}"
    env["PYTHONPATH"] = child_pythonpath
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = pycache_prefix
    env["PYTHONNOUSERSITE"] = "1"
    env[STDOUT_ISOLATOR_HASH_ENV] = isolator_hash
    return {
        "sitecustomize_path": isolator_rel,
        "sitecustomize_sha256": isolator_hash,
        "child_pythonpath": child_pythonpath,
        "child_python_pycache_prefix": pycache_prefix,
        "child_python_dont_write_bytecode": "1",
        "child_python_no_user_site": "1",
        "child_expected_sha256_environment": isolator_hash,
        "python_stdout_capture": "stdout",
        "native_fd1_capture": "stderr",
        "activation_marker": activation_marker,
        "pythonpath_directory_policy": "only-regular-sitecustomize.py",
    }


def validate_stdout_isolation_metadata(isolation: Any) -> dict[str, Any]:
    if not isinstance(isolation, dict):
        raise RuntimeError("stdout-isolation metadata is not an object")
    expected_keys = {
        "sitecustomize_path",
        "sitecustomize_sha256",
        "child_pythonpath",
        "child_python_pycache_prefix",
        "child_python_dont_write_bytecode",
        "child_python_no_user_site",
        "child_expected_sha256_environment",
        "python_stdout_capture",
        "native_fd1_capture",
        "activation_marker",
        "pythonpath_directory_policy",
    }
    if set(isolation) != expected_keys:
        raise RuntimeError("stdout-isolation metadata has unexpected fields")
    isolator_hash = isolation.get("sitecustomize_sha256")
    if not isinstance(isolator_hash, str) or re.fullmatch(
        r"[0-9a-f]{64}", isolator_hash
    ) is None:
        raise RuntimeError("stdout-isolation source hash is invalid")
    expected_values = {
        "sitecustomize_path": STDOUT_ISOLATOR.relative_to(REPO).as_posix(),
        "child_pythonpath": STDOUT_ISOLATOR.parent.relative_to(REPO).as_posix(),
        "child_python_pycache_prefix": STDOUT_ISOLATOR_PYCACHE_PREFIX.relative_to(
            REPO
        ).as_posix(),
        "child_python_dont_write_bytecode": "1",
        "child_python_no_user_site": "1",
        "child_expected_sha256_environment": isolator_hash,
        "python_stdout_capture": "stdout",
        "native_fd1_capture": "stderr",
        "activation_marker": f"{STDOUT_ISOLATOR_MARKER_PREFIX}{isolator_hash}",
        "pythonpath_directory_policy": "only-regular-sitecustomize.py",
    }
    for key, expected in expected_values.items():
        if isolation.get(key) != expected:
            raise RuntimeError(f"stdout-isolation metadata field {key} is invalid")
    return isolation


def observed_activation(stderr: str) -> tuple[str | None, int]:
    markers = [
        line
        for line in stderr.splitlines()
        if line.startswith(STDOUT_ISOLATOR_MARKER_PREFIX)
    ]
    return (markers[0] if len(markers) == 1 else None), len(markers)


def expected_identity(start: dict[str, Any]) -> dict[str, Any]:
    identity = {
        "candidate_sha256": start["candidate_sha256"],
        "certifier_sha256": start["certifier_sha256"],
        "gf2_sha256": start["gf2_sha256"],
    }
    isolation = start.get("stdout_isolation")
    if isolation is not None:
        isolation = validate_stdout_isolation_metadata(isolation)
        identity["stdout_isolator_sha256"] = isolation["sitecustomize_sha256"]
        identity["stdout_isolator_activation_marker"] = isolation[
            "activation_marker"
        ]
        identity["stdout_isolator_activation_marker_count"] = 1
        identity["stdout_isolator_pythonpath_directory_clean"] = True
    return identity


def validate_source_batch(
    stage: str, certifier_hash: str, by_id: dict[int, dict[str, Any]]
) -> tuple[Path, dict[str, Any], list[int]]:
    path = RESULTS / "batches" / f"{stage}.json"
    require_under(path, RESULTS / "batches", "source-stage path")
    batch = read_json_object(path)
    if batch.get("stage") != stage:
        raise RuntimeError(f"source batch stage mismatch: {path}")
    if batch.get("certifier_sha256") != certifier_hash:
        raise RuntimeError(f"source batch certifier hash mismatch: {path}")
    aggregates = batch.get("aggregates")
    if not isinstance(aggregates, list):
        raise RuntimeError(f"source batch has no aggregate list: {path}")

    requested: list[int] = []
    for item in aggregates:
        if (
            not isinstance(item, dict)
            or item.get("aggregate_status")
            != "apparent_exact_requires_serial_confirmation"
        ):
            continue
        key = item.get("candidate_key")
        if not isinstance(key, str) or re.fullmatch(r"c[0-9]{7}", key) is None:
            raise RuntimeError(f"invalid candidate key in source batch: {key!r}")
        candidate_id = int(key[1:])
        target = by_id.get(candidate_id)
        if target is None:
            raise RuntimeError(f"source batch candidate is absent from manifest: {key}")
        aggregate_rel = item.get("aggregate_path")
        if not isinstance(aggregate_rel, str):
            raise RuntimeError(f"source batch aggregate path missing for {key}")
        aggregate_path = REPO / aggregate_rel
        require_under(aggregate_path, RESULTS, "source aggregate path")
        aggregate = read_json_object(aggregate_path)
        if aggregate.get("candidate_key") != key:
            raise RuntimeError(f"source aggregate candidate mismatch: {aggregate_path}")
        if aggregate.get("candidate_sha256") != target["candidate_sha256"]:
            raise RuntimeError(f"source aggregate candidate hash mismatch: {aggregate_path}")
        if aggregate.get("certifier_sha256") != certifier_hash:
            raise RuntimeError(f"source aggregate certifier hash mismatch: {aggregate_path}")
        if (
            aggregate.get("aggregate_status")
            != "apparent_exact_requires_serial_confirmation"
        ):
            raise RuntimeError(f"source aggregate is not an apparent closure: {aggregate_path}")
        sides = aggregate.get("sides")
        if not isinstance(sides, dict) or set(sides) != set(SIDES):
            raise RuntimeError(f"source aggregate has invalid sides: {aggregate_path}")
        for side in SIDES:
            side_result = sides[side]
            counts = side_result.get("counts") if isinstance(side_result, dict) else None
            if (
                not isinstance(side_result, dict)
                or side_result.get("status") != "exact"
                or side_result.get("task_count") != target["k"]
                or not isinstance(counts, dict)
                or counts.get("proven_infeasible") != target["k"]
                or any(
                    counts.get(status, 0) != 0
                    for status in (
                        "feasible_refutation",
                        "unknown",
                        "runner_error",
                        "missing",
                    )
                )
            ):
                raise RuntimeError(
                    f"source aggregate side {side} is not closed: {aggregate_path}"
                )
        requested.append(candidate_id)
    return path, batch, requested


def restore_or_validate_authoritative(
    record: dict[str, Any], authoritative_path: Path, output_valid: bool
) -> None:
    parsed = record.get("certifier_output")
    should_exist = record.get("returncode") == 0 and output_valid
    if authoritative_path.is_symlink():
        raise RuntimeError(f"refusing symlink authoritative output: {authoritative_path}")
    if authoritative_path.exists():
        authoritative = read_json_object(authoritative_path)
        if not should_exist or authoritative != parsed:
            raise RuntimeError(f"authoritative output mismatch: {authoritative_path}")
    elif should_exist:
        atomic_json(authoritative_path, parsed)


def validate_completed_record(
    record_path: Path,
    authoritative_path: Path,
    expected_start: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    record = read_json_object(record_path)
    if stable_start_fields(record) != stable_start_fields(expected_start):
        raise RuntimeError(f"completed record identity mismatch: {record_path}")
    if not isinstance(record.get("stdout"), str) or not isinstance(
        record.get("stderr"), str
    ):
        raise RuntimeError(f"completed record does not preserve stdout/stderr: {record_path}")
    if (
        not isinstance(record.get("child_process_cpu_seconds"), (int, float))
        or isinstance(record.get("child_process_cpu_seconds"), bool)
        or record["child_process_cpu_seconds"] < 0
    ):
        raise RuntimeError(f"completed record has no child CPU accounting: {record_path}")

    stdout = record["stdout"]
    parsed_from_stdout: Any = None
    parse_error = None
    if stdout:
        try:
            parsed_from_stdout = json.loads(stdout)
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
    else:
        parse_error = "stdout was empty"
    parsed = record.get("certifier_output")
    if parsed_from_stdout != parsed:
        raise RuntimeError(f"completed record parsed-output mismatch: {record_path}")
    validation_errors, refutation_signals, timed_out = validate_certifier_output(
        parsed, candidate
    )
    if parse_error:
        validation_errors.insert(0, f"invalid JSON: {parse_error}")
    output_valid = isinstance(parsed, dict) and not validation_errors
    expected_identity_values = expected_identity(expected_start)
    identity_after = record.get("identity_after")
    if not isinstance(identity_after, dict):
        raise RuntimeError(f"completed record has no post-run identity: {record_path}")
    observed_marker, observed_marker_count = observed_activation(record["stderr"])
    if expected_start.get("stdout_isolation") is None:
        unexpected_marker = bool(observed_marker_count)
    elif (
        identity_after.get("stdout_isolator_activation_marker") != observed_marker
        or identity_after.get("stdout_isolator_activation_marker_count")
        != observed_marker_count
    ):
        raise RuntimeError(
            f"completed record activation-marker mismatch: {record_path}"
        )
    else:
        unexpected_marker = False
    identity_errors = [
        key
        for key, expected in expected_identity_values.items()
        if identity_after.get(key) != expected
    ]
    if unexpected_marker:
        identity_errors.append("unexpected_stdout_isolator_activation_marker")
    expected_validation = {
        "valid": output_valid,
        "errors": validation_errors,
        "refutation_signal_sides": refutation_signals,
        "timed_out_sides": timed_out,
    }
    if record.get("output_validation") != expected_validation:
        raise RuntimeError(f"completed record output-validation mismatch: {record_path}")
    if record.get("identity_errors") != identity_errors:
        raise RuntimeError(f"completed record identity-validation mismatch: {record_path}")
    if record.get("execution_error") is not None or record.get("returncode") not in (0, None):
        expected_status = "process_error"
    elif identity_errors:
        expected_status = "identity_error"
    elif not output_valid:
        expected_status = "invalid_output"
    elif refutation_signals:
        expected_status = "refutation_signal_requires_witness"
    elif parsed.get("d_exact") is True:
        expected_status = "exact"
    else:
        expected_status = "not_exact"
    if record.get("status") != expected_status:
        raise RuntimeError(f"completed record status mismatch: {record_path}")
    exact = bool(expected_status == "exact" and parsed.get("d_exact") is True)
    if record.get("d_exact") is not exact:
        raise RuntimeError(f"completed record d_exact mismatch: {record_path}")
    restore_or_validate_authoritative(
        record, authoritative_path, output_valid and not identity_errors
    )
    return record


def load_trust_anchor() -> tuple[str, str, str]:
    environment = read_json_object(ENVIRONMENT)
    trust = environment.get("trust_anchor")
    if not isinstance(trust, dict):
        raise RuntimeError(f"missing trust anchor in {ENVIRONMENT}")
    certify_path = REPO / "verify" / "certify.py"
    gf2_path = REPO / "verify" / "gf2.py"
    certifier_hash = sha256(certify_path)
    gf2_hash = sha256(gf2_path)
    if (
        trust.get("certify_path") != "verify/certify.py"
        or trust.get("certify_sha256") != certifier_hash
    ):
        raise RuntimeError("current verify/certify.py does not match captured trust anchor")
    if trust.get("gf2_path") != "verify/gf2.py" or trust.get("gf2_sha256") != gf2_hash:
        raise RuntimeError("current verify/gf2.py does not match captured trust anchor")
    manifest_hash = sha256(TARGETS)
    recorded_manifest = environment.get("manifest")
    if (
        not isinstance(recorded_manifest, dict)
        or recorded_manifest.get("sha256") != manifest_hash
    ):
        raise RuntimeError("current targets.json does not match captured environment")
    return certifier_hash, gf2_hash, manifest_hash


def prepare_output_directory(path: Path, resume: bool) -> None:
    require_under(path, RESULTS, "confirmation output path")
    if path.is_symlink():
        raise RuntimeError(f"refusing symlink output directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise RuntimeError(f"confirmation output is not a directory: {path}")
        if not resume:
            raise FileExistsError(f"refusing to reuse confirmation stage: {path}")
    else:
        path.mkdir(parents=True, exist_ok=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-id", action="append", type=int)
    parser.add_argument("--from-stage")
    parser.add_argument("--confirmation-stage", required=True)
    parser.add_argument("--tlim", type=float, required=True)
    parser.add_argument(
        "--isolate-native-stdout",
        action="store_true",
        help=(
            "load the hash-recorded child-only sitecustomize module that keeps "
            "Python JSON on stdout while capturing native fd-1 writes on stderr"
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="resume only a matching, previously started immutable confirmation stage",
    )
    args = parser.parse_args()
    confirmation_stage = safe_stage(args.confirmation_stage, "--confirmation-stage")
    if args.from_stage:
        args.from_stage = safe_stage(args.from_stage, "--from-stage")
    if not math.isfinite(args.tlim) or args.tlim <= 0:
        raise ValueError("--tlim must be finite and positive")

    manifest = read_json_object(TARGETS)
    targets = manifest.get("targets")
    if not isinstance(targets, list):
        raise RuntimeError("targets.json has no targets list")
    by_id = {item["candidate_id"]: item for item in targets}
    certifier_hash, gf2_hash, manifest_hash = load_trust_anchor()

    requested = list(args.target_id or [])
    source_batch_path = None
    source_batch_hash = None
    if args.from_stage:
        source_batch_path, _, source_ids = validate_source_batch(
            args.from_stage, certifier_hash, by_id
        )
        source_batch_hash = sha256(source_batch_path)
        requested.extend(source_ids)
    requested = list(dict.fromkeys(requested))
    if not requested:
        print("no apparent exact candidates require confirmation")
        return
    unknown_ids = [candidate_id for candidate_id in requested if candidate_id not in by_id]
    if unknown_ids:
        raise ValueError(f"target IDs not in manifest: {unknown_ids}")

    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    stdout_isolation = configure_stdout_isolation(args.isolate_native_stdout, env)
    batch_dir = SERIAL_BATCHES / confirmation_stage
    require_under(batch_dir, SERIAL_BATCHES, "serial batch path")
    batch_start_path = batch_dir / "run-start.json"
    batch_record_path = batch_dir / "record.json"
    batch_start = {
        "schema_version": 1,
        "confirmation_stage": confirmation_stage,
        "requested_candidate_ids": requested,
        "source_stage": args.from_stage,
        "source_batch": (
            source_batch_path.relative_to(REPO).as_posix() if source_batch_path else None
        ),
        "source_batch_sha256": source_batch_hash,
        "manifest_sha256": manifest_hash,
        "certifier_sha256": certifier_hash,
        "gf2_sha256": gf2_hash,
        "per_task_time_limit_seconds": args.tlim,
        # Keep the environment launcher path intact.  Resolving the venv
        # symlink selects the bare uv-managed interpreter and drops the
        # repository environment's installed SciPy/NumPy packages.
        "python_executable": sys.executable,
        "thread_limits": {
            key: env[key]
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }
    if stdout_isolation is not None:
        batch_start["stdout_isolation"] = stdout_isolation

    output_dirs = {
        candidate_id: RESULTS
        / f"c{candidate_id:07d}"
        / "serial-confirmation"
        / confirmation_stage
        for candidate_id in requested
    }
    if args.resume:
        if not batch_dir.exists() and not batch_dir.is_symlink():
            raise FileNotFoundError(
                f"cannot resume a serial stage that does not exist: {batch_dir}"
            )
        prepare_output_directory(batch_dir, True)
        if batch_start_path.is_symlink() or batch_record_path.is_symlink():
            raise RuntimeError(f"refusing symlink metadata in serial batch: {batch_dir}")
        if not batch_start_path.is_file():
            unexpected = [
                path for path in batch_dir.iterdir() if not path.name.startswith(".")
            ]
            if unexpected:
                raise RuntimeError(
                    f"cannot recover serial batch without run-start: {batch_dir}"
                )
            atomic_json(batch_start_path, {**batch_start, "started_at_utc": utc_now()})
        else:
            existing = read_json_object(batch_start_path)
            expected = {**batch_start, "started_at_utc": existing.get("started_at_utc")}
            if existing != expected:
                raise RuntimeError(
                    f"serial batch resume metadata mismatch: {batch_start_path}"
                )
    else:
        collisions = [
            path for path in output_dirs.values() if path.exists() or path.is_symlink()
        ]
        collisions.extend(
            path
            for path in RESULTS.glob(
                f"c*/serial-confirmation/{confirmation_stage}"
            )
            if path.exists() or path.is_symlink()
        )
        sharded_collisions = [
            RESULTS / "batches" / f"{confirmation_stage}-start.json",
            RESULTS / "batches" / f"{confirmation_stage}.json",
        ]
        collisions.extend(
            path for path in sharded_collisions if path.exists() or path.is_symlink()
        )
        if batch_dir.exists() or batch_dir.is_symlink():
            collisions.append(batch_dir)
        if collisions:
            raise FileExistsError(
                f"confirmation stage is not unique; existing paths: {collisions}"
            )
        batch_dir.mkdir(parents=True, exist_ok=False)
        atomic_json(batch_start_path, {**batch_start, "started_at_utc": utc_now()})
    persisted_batch_start = read_json_object(batch_start_path)

    records: list[dict[str, Any]] = []
    for candidate_id in requested:
        target = by_id[candidate_id]
        candidate_path = REPO / target["candidate"]
        require_under(candidate_path, REPO, "candidate path")
        candidate_hash = sha256(candidate_path)
        if candidate_hash != target["candidate_sha256"]:
            raise RuntimeError(f"candidate hash mismatch: {candidate_id}")
        candidate = read_json_object(candidate_path)
        if candidate.get("n") != target.get("n") or candidate.get("k") != target.get("k"):
            raise RuntimeError(f"candidate parameter mismatch: {candidate_id}")

        output_dir = output_dirs[candidate_id]
        prepare_output_directory(output_dir, args.resume)
        start_path = output_dir / "run-start.json"
        record_path = output_dir / "record.json"
        authoritative_path = output_dir / "authoritative-output.json"
        command = [
            sys.executable,
            "verify/certify.py",
            target["candidate"],
            "--tlim",
            str(args.tlim),
        ]
        start_record = {
            "schema_version": 1,
            "confirmation_stage": confirmation_stage,
            "candidate_id": candidate_id,
            "candidate": target["candidate"],
            "candidate_sha256": candidate_hash,
            "certifier_sha256": certifier_hash,
            "gf2_sha256": gf2_hash,
            "per_task_time_limit_seconds": args.tlim,
            "command": command,
        }
        if stdout_isolation is not None:
            start_record["stdout_isolation"] = stdout_isolation

        if start_path.exists():
            if start_path.is_symlink():
                raise RuntimeError(f"refusing symlink run-start: {start_path}")
            if not args.resume:
                raise FileExistsError(f"refusing to overwrite {output_dir}")
            existing_start = read_json_object(start_path)
            if stable_start_fields(existing_start) != stable_start_fields(start_record):
                raise RuntimeError(f"confirmation resume metadata mismatch: {start_path}")
        else:
            unexpected = [
                path for path in output_dir.iterdir() if not path.name.startswith(".")
            ]
            if unexpected:
                raise RuntimeError(
                    f"cannot recover confirmation without run-start: {output_dir}"
                )
            atomic_json(start_path, {**start_record, "started_at_utc": utc_now()})

        if record_path.is_symlink():
            raise RuntimeError(f"refusing symlink completed record: {record_path}")
        if record_path.exists():
            if not args.resume:
                raise FileExistsError(f"refusing to overwrite {record_path}")
            record = validate_completed_record(
                record_path, authoritative_path, start_record, candidate
            )
            records.append(record)
            print(
                f"c{candidate_id:07d}: resume existing status={record['status']} "
                f"d_exact={record['d_exact']}",
                flush=True,
            )
            continue
        if authoritative_path.exists() or authoritative_path.is_symlink():
            raise RuntimeError(
                f"authoritative output exists without record: {authoritative_path}"
            )

        started = utc_now()
        wall_start = time.monotonic()
        parent_cpu_start = time.process_time()
        child_user_start, child_system_start = child_usage()
        completed: subprocess.CompletedProcess[str] | None = None
        execution_error: dict[str, str] | None = None
        try:
            completed = subprocess.run(
                command,
                cwd=REPO,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
        except Exception as exc:
            execution_error = {"type": type(exc).__name__, "message": str(exc)}
        child_user_end, child_system_end = child_usage()

        stdout = completed.stdout if completed is not None else ""
        stderr = completed.stderr if completed is not None else ""
        returncode = completed.returncode if completed is not None else None
        parsed: Any = None
        parse_error = None
        if stdout:
            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError as exc:
                parse_error = str(exc)
        else:
            parse_error = "stdout was empty"
        (
            validation_errors,
            refutation_signal_sides,
            timed_out_sides,
        ) = validate_certifier_output(parsed, candidate)
        if parse_error:
            validation_errors.insert(0, f"invalid JSON: {parse_error}")

        current_identity = {
            "candidate_sha256": sha256(candidate_path),
            "certifier_sha256": sha256(REPO / "verify" / "certify.py"),
            "gf2_sha256": sha256(REPO / "verify" / "gf2.py"),
        }
        marker, marker_count = observed_activation(stderr)
        if stdout_isolation is not None:
            current_identity["stdout_isolator_sha256"] = sha256(STDOUT_ISOLATOR)
            current_identity["stdout_isolator_activation_marker"] = marker
            current_identity["stdout_isolator_activation_marker_count"] = marker_count
            current_identity["stdout_isolator_pythonpath_directory_clean"] = (
                stdout_isolation_directory_clean()
            )
        expected_identity_values = expected_identity(start_record)
        identity_errors = [
            key
            for key, expected in expected_identity_values.items()
            if current_identity[key] != expected
        ]
        if stdout_isolation is None and marker_count:
            identity_errors.append("unexpected_stdout_isolator_activation_marker")
        output_valid = isinstance(parsed, dict) and not validation_errors
        if execution_error is not None or returncode not in (0, None):
            status = "process_error"
        elif identity_errors:
            status = "identity_error"
        elif not output_valid:
            status = "invalid_output"
        elif refutation_signal_sides:
            status = "refutation_signal_requires_witness"
        elif parsed.get("d_exact") is True:
            status = "exact"
        else:
            status = "not_exact"
        exact = status == "exact" and parsed.get("d_exact") is True

        child_user_seconds = max(0.0, child_user_end - child_user_start)
        child_system_seconds = max(0.0, child_system_end - child_system_start)
        record = {
            **start_record,
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "duration_seconds": time.monotonic() - wall_start,
            "parent_process_cpu_seconds": time.process_time() - parent_cpu_start,
            "child_process_user_seconds": child_user_seconds,
            "child_process_system_seconds": child_system_seconds,
            "child_process_cpu_seconds": child_user_seconds + child_system_seconds,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "execution_error": execution_error,
            "certifier_output": parsed,
            "identity_after": current_identity,
            "identity_errors": identity_errors,
            "output_validation": {
                "valid": output_valid,
                "errors": validation_errors,
                "refutation_signal_sides": refutation_signal_sides,
                "timed_out_sides": timed_out_sides,
            },
            "status": status,
            "d_exact": bool(exact),
        }
        atomic_json(record_path, record)
        if completed is not None and returncode == 0 and output_valid and not identity_errors:
            atomic_json(authoritative_path, parsed)
        records.append(record)
        print(
            f"c{candidate_id:07d}: status={status} d_exact={exact} "
            f"duration={record['duration_seconds']:.3f}s "
            f"child_cpu={record['child_process_cpu_seconds']:.3f}s",
            flush=True,
        )
        if status == "refutation_signal_requires_witness":
            raise RuntimeError(
                f"c{candidate_id:07d}: stock serial certifier signaled a lighter "
                f"logical on sides {refutation_signal_sides}; persist an explicit "
                "witness with the sharded recovery path before treating this as "
                "a refutation"
            )
        if status in {"process_error", "identity_error", "invalid_output"}:
            raise RuntimeError(
                f"c{candidate_id:07d}: serial confirmation failed with status {status}; "
                f"see {record_path.relative_to(REPO)}"
            )

    batch_record = {
        **persisted_batch_start,
        "finished_at_utc": utc_now(),
        "results": [
            {
                "candidate_id": record["candidate_id"],
                "status": record["status"],
                "d_exact": record["d_exact"],
                "record": (
                    output_dirs[record["candidate_id"]] / "record.json"
                ).relative_to(REPO).as_posix(),
            }
            for record in records
        ],
    }
    if batch_record_path.exists():
        existing_batch_record = read_json_object(batch_record_path)
        expected_without_finish = {
            key: value for key, value in batch_record.items() if key != "finished_at_utc"
        }
        existing_without_finish = {
            key: value
            for key, value in existing_batch_record.items()
            if key != "finished_at_utc"
        }
        if not args.resume or existing_without_finish != expected_without_finish:
            raise FileExistsError(f"refusing to overwrite {batch_record_path}")
    else:
        atomic_json(batch_record_path, batch_record)

    non_exact = [record for record in records if record.get("d_exact") is not True]
    if non_exact:
        statuses = ", ".join(
            f"c{record['candidate_id']:07d}:{record['status']}" for record in non_exact
        )
        raise RuntimeError(f"serial confirmation completed with non-exact outcomes: {statuses}")


if __name__ == "__main__":
    main()
