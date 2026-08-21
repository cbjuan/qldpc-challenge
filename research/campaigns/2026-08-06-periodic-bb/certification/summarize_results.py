"""Build the maintained campaign summary from immutable task evidence."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RESULTS = HERE / "results"
TARGETS = HERE / "targets.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def summarize_target(target: dict) -> dict:
    key = f"c{target['candidate_id']:07d}"
    root = RESULTS / key
    task_records = []
    budgets = set()
    for path in root.glob("attempts/*/tasks/*.json"):
        record = read_json(path)
        if record.get("candidate_sha256") == target["candidate_sha256"]:
            task_records.append((path, record))
            budgets.add(record.get("time_limit_seconds"))

    refutation_indexes = [
        path
        for path in root.glob("refutation/*.json")
        if not path.name.endswith(".submission.json")
    ]
    feasible = [item for item in task_records if item[1].get("status") == "feasible_refutation"]
    if feasible and not refutation_indexes:
        raise RuntimeError(f"{key} has a lighter logical but no persisted submission witness")

    serial_records = []
    for path in root.glob("serial-confirmation/*/record.json"):
        record = read_json(path)
        if (
            record.get("candidate_sha256") == target["candidate_sha256"]
            and record.get("d_exact") is True
        ):
            serial_records.append((path, record))
    exact = bool(serial_records)
    refuted = bool(feasible and refutation_indexes)
    attempts = list(root.glob("attempts/*/run-start.json"))
    apparent = any(
        read_json(path).get("aggregate_status")
        == "apparent_exact_requires_serial_confirmation"
        for path in root.glob("attempts/*/aggregate.json")
    )
    if exact:
        status = "exact"
    elif refuted:
        status = "refuted"
    elif attempts and not apparent:
        status = "timeout"
    else:
        status = "pending"

    side_status = {}
    for side in ("X", "Z"):
        selected = [item for item in task_records if item[1].get("side") == side]
        if exact:
            value = "exact"
        elif any(item[1].get("status") == "feasible_refutation" for item in selected):
            value = "refuted"
        elif apparent:
            value = "pending serial"
        elif selected:
            value = "timeout"
        else:
            value = "pending"
        side_status[side] = value

    return {
        "candidate_id": target["candidate_id"],
        "candidate_key": key,
        "n": target["n"],
        "k": target["k"],
        "d": target["d"],
        "status": status,
        "side_status": side_status,
        "timeout_budgets_seconds": sorted(value for value in budgets if value is not None),
        "solver_wall_seconds": sum(item[1].get("duration_seconds", 0.0) for item in task_records),
        "solver_cpu_seconds": sum(item[1].get("process_cpu_seconds", 0.0) for item in task_records),
        "task_result_count": len(task_records),
        "serial_confirmation": (
            serial_records[-1][0].relative_to(REPO).as_posix() if serial_records else None
        ),
        "refutation_evidence": [path.relative_to(REPO).as_posix() for path in refutation_indexes],
    }


def main() -> None:
    manifest = read_json(TARGETS)
    rows = [summarize_target(target) for target in manifest["targets"] if target["board_advancing"]]
    counts = {
        status: sum(row["status"] == status for row in rows)
        for status in ("exact", "refuted", "timeout", "pending")
    }
    batch_records = [read_json(path) for path in RESULTS.glob("batches/*.json") if not path.name.endswith("-start.json")]
    campaign_batches = [
        batch
        for batch in batch_records
        if any(str(key).startswith("c") for key in batch.get("candidate_keys", []))
    ]
    summary = {
        "schema_version": 1,
        "target_count": len(rows),
        "counts": counts,
        "batch_wall_seconds": sum(batch.get("wall_seconds", 0.0) for batch in campaign_batches),
        "solver_wall_seconds": sum(row["solver_wall_seconds"] for row in rows),
        "solver_cpu_seconds": sum(row["solver_cpu_seconds"] for row in rows),
        "batches": [batch.get("stage") for batch in campaign_batches],
        "targets": rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# Periodic BB exact-certification summary",
        "",
        (
            f"Targets: {len(rows)}; exact: {counts['exact']}; refuted: {counts['refuted']}; "
            f"timeout: {counts['timeout']}; pending: {counts['pending']}."
        ),
        "",
        (
            f"Batch wall time: {summary['batch_wall_seconds']:.1f} s; summed solver wall time: "
            f"{summary['solver_wall_seconds']:.1f} s; summed task CPU time: "
            f"{summary['solver_cpu_seconds']:.1f} s."
        ),
        "",
        "A row is `exact` only after a persisted unmodified serial `verify/certify.py` output has `d_exact: true`.",
        "",
        "| target | parameters | X | Z | overall | budgets (s) | solver wall (s) | CPU (s) |",
        "|---|---:|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        budgets = ",".join(f"{value:g}" for value in row["timeout_budgets_seconds"]) or "—"
        lines.append(
            f"| {row['candidate_key']} | [[{row['n']},{row['k']},{row['d']}]] | "
            f"{row['side_status']['X']} | {row['side_status']['Z']} | {row['status']} | "
            f"{budgets} | {row['solver_wall_seconds']:.1f} | {row['solver_cpu_seconds']:.1f} |"
        )
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
