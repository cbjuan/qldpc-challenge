#!/usr/bin/env python3
"""Structural regression tests for the local periodic-BB campaign."""

from __future__ import annotations

import hashlib
import json
import unittest

import campaign


OLD_PROPOSAL_END = 51_663
OLD_PROPOSAL_DIGEST = "dc5a3eef67f8a668ba8f096cc06ec00904512b9ed29f4cdbb8cb4b73d44144c0"
REFRESHED_PROPOSAL_END = 57_663
REFRESHED_PROPOSAL_DIGEST = "84e1dc1c7a4ba06adad539fd75cac1fabc9394b848bc3e1e808dc0ea06efce11"
EPOCH5_FIRST_CYCLE_DIGEST = "9a445a7870d4ed759299427459603762c2ffbf1b25978f72076b735fd68a567d"
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
EPOCH5_SOURCE_IDS = (50_584, 54_828, 56_213, 57_634, 56_884, 52_988)
EPOCH5_SOURCE_KEYS = {
    50_584: "6319d85735ce46aa7d307896",
    54_828: "09ff68dae866969e4e8ac704",
    56_213: "d2e5e445f5073e9e2650558f",
    57_634: "4a0a53c8649a293d7b857c61",
    56_884: "add1f28e9473301022dda49a",
    52_988: "c5f0902d470bca9c8ecc1151",
}
EPOCH5_SOURCE_SELECTIONS = {
    50_584: "selection-validated-highd-epoch2-002.json",
    54_828: "selection-refreshed-highd-epoch4-001.json",
    56_213: "selection-refreshed-highd-epoch4-001.json",
    57_634: "selection-refreshed-highd-reserve-epoch4-001.json",
    56_884: "selection-refreshed-highd-epoch4-001.json",
    52_988: "selection-refreshed-highd-epoch3-001.json",
}
EPOCH5_SOURCE_FINAL_ARTIFACTS = {
    50_584: "c0050584-6319d85735-validated-highd-epoch2-nonroot-final-allrungs-s1192805705",
    54_828: "c0054828-09ff68dae8-epoch4-c54828-final-allrungs-s1270196823",
    56_213: "c0056213-d2e5e445f5-epoch4-c56213-final-allrungs-s596989082",
    57_634: "c0057634-4a0a53c864-epoch4-reserve-final-allrungs-s2014784105",
    56_884: "c0056884-add1f28e94-epoch4-c56884-final-allrungs-s255505412",
    52_988: "c0052988-c5f0902d47-epoch3-final-allrungs-s2067371932",
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

    def test_refreshed_candidate_ids_are_immutable(self) -> None:
        self.assertEqual(
            campaign.REFRESHED_HIGH_DISTANCE_EPOCH5_START,
            REFRESHED_PROPOSAL_END,
        )
        self.assertEqual(
            proposal_digest(
                campaign.REFRESHED_HIGH_DISTANCE_START,
                REFRESHED_PROPOSAL_END,
            ),
            REFRESHED_PROPOSAL_DIGEST,
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

    def test_epoch5_parents_match_connected_validated_sources(self) -> None:
        ledger_by_id = {record["candidate_id"]: record for record in campaign.load_records()}
        old_keys = {
            campaign.canonical_key(parent)
            for parent in campaign.REFRESHED_HIGH_DISTANCE_PARENTS
        }
        new_keys: set[str] = set()

        self.assertEqual(
            len(campaign.EPOCH5_ADDITIONAL_HIGH_DISTANCE_PARENTS),
            len(EPOCH5_SOURCE_IDS),
        )
        for parent, source_id in zip(
            campaign.EPOCH5_ADDITIONAL_HIGH_DISTANCE_PARENTS,
            EPOCH5_SOURCE_IDS,
            strict=True,
        ):
            source = ledger_by_id[source_id]
            selection_path = campaign.ARTIFACTS / EPOCH5_SOURCE_SELECTIONS[source_id]
            selection = json.loads(selection_path.read_text())
            selected = [
                record for record in selection["records"]
                if record["candidate_id"] == source_id
            ]

            self.assertEqual(selected, [source])
            self.assertTrue(source["indecomposable"])
            self.assertEqual(
                (source["components"], source["component_sizes"]),
                (1, [source["n"]]),
            )

            key = campaign.canonical_key(parent)
            new_keys.add(key)
            self.assertEqual(key, EPOCH5_SOURCE_KEYS[source_id])
            self.assertEqual(parent["l"], source["l"])
            self.assertEqual(parent["m"], source["m"])
            self.assertEqual([list(term) for term in parent["A"]], source["A"])
            self.assertEqual([list(term) for term in parent["B"]], source["B"])
            self.assertEqual(parent["parent_k"], source["k"])

            artifact_stem = EPOCH5_SOURCE_FINAL_ARTIFACTS[source_id]
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

        self.assertEqual(len(new_keys), len(EPOCH5_SOURCE_IDS))
        self.assertTrue(new_keys.isdisjoint(old_keys))
        self.assertEqual(
            [parent["name"] for parent in campaign.EPOCH5_DIVERSITY_PARENTS],
            list(campaign.EPOCH5_DIVERSITY_PARENT_NAMES),
        )
        self.assertTrue(
            all(
                parent in campaign.REFRESHED_HIGH_DISTANCE_PARENTS
                for parent in campaign.EPOCH5_DIVERSITY_PARENTS
            )
        )
        self.assertEqual(
            campaign.EPOCH5_HIGH_DISTANCE_PARENTS,
            [
                *campaign.EPOCH5_ADDITIONAL_HIGH_DISTANCE_PARENTS,
                *campaign.EPOCH5_DIVERSITY_PARENTS,
            ],
        )
        epoch5_names = {
            parent["name"] for parent in campaign.EPOCH5_HIGH_DISTANCE_PARENTS
        }
        self.assertEqual(len(campaign.EPOCH5_HIGH_DISTANCE_PARENTS), 11)
        self.assertIn("validated-c50584-630-8-34", epoch5_names)
        self.assertNotIn("validated-c45118-630-8-30", epoch5_names)
        self.assertIn("validated-c52988-576-16-20", epoch5_names)
        self.assertIn("validated-c45107-576-24-12", epoch5_names)

    def test_epoch5_proposals_are_deterministic_valid_bb_specs(self) -> None:
        kernels = [
            "validated-highd-local-one",
            "validated-highd-local-pair",
            "validated-highd-nearby-geometry",
            "validated-highd-two-step",
            "validated-highd-correlated",
        ]
        parents = campaign.EPOCH5_HIGH_DISTANCE_PARENTS
        parent_count = len(parents)
        cycle_stop = (
            campaign.REFRESHED_HIGH_DISTANCE_EPOCH5_START
            + parent_count * len(kernels)
        )
        self.assertEqual(
            proposal_digest(
                campaign.REFRESHED_HIGH_DISTANCE_EPOCH5_START,
                cycle_stop,
            ),
            EPOCH5_FIRST_CYCLE_DIGEST,
        )

        for offset in range(parent_count * len(kernels)):
            candidate_id = campaign.REFRESHED_HIGH_DISTANCE_EPOCH5_START + offset
            proposal = campaign.proposal(candidate_id)
            parent = parents[offset % parent_count]

            self.assertEqual(proposal, campaign.proposal(candidate_id))
            self.assertEqual(proposal["candidate_id"], candidate_id)
            self.assertEqual(proposal["parent"], parent["name"])
            self.assertEqual(proposal["parent_d"], parent["parent_d"])
            self.assertEqual(proposal["parent_k"], parent["parent_k"])
            self.assertEqual(proposal["proposal_kernel"], kernels[offset // parent_count])
            self.assertEqual(proposal["lane"], "refreshed-high-distance-mutation")
            self.assertLessEqual(2 * proposal["l"] * proposal["m"], 700)
            self.assertEqual(
                proposal["A"],
                [list(term) for term in campaign.normalize_support(
                    proposal["A"], proposal["l"], proposal["m"]
                )],
            )
            self.assertEqual(
                proposal["B"],
                [list(term) for term in campaign.normalize_support(
                    proposal["B"], proposal["l"], proposal["m"]
                )],
            )

            HX, HZ = campaign.build_bb(
                proposal["l"], proposal["m"], proposal["A"], proposal["B"]
            )
            self.assertEqual(HX.shape, HZ.shape)
            self.assertEqual(
                HX.shape,
                (
                    proposal["l"] * proposal["m"],
                    2 * proposal["l"] * proposal["m"],
                ),
            )
            self.assertTrue(campaign.verify_css(HX, HZ))


if __name__ == "__main__":
    unittest.main()
