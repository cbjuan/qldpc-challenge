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


def atomic_json(path: Path, value: Any, *, overwrite: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite {path}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


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


def serialize_solver_result(result: Any, n: int, H: np.ndarray, logical: np.ndarray, cap: int) -> dict:
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


def run_one_task(task: dict) -> dict:
    """Worker entry point: call the stock predicate on one logical row."""
    started_at = utc_now()
    wall_start = time.monotonic()
    cpu_start = time.process_time()
    memory_before = proc_memory_bytes()
    solver_calls: list[dict] = []
    original_milp = certify.milp
    H = task["H"]
    logical = task["logical"]

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
        lighter = certify._exists_lighter(
            H, logical.reshape(1, -1), task["cutoff"], task["time_limit_seconds"]
        )
        status = {
            True: "feasible_refutation",
            False: "proven_infeasible",
            None: "unknown",
        }[lighter]
        error = None
    except BaseException as exc:  # preserve unexpected worker failures as data
        lighter = None
        status = "runner_error"
        error = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        certify.milp = original_milp

    memory_after = proc_memory_bytes()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "schema_version": 1,
        "candidate_key": task["candidate_key"],
        "candidate_path": task["candidate_path"],
        "candidate_sha256": task["candidate_sha256"],
        "certifier_sha256": task["certifier_sha256"],
        "task_id": task["task_id"],
        "side": task["side"],
        "logical_row_index": task["logical_row_index"],
        "logical_generator_support": np.flatnonzero(logical).astype(int).tolist(),
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
        "stock_predicate_return": lighter,
        "solver": "scipy/HiGHS MILP via verify/certify.py::_exists_lighter",
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


def prior_evidence(spec: dict, certifier_hash: str, task_id: str) -> dict | None:
    evidence = []
    attempts = spec["result_root"] / "attempts"
    if not attempts.is_dir():
        return None
    for path in attempts.glob(f"*/tasks/{task_id}.json"):
        record = json.loads(path.read_text())
        if (
            record.get("candidate_sha256") == spec["candidate_sha256"]
            and record.get("certifier_sha256") == certifier_hash
        ):
            evidence.append((path, record))
    definitive = [item for item in evidence if item[1].get("status") in {"feasible_refutation", "proven_infeasible"}]
    statuses = {item[1]["status"] for item in definitive}
    if len(statuses) > 1:
        raise RuntimeError(f"contradictory definitive evidence for {spec['candidate_key']} {task_id}")
    choices = definitive or evidence
    if not choices:
        return None
    path, record = max(choices, key=lambda item: item[1].get("finished_at_utc", ""))
    return {"path": path.relative_to(REPO).as_posix(), "record": record}


def persist_refutation(task: dict, record: dict, stage: str) -> dict:
    """Persist a feasible MILP witness through make_submission/save_submission.

    The solver witness replaces the corresponding side of the original
    candidate; the other submitted witness is retained.  ``make_submission``
    rechecks both witnesses against the repository GF(2) criteria before either
    copy is saved.
    """
    solver_witnesses = [
        call.get("logical_witness")
        for call in record.get("solver_calls", [])
        if call.get("logical_witness") is not None
    ]
    if not solver_witnesses:
        raise RuntimeError(f"feasible task has no captured witness: {task['task_id']}")
    witness_record = solver_witnesses[0]
    if not all(
        witness_record.get(key)
        for key in ("within_cutoff", "zero_syndrome", "anticommutes_with_logical_row")
    ):
        raise RuntimeError(f"captured MILP witness failed validation: {task['task_id']}")

    candidate_path = REPO / task["candidate_path"]
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

    safe_stage = "".join(char if char.isalnum() or char in "-_" else "-" for char in stage)
    stem = (
        f"{doc['n']}-{doc['k']}-{doc['distance']['d']}-"
        f"{task['candidate_key']}-{safe_stage}-{task['task_id']}"
    )
    result_path = (
        RESULTS
        / task["candidate_key"]
        / "refutation"
        / f"{safe_stage}-{task['task_id']}.submission.json"
    )
    staging_path = REPO / "research" / "candidates" / f"{stem}.json"
    for path in (result_path, staging_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite refutation witness: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        errors = submit_module.save_submission(doc, str(path))
        if errors:
            raise RuntimeError(f"schema errors saving refutation witness {path}: {errors}")
    index = {
        "schema_version": 1,
        "persisted_at_utc": utc_now(),
        "candidate_key": task["candidate_key"],
        "task_id": task["task_id"],
        "side": task["side"],
        "weight": witness_record["weight"],
        "support": witness_record["support"],
        "result_submission": result_path.relative_to(REPO).as_posix(),
        "local_staging_submission": staging_path.relative_to(REPO).as_posix(),
        "result_submission_sha256": sha256(result_path),
        "local_staging_submission_sha256": sha256(staging_path),
    }
    atomic_json(
        RESULTS
        / task["candidate_key"]
        / "refutation"
        / f"{safe_stage}-{task['task_id']}.json",
        index,
    )
    return index


def prepare_candidate(
    spec: dict,
    args: argparse.Namespace,
    certifier_hash: str,
) -> tuple[list[dict], dict]:
    candidate_path = REPO / spec["candidate"]
    doc = json.loads(candidate_path.read_text())
    n = int(doc["n"])
    HX = certify._matrix(doc["checks"]["X"], n)
    HZ = certify._matrix(doc["checks"]["Z"], n)
    sides = {
        "X": (HZ, gf2.logical_basis(HX, HZ)),
        "Z": (HX, gf2.logical_basis(HZ, HX)),
    }
    task_descriptors = []
    new_tasks = []
    for side in ("X", "Z"):
        if side not in doc["distance"]:
            continue
        H, logical_basis = sides[side]
        value = int(doc["distance"][side]["value"])
        for row_index, logical in enumerate(logical_basis):
            task_id = f"{side}-{row_index:04d}"
            prior = prior_evidence(spec, certifier_hash, task_id) if args.reuse_definitive else None
            inherited = bool(
                prior and prior["record"].get("status") in {"feasible_refutation", "proven_infeasible"}
            )
            task_descriptors.append(
                {
                    "task_id": task_id,
                    "side": side,
                    "logical_row_index": row_index,
                    "cutoff": value - 1,
                    "inherited": inherited,
                    "evidence_path": prior["path"] if inherited else None,
                }
            )
            if inherited:
                continue
            new_tasks.append(
                {
                    "candidate_key": spec["candidate_key"],
                    "candidate_path": spec["candidate"],
                    "candidate_sha256": spec["candidate_sha256"],
                    "certifier_sha256": certifier_hash,
                    "task_id": task_id,
                    "side": side,
                    "logical_row_index": row_index,
                    "cutoff": value - 1,
                    "time_limit_seconds": args.tlim,
                    "H": H,
                    "logical": logical,
                }
            )

    expected_tasks = 2 * int(doc["k"])
    if len(task_descriptors) != expected_tasks:
        raise RuntimeError(
            f"{spec['candidate_key']}: expected {expected_tasks} logical tasks, got {len(task_descriptors)}"
        )
    run_dir = spec["result_root"] / "attempts" / args.stage
    start_path = run_dir / "run-start.json"
    start_record = {
        "schema_version": 1,
        "stage": args.stage,
        "started_at_utc": utc_now(),
        "candidate_key": spec["candidate_key"],
        "candidate_path": spec["candidate"],
        "candidate_sha256": spec["candidate_sha256"],
        "certifier_sha256": certifier_hash,
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
            side: array_sha256(basis) for side, (_, basis) in sides.items()
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
    if start_path.exists():
        if not args.resume:
            raise FileExistsError(f"stage exists; pass --resume: {run_dir}")
        existing = json.loads(start_path.read_text())
        for key in ("candidate_sha256", "certifier_sha256", "expected_task_count"):
            if existing.get(key) != start_record.get(key):
                raise RuntimeError(f"resume metadata mismatch in {start_path}: {key}")
    else:
        atomic_json(start_path, start_record)
    tasks_path = run_dir / "tasks"
    tasks_path.mkdir(parents=True, exist_ok=True)
    if args.resume:
        new_tasks = [task for task in new_tasks if not (tasks_path / f"{task['task_id']}.json").exists()]
    context = {
        "spec": spec,
        "doc": doc,
        "run_dir": run_dir,
        "task_descriptors": task_descriptors,
        "new_task_count": len(new_tasks),
    }
    return new_tasks, context


def aggregate_candidate(context: dict, certifier_hash: str) -> dict:
    spec = context["spec"]
    run_dir = context["run_dir"]
    tasks = []
    for descriptor in context["task_descriptors"]:
        current = run_dir / "tasks" / f"{descriptor['task_id']}.json"
        if current.is_file():
            record = json.loads(current.read_text())
            path = current
        else:
            prior = prior_evidence(spec, certifier_hash, descriptor["task_id"])
            if prior is None:
                record = {
                    "task_id": descriptor["task_id"],
                    "side": descriptor["side"],
                    "status": "missing",
                    "duration_seconds": 0.0,
                    "process_cpu_seconds": 0.0,
                }
                path = None
            else:
                record = prior["record"]
                path = REPO / prior["path"]
        tasks.append(
            {
                "task_id": descriptor["task_id"],
                "side": descriptor["side"],
                "status": record["status"],
                "evidence_path": path.relative_to(REPO).as_posix() if path else None,
                "duration_seconds": record.get("duration_seconds", 0.0),
                "process_cpu_seconds": record.get("process_cpu_seconds", 0.0),
            }
        )
    sides = {}
    for side in ("X", "Z"):
        selected = [task for task in tasks if task["side"] == side]
        counts = {
            status: sum(task["status"] == status for task in selected)
            for status in ("proven_infeasible", "feasible_refutation", "unknown", "runner_error", "missing")
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
        "schema_version": 1,
        "stage": run_dir.name,
        "finished_at_utc": utc_now(),
        "candidate_key": spec["candidate_key"],
        "candidate_path": spec["candidate"],
        "candidate_sha256": spec["candidate_sha256"],
        "certifier_sha256": certifier_hash,
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
        "task_wall_seconds_sum": sum(task["duration_seconds"] for task in tasks),
        "task_cpu_seconds_sum": sum(task["process_cpu_seconds"] for task in tasks),
        "tasks": tasks,
    }


def task_stream(
    specs: list[dict], args: argparse.Namespace, certifier_hash: str, contexts: list[dict]
) -> Iterator[tuple[dict, Path]]:
    for spec in specs:
        new_tasks, context = prepare_candidate(spec, args, certifier_hash)
        contexts.append(context)
        for task in new_tasks:
            yield task, context["run_dir"] / "tasks" / f"{task['task_id']}.json"


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
    if not 1 <= args.workers <= (os.cpu_count() or 1):
        raise ValueError(f"workers must be in [1, {os.cpu_count()}]")
    if args.tlim <= 0:
        raise ValueError("--tlim must be positive")

    specs = candidate_specs(args)
    certifier_hash = sha256(VERIFY / "certify.py")
    batch_dir = RESULTS / "batches"
    batch_start_path = batch_dir / f"{args.stage}-start.json"
    batch_output_path = batch_dir / f"{args.stage}.json"
    if batch_output_path.exists() and not args.resume:
        raise FileExistsError(batch_output_path)
    batch_started = utc_now()
    batch_wall_start = time.monotonic()
    start_record = {
        "schema_version": 1,
        "stage": args.stage,
        "started_at_utc": batch_started,
        "certifier_sha256": certifier_hash,
        "workers": args.workers,
        "task_time_limit_seconds": args.tlim,
        "reuse_definitive": args.reuse_definitive,
        "candidate_keys": [spec["candidate_key"] for spec in specs],
    }
    if not batch_start_path.exists():
        atomic_json(batch_start_path, start_record)
    elif not args.resume:
        raise FileExistsError(batch_start_path)

    contexts: list[dict] = []
    stream = iter(task_stream(specs, args, certifier_hash, contexts))
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
                        "schema_version": 1,
                        "candidate_key": task["candidate_key"],
                        "candidate_path": task["candidate_path"],
                        "candidate_sha256": task["candidate_sha256"],
                        "certifier_sha256": task["certifier_sha256"],
                        "task_id": task["task_id"],
                        "side": task["side"],
                        "logical_row_index": task["logical_row_index"],
                        "cutoff": task["cutoff"],
                        "time_limit_seconds": task["time_limit_seconds"],
                        "seed": None,
                        "finished_at_utc": utc_now(),
                        "duration_seconds": 0.0,
                        "process_cpu_seconds": 0.0,
                        "status": "runner_error",
                        "stock_predicate_return": None,
                        "solver_calls": [],
                        "error": {
                            "type": type(exc).__name__,
                            "message": str(exc),
                            "traceback": "".join(traceback.format_exception(exc)),
                        },
                    }
                atomic_json(output_path, record)
                if record["status"] == "feasible_refutation" and task["candidate_key"].startswith("c"):
                    persisted = persist_refutation(task, record, args.stage)
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
        atomic_json(context["run_dir"] / "aggregate.json", aggregate, overwrite=args.resume)
        aggregates.append(aggregate)
    status_counts = {
        status: sum(item["aggregate_status"] == status for item in aggregates)
        for status in ("apparent_exact_requires_serial_confirmation", "refuted", "timeout")
    }
    batch = {
        **start_record,
        "finished_at_utc": utc_now(),
        "wall_seconds": time.monotonic() - batch_wall_start,
        "submitted_task_count": submitted,
        "completed_task_count": completed,
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
    atomic_json(batch_output_path, batch, overwrite=args.resume)
    print(json.dumps({"stage": args.stage, "status_counts": status_counts}, indent=2))


if __name__ == "__main__":
    main()
