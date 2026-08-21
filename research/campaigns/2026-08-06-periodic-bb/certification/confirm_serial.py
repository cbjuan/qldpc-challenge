"""Persist authoritative stock-serial confirmations for apparent closures."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RESULTS = HERE / "results"
TARGETS = HERE / "targets.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-id", action="append", type=int)
    parser.add_argument("--from-stage")
    parser.add_argument("--confirmation-stage", required=True)
    parser.add_argument("--tlim", type=float, required=True)
    args = parser.parse_args()
    manifest = json.loads(TARGETS.read_text())
    by_id = {item["candidate_id"]: item for item in manifest["targets"]}
    requested = list(args.target_id or [])
    if args.from_stage:
        batch = json.loads((RESULTS / "batches" / f"{args.from_stage}.json").read_text())
        requested.extend(
            int(item["candidate_key"][1:])
            for item in batch["aggregates"]
            if item["aggregate_status"] == "apparent_exact_requires_serial_confirmation"
            and item["candidate_key"].startswith("c")
        )
    requested = list(dict.fromkeys(requested))
    if not requested:
        print("no apparent exact candidates require confirmation")
        return

    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    certifier_hash = sha256(REPO / "verify/certify.py")
    for candidate_id in requested:
        target = by_id[candidate_id]
        candidate = REPO / target["candidate"]
        if sha256(candidate) != target["candidate_sha256"]:
            raise RuntimeError(f"candidate hash mismatch: {candidate_id}")
        output_dir = (
            RESULTS
            / f"c{candidate_id:07d}"
            / "serial-confirmation"
            / args.confirmation_stage
        )
        record_path = output_dir / "record.json"
        authoritative_path = output_dir / "authoritative-output.json"
        if record_path.exists() or authoritative_path.exists():
            raise FileExistsError(f"refusing to overwrite {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            "verify/certify.py",
            target["candidate"],
            "--tlim",
            str(args.tlim),
        ]
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        wall_start = time.monotonic()
        cpu_start = time.process_time()
        completed = subprocess.run(
            command,
            cwd=REPO,
            env=env,
            text=True,
            capture_output=True,
        )
        parsed = None
        if completed.returncode == 0:
            try:
                parsed = json.loads(completed.stdout)
            except json.JSONDecodeError:
                pass
        exact = bool(parsed and parsed.get("d_exact") is True)
        record = {
            "schema_version": 1,
            "candidate_id": candidate_id,
            "candidate": target["candidate"],
            "candidate_sha256": target["candidate_sha256"],
            "certifier_sha256": certifier_hash,
            "started_at_utc": started,
            "finished_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "duration_seconds": time.monotonic() - wall_start,
            "parent_process_cpu_seconds": time.process_time() - cpu_start,
            "per_task_time_limit_seconds": args.tlim,
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "certifier_output": parsed,
            "d_exact": exact,
        }
        record_path.write_text(json.dumps(record, indent=2) + "\n")
        if parsed is not None:
            authoritative_path.write_text(json.dumps(parsed, indent=2) + "\n")
        print(
            f"c{candidate_id:07d}: d_exact={exact} "
            f"duration={record['duration_seconds']:.3f}s",
            flush=True,
        )


if __name__ == "__main__":
    main()
