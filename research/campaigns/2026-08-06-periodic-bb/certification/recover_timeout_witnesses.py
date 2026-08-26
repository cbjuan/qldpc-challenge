"""Persist valid logical incumbents embedded in timeout task records.

The source task JSON remains immutable. Each incumbent is independently
rechecked against the current candidate matrices and logical-basis row before
the persistence-first submission path is invoked.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import run_sharded as runner


def task_from_record(
    record: dict,
    target: dict,
    *,
    certifier_hash: str,
    gf2_hash: str,
    runner_hash: str,
) -> dict:
    candidate_path = runner.REPO / target["candidate"]
    if runner.sha256(candidate_path) != target["candidate_sha256"]:
        raise RuntimeError(f"candidate hash mismatch: {target['candidate_id']}")
    if record.get("candidate_path") != target["candidate"]:
        raise RuntimeError(f"candidate path mismatch: {record.get('candidate_key')}")
    if record.get("candidate_sha256") != target["candidate_sha256"]:
        raise RuntimeError(f"candidate record hash mismatch: {record.get('candidate_key')}")
    if record.get("certifier_sha256") != certifier_hash:
        raise RuntimeError(f"certifier hash mismatch: {record.get('candidate_key')}")

    doc = json.loads(candidate_path.read_text())
    n = int(doc["n"])
    HX = runner.certify._matrix(doc["checks"]["X"], n)
    HZ = runner.certify._matrix(doc["checks"]["Z"], n)
    side = record.get("side")
    if side == "X":
        H = HZ
        basis = runner.gf2.logical_basis(HX, HZ)
    elif side == "Z":
        H = HX
        basis = runner.gf2.logical_basis(HZ, HX)
    else:
        raise RuntimeError(f"invalid task side: {side!r}")
    row_index = record.get("logical_row_index")
    if type(row_index) is not int or not 0 <= row_index < len(basis):
        raise RuntimeError(f"invalid logical row index: {row_index!r}")
    task_id = f"{side}-{row_index:04d}"
    if record.get("task_id") != task_id:
        raise RuntimeError(f"task ID mismatch: {record.get('task_id')!r} != {task_id!r}")
    H_rref, H_pivots = runner.gf2.rref(H)
    task = {
        "candidate_key": f"c{target['candidate_id']:07d}",
        "candidate_path": target["candidate"],
        "candidate_sha256": target["candidate_sha256"],
        "certifier_sha256": certifier_hash,
        "gf2_sha256": gf2_hash,
        "runner_sha256": runner_hash,
        "task_id": task_id,
        "side": side,
        "logical_row_index": row_index,
        "cutoff": int(doc["distance"][side]["value"]) - 1,
        "time_limit_seconds": record.get("time_limit_seconds"),
        "H": H,
        "H_rref": H_rref,
        "H_pivots": H_pivots,
        "logical": basis[row_index],
    }
    runner.validate_task_record(record, task, require_runtime_identity=False)
    return task


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-stage", action="append", required=True)
    parser.add_argument("--batch-name")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    source_stages = list(dict.fromkeys(args.source_stage))
    for stage in source_stages:
        runner.validate_artifact_name(stage, label="source stage")
    if args.check_only:
        if args.batch_name is not None:
            parser.error("--batch-name is not used with --check-only")
    elif args.batch_name is None:
        parser.error("--batch-name is required unless --check-only is used")
    else:
        runner.validate_artifact_name(args.batch_name, label="batch name")

    manifest, _ = runner.load_manifest()
    by_key = {
        f"c{target['candidate_id']:07d}": target for target in manifest["targets"]
    }
    certifier_hash = runner.sha256(runner.VERIFY / "certify.py")
    gf2_hash = runner.sha256(runner.VERIFY / "gf2.py")
    runner_hash = runner.sha256(Path(runner.__file__))
    recovered = []
    inspected_records = 0
    for source_stage in source_stages:
        pattern = f"c*/attempts/{source_stage}/tasks/*.json"
        for task_path in sorted(runner.RESULTS.glob(pattern)):
            record = json.loads(task_path.read_text())
            inspected_records += 1
            if not any(
                isinstance(call.get("logical_witness"), dict)
                for call in record.get("solver_calls", [])
            ):
                continue
            candidate_key = record.get("candidate_key")
            target = by_key.get(candidate_key)
            if target is None:
                raise RuntimeError(f"unknown candidate key in {task_path}: {candidate_key!r}")
            expected_root = (
                runner.RESULTS / candidate_key / "attempts" / source_stage / "tasks"
            )
            if task_path.parent != expected_root:
                raise RuntimeError(f"task path/candidate mismatch: {task_path}")
            task = task_from_record(
                record,
                target,
                certifier_hash=certifier_hash,
                gf2_hash=gf2_hash,
                runner_hash=runner_hash,
            )
            if not runner.has_valid_witness(record, task):
                continue
            task["source_task_result"] = task_path.relative_to(runner.REPO).as_posix()
            index = runner.persist_refutation(
                task, record, source_stage, check_only=args.check_only
            )
            recovered.append(index)
            verb = "validated" if args.check_only else "persisted"
            print(
                f"{verb} {record['candidate_key']} {record['task_id']} "
                f"weight={index['weight']}",
                flush=True,
            )

    result = {
        "schema_version": 2,
        "completed_at_utc": runner.utc_now(),
        "source_stages": source_stages,
        "check_only": args.check_only,
        "candidate_manifest": runner.MANIFEST_PATH.relative_to(runner.REPO).as_posix(),
        "candidate_manifest_sha256": runner.sha256(runner.MANIFEST_PATH),
        "certifier_sha256": certifier_hash,
        "gf2_sha256": gf2_hash,
        "runner_sha256": runner_hash,
        "inspected_task_record_count": inspected_records,
        "validated_refutation_count": len(recovered),
        "refutations": recovered,
    }
    if not args.check_only:
        output = runner.RESULTS / "batches" / f"{args.batch_name}.json"
        runner.atomic_json(output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
