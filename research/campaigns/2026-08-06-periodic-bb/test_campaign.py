#!/usr/bin/env python3
"""Structural regression tests for the local periodic-BB campaign."""

from __future__ import annotations

import hashlib
import json
import unittest

import campaign


OLD_PROPOSAL_END = 51_663
OLD_PROPOSAL_DIGEST = "dc5a3eef67f8a668ba8f096cc06ec00904512b9ed29f4cdbb8cb4b73d44144c0"
SELECTION_IDS = {
    49_973, 49_984, 50_011, 50_033, 50_071, 50_490,
    50_526, 50_584, 50_670, 50_719, 50_947, 51_066,
}
SOURCE_KEYS = {
    48_101: "90fdf16c76dcff01e74121ab",
    48_487: "c58b080116488e2ecc27f767",
    48_911: "70f214640c9262c9476079cc",
}
SOURCE_FINAL_ARTIFACTS = {
    48_101: "c0048101-90fdf16c76-continuation-final-allrungs-s1427629452",
    48_487: "c0048487-c58b080116-continuation-final-allrungs-s1030785542",
    48_911: "c0048911-70f214640c-continuation-final-allrungs-s283679173",
}


def proposal_digest(start: int, stop: int) -> str:
    digest = hashlib.sha256()
    for candidate_id in range(start, stop):
        payload = json.dumps(
            campaign.proposal(candidate_id), sort_keys=True, separators=(",", ":")
        ).encode()
        digest.update(len(payload).to_bytes(4, "big"))
        digest.update(payload)
    return digest.hexdigest()


class CampaignStructureTest(unittest.TestCase):
    def test_existing_candidate_ids_are_immutable(self) -> None:
        self.assertEqual(campaign.REFRESHED_HIGH_DISTANCE_START, OLD_PROPOSAL_END)
        self.assertEqual(
            proposal_digest(campaign.VALIDATED_HIGH_DISTANCE_START, OLD_PROPOSAL_END),
            OLD_PROPOSAL_DIGEST,
        )

    def test_next_selection_is_an_exact_connected_ledger_subset(self) -> None:
        selection_path = campaign.ARTIFACTS / "selection-validated-highd-epoch2-002.json"
        selection = json.loads(selection_path.read_text())
        records = selection["records"]
        ledger = campaign.load_records()

        self.assertEqual(selection["selection_size"], len(records))
        self.assertEqual({record["candidate_id"] for record in records}, SELECTION_IDS)
        self.assertEqual(len(records), len(SELECTION_IDS))
        self.assertTrue(all(record["indecomposable"] for record in records))
        self.assertTrue(all(record["components"] == 1 for record in records))
        self.assertTrue(all(record in ledger for record in records))

    def test_refreshed_parents_match_connected_validated_sources(self) -> None:
        ledger_by_id = {record["candidate_id"]: record for record in campaign.load_records()}
        old_keys = {
            campaign.canonical_key(parent)
            for parent in campaign.VALIDATED_HIGH_DISTANCE_PARENTS
        }
        new_keys: set[str] = set()

        for parent, source_id in zip(
            campaign.ADDITIONAL_HIGH_DISTANCE_PARENTS, SOURCE_KEYS, strict=True
        ):
            source = ledger_by_id[source_id]
            key = campaign.canonical_key(parent)
            new_keys.add(key)

            self.assertEqual(key, SOURCE_KEYS[source_id])
            self.assertEqual(parent["l"], source["l"])
            self.assertEqual(parent["m"], source["m"])
            self.assertEqual([list(term) for term in parent["A"]], source["A"])
            self.assertEqual([list(term) for term in parent["B"]], source["B"])
            self.assertEqual(parent["parent_k"], source["k"])
            self.assertTrue(source["indecomposable"])

            artifact_stem = SOURCE_FINAL_ARTIFACTS[source_id]
            candidate_path = campaign.ARTIFACTS / "candidates" / f"{artifact_stem}.json"
            verdict_path = (
                campaign.ARTIFACTS / "candidates" / f"{artifact_stem}.verdict.json"
            )
            candidate = json.loads(candidate_path.read_text())
            verdict = json.loads(verdict_path.read_text())
            self.assertEqual(
                (candidate["n"], candidate["k"], candidate["distance"]["d"]),
                (source["n"], parent["parent_k"], parent["parent_d"]),
            )
            self.assertTrue(verdict["passed"])
            self.assertTrue(verdict["gates"]["novelty"]["board_advancing"])

            HX, HZ = campaign.build_bb(
                parent["l"], parent["m"], parent["A"], parent["B"]
            )
            self.assertTrue(campaign.verify_css(HX, HZ))
            self.assertEqual(campaign.exact_k(HX, HZ), parent["parent_k"])
            components, sizes = campaign.component_profile(HX, HZ)
            self.assertEqual((components, sizes), (1, [source["n"]]))

        self.assertEqual(len(new_keys), len(campaign.ADDITIONAL_HIGH_DISTANCE_PARENTS))
        self.assertTrue(new_keys.isdisjoint(old_keys))
        self.assertEqual(
            campaign.REFRESHED_HIGH_DISTANCE_PARENTS,
            [
                *campaign.ADDITIONAL_HIGH_DISTANCE_PARENTS,
                *campaign.VALIDATED_HIGH_DISTANCE_PARENTS,
            ],
        )

    def test_refreshed_epoch_parent_and_kernel_cycle(self) -> None:
        kernels = [
            "validated-highd-local-one",
            "validated-highd-local-pair",
            "validated-highd-nearby-geometry",
            "validated-highd-two-step",
            "validated-highd-correlated",
        ]
        parent_count = len(campaign.REFRESHED_HIGH_DISTANCE_PARENTS)

        for offset in range(parent_count * len(kernels)):
            candidate_id = campaign.REFRESHED_HIGH_DISTANCE_START + offset
            proposal = campaign.proposal(candidate_id)
            parent = campaign.REFRESHED_HIGH_DISTANCE_PARENTS[offset % parent_count]

            self.assertEqual(proposal, campaign.proposal(candidate_id))
            self.assertEqual(proposal["candidate_id"], candidate_id)
            self.assertEqual(proposal["parent"], parent["name"])
            self.assertEqual(proposal["parent_d"], parent["parent_d"])
            self.assertEqual(proposal["parent_k"], parent["parent_k"])
            self.assertEqual(proposal["proposal_kernel"], kernels[offset // parent_count])
            self.assertEqual(proposal["lane"], "refreshed-high-distance-mutation")


if __name__ == "__main__":
    unittest.main()
