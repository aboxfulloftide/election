from __future__ import annotations

import json
from pathlib import Path
from unittest import TestCase

ROOT_DIR = Path(__file__).resolve().parents[1]


class FloridaPrecinctDrilldownTests(TestCase):
    def test_miami_dade_bundles_reference_the_matching_geometry_vintage(self) -> None:
        expected_join_stats = {
            2012: (589, 499, 90),
            2014: (568, 454, 114),
        }
        for year, contest_count in ((2012, 22), (2014, 18)):
            bundle = json.loads((ROOT_DIR / f"public/results/precincts/florida-miami-dade-{year}-precincts.json").read_text())

            self.assertEqual(bundle["county"], {"fips": "12086", "name": "Miami-Dade County"})
            self.assertEqual(bundle["geometry"]["vintage"], str(year))
            self.assertEqual(
                tuple(bundle["geometry"][key] for key in ("result_precinct_count", "matched_result_precinct_count", "unmatched_result_precinct_count")),
                expected_join_stats[year],
            )
            self.assertEqual(len(bundle["contests"]), contest_count)
            for contest in bundle["contests"]:
                self.assertTrue(contest["precincts"])
                self.assertEqual(len(contest["precincts"]), len({row["precinct_id"] for row in contest["precincts"]}))

    def test_miami_dade_precinct_candidates_have_reconciled_totals(self) -> None:
        bundle = json.loads((ROOT_DIR / "public/results/precincts/florida-miami-dade-2014-precincts.json").read_text())

        for contest in bundle["contests"]:
            for precinct in contest["precincts"]:
                self.assertEqual(precinct["total_votes"], sum(candidate["votes"] for candidate in precinct["candidates"]))
                self.assertIsNotNone(precinct["winner"])

    def test_broward_2020_result_join_is_complete(self) -> None:
        bundle = json.loads((ROOT_DIR / "public/results/precincts/florida-broward-2020-precincts.json").read_text())

        self.assertEqual(bundle["county"], {"fips": "12011", "name": "Broward County"})
        self.assertEqual(len(bundle["contests"]), 13)
        self.assertEqual(bundle["geometry"]["vintage"], "2020")
        self.assertEqual(bundle["geometry"]["result_precinct_count"], 577)
        self.assertEqual(bundle["geometry"]["matched_result_precinct_count"], 577)
        self.assertEqual(bundle["geometry"]["unmatched_result_precinct_count"], 0)

    def test_broward_2022_bundle_preserves_namespace_mismatch(self) -> None:
        bundle = json.loads((ROOT_DIR / "public/results/precincts/florida-broward-2022-precincts.json").read_text())

        self.assertEqual(bundle["county"]["fips"], "12011")
        self.assertEqual(bundle["geometry"]["result_precinct_count"], 355)
        self.assertEqual(bundle["geometry"]["matched_result_precinct_count"], 0)
        self.assertEqual(bundle["geometry"]["unmatched_result_precinct_count"], 355)

    def test_broward_2024_result_join_is_complete(self) -> None:
        bundle = json.loads((ROOT_DIR / "public/results/precincts/florida-broward-2024-precincts.json").read_text())

        self.assertEqual(bundle["county"]["fips"], "12011")
        self.assertEqual(len(bundle["contests"]), 11)
        self.assertEqual(bundle["geometry"]["result_precinct_count"], 358)
        self.assertEqual(bundle["geometry"]["matched_result_precinct_count"], 358)
        self.assertEqual(bundle["geometry"]["unmatched_result_precinct_count"], 0)
