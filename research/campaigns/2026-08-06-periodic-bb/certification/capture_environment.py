"""Capture immutable provenance for the periodic-BB certification campaign."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np
import scipy
from scipy.optimize._highspy import _core as highs_core


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TARGETS = HERE / "targets.json"
RESULTS = HERE / "results"
OUTPUT = RESULTS / "environment.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True).strip()


def meminfo() -> dict[str, int]:
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, raw = line.split(":", 1)
        values[key] = int(raw.strip().split()[0]) * 1024
    return values


def main() -> None:
    manifest = json.loads(TARGETS.read_text())
    candidate_hashes = []
    failures = []
    for target in manifest["targets"]:
        candidate = REPO / target["candidate"]
        verdict = REPO / target["verdict"]
        candidate_actual = sha256(candidate)
        verdict_actual = sha256(verdict)
        row = {
            "candidate_id": target["candidate_id"],
            "candidate": target["candidate"],
            "candidate_expected_sha256": target["candidate_sha256"],
            "candidate_actual_sha256": candidate_actual,
            "verdict": target["verdict"],
            "verdict_expected_sha256": target["verdict_sha256"],
            "verdict_actual_sha256": verdict_actual,
            "verified": (
                candidate_actual == target["candidate_sha256"]
                and verdict_actual == target["verdict_sha256"]
            ),
        }
        candidate_hashes.append(row)
        if not row["verified"]:
            failures.append(target["candidate_id"])

    if failures:
        raise RuntimeError(f"target hash mismatches: {failures}")

    mem = meminfo()
    provenance = {
        "schema_version": 1,
        "captured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository": {
            "commit": command("git", "rev-parse", "HEAD"),
            "branch": command("git", "branch", "--show-current"),
            "origin": command("git", "remote", "get-url", "origin"),
            "status_porcelain": command("git", "status", "--short"),
        },
        "trust_anchor": {
            "certify_path": "verify/certify.py",
            "certify_sha256": sha256(REPO / "verify/certify.py"),
            "gf2_path": "verify/gf2.py",
            "gf2_sha256": sha256(REPO / "verify/gf2.py"),
        },
        "manifest": {
            "path": TARGETS.relative_to(REPO).as_posix(),
            "sha256": sha256(TARGETS),
            "target_count": manifest["target_count"],
            "board_advancing_target_count": manifest["board_advancing_target_count"],
            "all_candidate_and_verdict_hashes_verified": True,
        },
        "software": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "highs": highs_core._Highs().version(),
        },
        "host": {
            "platform": platform.platform(),
            "uname": list(platform.uname()),
            "lscpu": json.loads(command("lscpu", "-J")),
            "memory_bytes": {
                "total": mem["MemTotal"],
                "available": mem["MemAvailable"],
                "swap_total": mem["SwapTotal"],
            },
        },
        "thread_limits": {
            name: os.environ.get(name)
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "candidate_hashes": candidate_hashes,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite {OUTPUT}")
    OUTPUT.write_text(json.dumps(provenance, indent=2) + "\n")
    print(OUTPUT.relative_to(REPO))


if __name__ == "__main__":
    main()
