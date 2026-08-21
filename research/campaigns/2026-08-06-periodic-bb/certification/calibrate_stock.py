"""Run and persist stock-certifier calibration against exact board fixtures."""

from __future__ import annotations

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
OUTPUT = HERE / "results" / "calibration" / "stock"
FIXTURES = ("7-1-3", "16-2-4", "36-2-6", "64-2-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )
    failures = []
    for stem in FIXTURES:
        candidate = REPO / "codes" / f"{stem}.json"
        expected_path = REPO / "certs" / f"{stem}.json"
        output_path = OUTPUT / f"{stem}.json"
        if output_path.exists():
            raise FileExistsError(f"refusing to overwrite {output_path}")
        started = dt.datetime.now(dt.timezone.utc)
        t0 = time.monotonic()
        completed = subprocess.run(
            [sys.executable, "verify/certify.py", str(candidate), "--tlim", "120"],
            cwd=REPO,
            env=env,
            text=True,
            capture_output=True,
        )
        duration = time.monotonic() - t0
        parsed = None
        if completed.returncode == 0:
            try:
                parsed = json.loads(completed.stdout)
            except json.JSONDecodeError:
                pass
        expected = json.loads(expected_path.read_text())
        passed = bool(
            completed.returncode == 0
            and parsed
            and parsed.get("d_exact") is True
            and parsed.get("d") == expected.get("d")
            and all(side.get("exact") for side in parsed.get("sides", {}).values())
        )
        record = {
            "schema_version": 1,
            "fixture": stem,
            "started_at_utc": started.isoformat(),
            "duration_seconds": duration,
            "command": [
                sys.executable,
                "verify/certify.py",
                candidate.relative_to(REPO).as_posix(),
                "--tlim",
                "120",
            ],
            "candidate_sha256": sha256(candidate),
            "certifier_sha256": sha256(REPO / "verify/certify.py"),
            "expected_certificate_sha256": sha256(expected_path),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "certifier_output": parsed,
            "calibration_passed": passed,
        }
        output_path.write_text(json.dumps(record, indent=2) + "\n")
        print(f"{stem}: passed={passed} duration={duration:.3f}s", flush=True)
        if not passed:
            failures.append(stem)
    if failures:
        raise RuntimeError(f"stock calibration failures: {failures}")


if __name__ == "__main__":
    main()
