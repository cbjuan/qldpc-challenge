"""Build the exact-certification target manifest from the committed findings ledger.

The ledger is the source of truth for canonical candidate artifacts.  This script
checks every candidate/verdict pair before emitting a deterministic manifest for
the separate exact-distance campaign.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parent
REPO = HERE.parents[3]
FINDINGS = CAMPAIGN / "FINDINGS.md"
OUTPUT = HERE / "targets.json"

ROW_RE = re.compile(
    r"^\| `\[\[(\d+),(\d+),(\d+)\]\]` \| (\d+) \|.*"
    r"\| `(artifacts/candidates/[^`]+\.json)` \|$"
)
ID_RE = re.compile(r"^c(\d{7})-")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_path(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def build() -> dict:
    targets = []
    for line in FINDINGS.read_text().splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        n, k, d, weight = (int(match.group(i)) for i in range(1, 5))
        candidate = CAMPAIGN / match.group(5)
        verdict = candidate.with_suffix(".verdict.json")
        if not candidate.is_file() or not verdict.is_file():
            raise FileNotFoundError(f"missing canonical pair: {candidate}, {verdict}")

        doc = json.loads(candidate.read_text())
        gate = json.loads(verdict.read_text())
        if (doc.get("n"), doc.get("k"), doc.get("distance", {}).get("d")) != (n, k, d):
            raise ValueError(f"ledger/candidate parameter mismatch: {candidate}")
        if not gate.get("passed"):
            raise ValueError(f"ledger candidate did not pass its saved gate: {verdict}")
        if gate.get("candidate", {}).get("family") != "bivariate-bicycle":
            raise ValueError(f"wrong family in saved gate: {verdict}")

        id_match = ID_RE.match(candidate.name)
        if not id_match:
            raise ValueError(f"candidate filename has no stable ID: {candidate.name}")
        candidate_id = int(id_match.group(1))
        sides = doc["distance"]
        board_advancing = bool(gate["gates"]["novelty"]["board_advancing"])
        targets.append(
            {
                "candidate_id": candidate_id,
                "n": n,
                "k": k,
                "d": d,
                "d_x_upper": int(sides["X"]["value"]),
                "d_z_upper": int(sides["Z"]["value"]),
                "check_weight": weight,
                "board_advancing": board_advancing,
                "candidate": _repo_path(candidate),
                "verdict": _repo_path(verdict),
                "candidate_sha256": _sha256(candidate),
                "verdict_sha256": _sha256(verdict),
                "logical_milp_tasks": 2 * k,
                "campaign_fom_k2d_over_n": round(k * k * d / n, 12),
                "board_fom_kd2_over_n": round(k * d * d / n, 12),
            }
        )

    targets.sort(key=lambda item: item["candidate_id"])
    if len(targets) != 129:
        raise ValueError(f"expected 129 ledger targets, found {len(targets)}")
    advancing = sum(item["board_advancing"] for item in targets)
    if advancing != 128:
        raise ValueError(f"expected 128 board-advancing targets, found {advancing}")

    return {
        "schema_version": 1,
        "source_ledger": _repo_path(FINDINGS),
        "source_ledger_sha256": _sha256(FINDINGS),
        "target_count": len(targets),
        "board_advancing_target_count": advancing,
        "calibration_target_count": len(targets) - advancing,
        "targets": targets,
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build(), indent=2) + "\n")
    print(f"wrote {_repo_path(OUTPUT)}")
