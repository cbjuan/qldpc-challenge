"""Cross-check stock and sharded calibration outputs."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RESULTS = HERE / "results"
FIXTURES = ("7-1-3", "16-2-4", "36-2-6", "64-2-8")
SHARDED_STAGE = "calibration-sharded-threadcap-v2"


def main() -> None:
    comparisons = []
    for stem in FIXTURES:
        stock_path = RESULTS / "calibration" / "stock" / f"{stem}.json"
        sharded_path = (
            RESULTS
            / "calibration"
            / "sharded"
            / stem
            / "attempts"
            / SHARDED_STAGE
            / "aggregate.json"
        )
        stock = json.loads(stock_path.read_text())
        sharded = json.loads(sharded_path.read_text())
        matched = bool(
            stock["calibration_passed"]
            and stock["certifier_output"]["d_exact"] is True
            and sharded["aggregate_status"]
            == "apparent_exact_requires_serial_confirmation"
            and all(value["status"] == "exact" for value in sharded["sides"].values())
            and sharded["parameters"]["d"] == stock["certifier_output"]["d"]
        )
        comparisons.append(
            {
                "fixture": stem,
                "matched": matched,
                "stock_result": stock_path.relative_to(REPO).as_posix(),
                "sharded_result": sharded_path.relative_to(REPO).as_posix(),
                "d": sharded["parameters"]["d"],
            }
        )
    stress_path = (
        RESULTS
        / "calibration"
        / "sharded"
        / "126-28-8"
        / "attempts"
        / SHARDED_STAGE
        / "aggregate.json"
    )
    stress = json.loads(stress_path.read_text())
    passed = all(item["matched"] for item in comparisons) and stress["aggregate_status"] == "timeout"
    result = {
        "schema_version": 1,
        "validated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "passed": passed,
        "stock_sharded_exact_matches": comparisons,
        "timeout_conservatism_check": {
            "fixture": "126-28-8",
            "expected": "timeout",
            "observed": stress["aggregate_status"],
            "result": stress_path.relative_to(REPO).as_posix(),
            "passed": stress["aggregate_status"] == "timeout",
        },
    }
    output = RESULTS / "calibration" / "validation.json"
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not passed:
        raise RuntimeError("calibration validation failed")


if __name__ == "__main__":
    main()
