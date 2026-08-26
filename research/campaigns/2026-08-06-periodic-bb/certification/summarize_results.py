"""Build the maintained campaign summary from immutable task evidence."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RESULTS = HERE / "results"
TARGETS = HERE / "targets.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def has_valid_witness(record: dict) -> bool:
    return any(
        witness is not None
        and witness.get("within_cutoff") is True
        and witness.get("zero_syndrome") is True
        and witness.get("anticommutes_with_logical_row") is True
        for witness in (
            call.get("logical_witness") for call in record.get("solver_calls", [])
        )
    )


def summarize_target(target: dict) -> dict:
    key = f"c{target['candidate_id']:07d}"
    root = RESULTS / key
    certifier_hash = sha256(REPO / "verify/certify.py")
    task_records = []
    budgets = set()
    for path in root.glob("attempts/*/tasks/*.json"):
        record = read_json(path)
        if (
            record.get("candidate_sha256") == target["candidate_sha256"]
            and record.get("certifier_sha256") == certifier_hash
        ):
            task_records.append((path, record))
            budgets.add(record.get("time_limit_seconds"))

    refutation_indexes = []
    for path in root.glob("refutation/*.json"):
        if path.name.endswith(".submission.json"):
            continue
        index = read_json(path)
        if (
            index.get("candidate_sha256") != target["candidate_sha256"]
            or index.get("certifier_sha256") != certifier_hash
        ):
            continue
        source = REPO / index["source_task_result"]
        submission = REPO / index["result_submission"]
        verification = path.with_name(path.stem + ".verification.json")
        if not source.is_file() or not submission.is_file() or not verification.is_file():
            raise RuntimeError(f"incomplete refutation index: {path}")
        source_record = read_json(source)
        if not has_valid_witness(source_record):
            raise RuntimeError(f"refutation source has no valid witness: {source}")
        if sha256(submission) != index["result_submission_sha256"]:
            raise RuntimeError(f"refutation submission hash mismatch: {submission}")
        if read_json(verification).get("ok") is not True:
            raise RuntimeError(f"refutation submission failed verification: {verification}")
        refutation_indexes.append((path, index))

    witnessed_tasks = [item for item in task_records if has_valid_witness(item[1])]
    indexed_task_ids = {item[1]["task_id"] for item in refutation_indexes}
    unpersisted = [item for item in witnessed_tasks if item[1]["task_id"] not in indexed_task_ids]
    if unpersisted:
        raise RuntimeError(f"{key} has lighter logicals without persisted submissions")

    serial_records = []
    for path in root.glob("serial-confirmation/*/record.json"):
        record = read_json(path)
        if record.get("candidate_sha256") != target["candidate_sha256"]:
            continue
        if record.get("certifier_sha256") != certifier_hash:
            continue
        authoritative_path = path.with_name("authoritative-output.json")
        if not authoritative_path.is_file():
            continue
        authoritative = read_json(authoritative_path)
        if authoritative != record.get("certifier_output"):
            raise RuntimeError(f"serial output mismatch: {path}")
        if (
            record.get("returncode") == 0
            and record.get("d_exact") is True
            and authoritative.get("d_exact") is True
            and all(side.get("exact") is True for side in authoritative.get("sides", {}).values())
        ):
            serial_records.append((path, record))
    exact = bool(serial_records)
    refuted = bool(refutation_indexes)
    if exact and refuted:
        raise RuntimeError(f"contradictory exact and refuted evidence for {key}")

    side_status = {}
    for side in ("X", "Z"):
        selected = [item for item in task_records if item[1].get("side") == side]
        by_task: dict[str, list[dict]] = {}
        for _, record in selected:
            by_task.setdefault(record["task_id"], []).append(record)
        side_refuted = any(index["side"] == side for _, index in refutation_indexes)
        proven = sum(
            any(record.get("status") == "proven_infeasible" for record in records)
            for records in by_task.values()
        )
        if exact:
            value = "exact"
        elif side_refuted:
            value = "refuted"
        elif proven == target["k"]:
            value = "closed (pending serial)"
        elif selected:
            value = "timeout"
        else:
            value = "pending"
        side_status[side] = value

    apparent = all(value == "closed (pending serial)" for value in side_status.values())
    if exact:
        status = "exact"
    elif refuted:
        status = "refuted"
    elif apparent:
        status = "pending"
    elif task_records:
        status = "timeout"
    else:
        status = "pending"

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
        "refutation_evidence": [
            path.relative_to(REPO).as_posix() for path, _ in refutation_indexes
        ],
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
