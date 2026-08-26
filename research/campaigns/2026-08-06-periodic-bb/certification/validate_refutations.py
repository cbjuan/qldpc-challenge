"""Persist trustless-verifier reports for staged MILP refutation witnesses."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RESULTS = HERE / "results"
sys.path.insert(0, str(REPO / "verify"))
import qldpc_verify  # noqa: E402


def main() -> None:
    validated = 0
    for submission in sorted(RESULTS.glob("c*/refutation/*.submission.json")):
        output = submission.with_name(
            submission.name.removesuffix(".submission.json") + ".verification.json"
        )
        if output.exists():
            continue
        doc = json.loads(submission.read_text())
        report = qldpc_verify.verify(doc, refute=False, seed=0)
        if not report.get("ok"):
            raise RuntimeError(f"refutation witness failed verifier: {submission}")
        output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"validated {submission.relative_to(REPO)}", flush=True)
        validated += 1
    print(f"persisted {validated} new refutation verification reports")


if __name__ == "__main__":
    main()
