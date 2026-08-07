#!/usr/bin/env python3
"""Persist final candidates carrying the lightest witness from every saved rung.

This script performs no witness or distance search.  It only compares already
persisted candidate documents, revalidates their stored witnesses, and saves a
fresh consolidated document plus an audit manifest.  Existing artifacts are
never overwritten.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import campaign


def unique_candidate(candidate_dir: Path, pattern: str, *, exclude_fast: bool = False) -> Path:
    matches = sorted(
        path
        for path in candidate_dir.glob(pattern)
        if not path.name.endswith(".evidence.json")
        and not path.name.endswith(".verdict.json")
        and (not exclude_fast or "-fast" not in path.stem)
    )
    if len(matches) != 1:
        raise RuntimeError(f"expected one candidate for {pattern!r}, found {[p.name for p in matches]}")
    return matches[0]


def consolidate(record: dict) -> tuple[Path, Path, dict]:
    candidate_dir = campaign.ARTIFACTS / "candidates"
    prefix = f"c{int(record['candidate_id']):07d}-{record['canonical_key'][:10]}-"
    sources = campaign.candidate_submission_sources(record)
    if not sources:
        raise RuntimeError(f"no persisted submission documents for c{record['candidate_id']}")
    docs = [(path, json.loads(path.read_text())) for path in sources]
    for path, doc in docs:
        if int(doc["n"]) != int(record["n"]) or int(doc["k"]) != int(record["k"]):
            raise RuntimeError(f"candidate parameter drift in {path}")

    HX, HZ = campaign.build_record(record)
    selected: dict[str, dict] = {}
    for side in ("X", "Z"):
        choices = []
        for path, doc in docs:
            side_doc = doc["distance"][side]
            value = int(side_doc["value"])
            support = [int(qubit) for qubit in side_doc["witness"]]
            campaign.validate_fast_witness(HX, HZ, side, support, value)
            choices.append((value, path.name, side_doc))
        value, source_name, side_doc = min(choices, key=lambda item: (item[0], item[1]))
        selected[side] = {
            "value": value,
            "source": source_name,
            "document": copy.deepcopy(side_doc),
        }

    one_million_path = unique_candidate(
        candidate_dir, f"{prefix}1m-python8000reuse8k-s*-fast1000000.json"
    )
    one_million_doc = json.loads(one_million_path.read_text())
    final_doc = copy.deepcopy(one_million_doc)
    for side in ("X", "Z"):
        final_doc["distance"][side] = selected[side]["document"]
    final_doc["distance"]["d"] = min(
        int(final_doc["distance"]["X"]["value"]),
        int(final_doc["distance"]["Z"]["value"]),
    )
    final_doc["name"] = (
        f"[[{final_doc['n']},{final_doc['k']},{final_doc['distance']['d']}]] "
        f"local periodic BB c{record['candidate_id']}"
    )

    final_path = one_million_path.with_name(one_million_path.stem + "-allrungs.json")
    manifest_path = one_million_path.with_name(one_million_path.stem + "-allrungs.evidence.json")
    if final_path.exists() or manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite consolidation for c{record['candidate_id']}")

    manifest = {
        "candidate_id": int(record["candidate_id"]),
        "canonical_key": record["canonical_key"],
        "sources": [path.name for path in sources],
        "selected": {
            side: {
                "source": selected[side]["source"],
                "value": selected[side]["value"],
                "support": [int(qubit) for qubit in selected[side]["document"]["witness"]],
            }
            for side in ("X", "Z")
        },
        "distance": int(final_doc["distance"]["d"]),
    }
    final_doc["provenance"]["notes"] += (
        " Consolidated the lightest validated persisted X/Z witnesses across "
        f"every saved rung; audit={manifest_path.name}."
    )

    errors = campaign.save_submission(final_doc, str(final_path))
    if errors or not final_path.exists():
        raise RuntimeError(f"hard save/schema failure for {final_path}: {errors}")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    json.loads(final_path.read_text())
    json.loads(manifest_path.read_text())
    return final_path, manifest_path, final_doc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True)
    args = parser.parse_args()
    for record in campaign.selected_records(args.selection, []):
        final_path, manifest_path, doc = consolidate(record)
        print(
            f"saved {final_path.name} + {manifest_path.name}: "
            f"[[{doc['n']},{doc['k']},{doc['distance']['d']}]]"
        )


if __name__ == "__main__":
    main()
