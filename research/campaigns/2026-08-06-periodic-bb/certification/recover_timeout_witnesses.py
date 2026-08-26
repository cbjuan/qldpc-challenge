"""Persist valid logical incumbents embedded in older timeout task records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_sharded import REPO, RESULTS, has_valid_witness, persist_refutation, utc_now


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-stage", required=True)
    parser.add_argument("--batch-name", required=True)
    args = parser.parse_args()
    recovered = []
    pattern = f"c*/attempts/{args.source_stage}/tasks/*.json"
    for task_path in sorted(RESULTS.glob(pattern)):
        record = json.loads(task_path.read_text())
        if not has_valid_witness(record):
            continue
        task = {
            "candidate_key": record["candidate_key"],
            "candidate_path": record["candidate_path"],
            "candidate_sha256": record["candidate_sha256"],
            "task_id": record["task_id"],
            "side": record["side"],
            "source_task_result": task_path.relative_to(REPO).as_posix(),
        }
        index = persist_refutation(task, record, args.source_stage)
        recovered.append(index)
        print(
            f"persisted {record['candidate_key']} {record['task_id']} "
            f"weight={index['weight']}",
            flush=True,
        )
    output = RESULTS / "batches" / f"{args.batch_name}.json"
    if output.exists():
        raise FileExistsError(output)
    output.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "recovered_at_utc": utc_now(),
                "source_stage": args.source_stage,
                "recovered_count": len(recovered),
                "refutations": recovered,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"recovered {len(recovered)} validated timeout incumbents")


if __name__ == "__main__":
    main()
