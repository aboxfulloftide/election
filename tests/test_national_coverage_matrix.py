from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]


class NationalCoverageMatrixTests(TestCase):
    def test_matrix_covers_all_states_cycles_and_active_offices(self) -> None:
        matrix = json.loads((ROOT_DIR / "public/results/national-coverage-matrix.json").read_text())

        self.assertEqual(len(matrix["cells"]), 4200)
        self.assertEqual(len({cell["state_po"] for cell in matrix["cells"]}), 50)
        self.assertEqual(len({cell["year"] for cell in matrix["cells"]}), 14)
        self.assertEqual(len({cell["office"] for cell in matrix["cells"]}), 6)
        self.assertNotIn("Mayor", {cell["office"] for cell in matrix["cells"]})
        self.assertEqual(Counter(cell["status"] for cell in matrix["cells"])["not_yet_available"], 296)

    def test_first_cohort_tracks_ten_states_and_six_offices(self) -> None:
        cohort = json.loads(
            (ROOT_DIR / "data/national-cohorts/cohort-01-2020-2024.json").read_text()
        )

        self.assertEqual(cohort["years"], [2020, 2022, 2024])
        self.assertEqual(len(cohort["states"]), 10)
        self.assertEqual(len(cohort["offices"]), 6)
        self.assertEqual(
            {state["status"] for state in cohort["states"]},
            {"imported", "source_identified"},
        )

    def test_first_cohort_preflight_has_one_row_per_state_year(self) -> None:
        preflight = json.loads(
            (ROOT_DIR / "public/results/national-cohort-01-preflight.json").read_text()
        )

        self.assertEqual(preflight["summary"]["state_year_batches"], 30)
        self.assertEqual(len(preflight["rows"]), 30)
        self.assertTrue(all(row["status"] in {"files_present", "needs_source"} for row in preflight["rows"]))

    def test_remaining_modern_and_legacy_inventories_cover_the_unprocessed_states(self) -> None:
        modern = json.loads((ROOT_DIR / "data/national-cohorts/modern-remaining-2020-2024.json").read_text())
        legacy = json.loads((ROOT_DIR / "data/national-cohorts/legacy-2010-2018.json").read_text())
        modern_states = [state for cohort in modern["cohorts"] for state in cohort["states"]]
        self.assertEqual(len(modern_states), 40)
        self.assertEqual(len(set(modern_states)), 40)
        self.assertEqual(set(modern["offices"]), set(legacy["offices"]))
        self.assertEqual(len(legacy["states"]), 50)

    def test_north_carolina_summary_contains_only_active_offices(self) -> None:
        summary = json.loads(
            (ROOT_DIR / "public/results/north-carolina-statewide-summary.json").read_text()
        )
        offices = {contest["office"] for election in summary["elections"] for contest in election["contests"]}
        self.assertEqual(
            offices,
            {"President", "U.S. Senate", "U.S. House", "Governor", "State Senate", "State House"},
        )
        self.assertEqual([len(election["contests"]) for election in summary["elections"]], [186, 185, 186])

    def test_modern_cohort_inventory_keeps_official_source_lanes_explicit(self) -> None:
        registry = json.loads((ROOT_DIR / "data/source-registry/georgia.json").read_text())
        imported = next(entry for entry in registry["entries"] if entry["id"] == "ga-sos-federal-state-2022-imported")
        self.assertEqual(imported["years"], [2022])
        self.assertIn("State House", imported["offices"])
        summary = json.loads((ROOT_DIR / "public/results/georgia-2022-official-contests.json").read_text())
        contests = summary["elections"][0]["contests"]
        self.assertEqual(len(contests), 252)
        self.assertEqual({contest["office"] for contest in contests}, {"U.S. Senate", "U.S. House", "Governor", "State Senate", "State House"})
        for contest in contests:
            self.assertEqual(sum(candidate["votes"] for candidate in contest["candidates"]), contest["total_votes"])
            self.assertEqual(contest["winner"]["votes"], max(candidate["votes"] for candidate in contest["candidates"]))

    def test_georgia_2024_official_pdf_artifact_has_expected_district_lanes(self) -> None:
        summary = json.loads((ROOT_DIR / "public/results/georgia-2024-official-contests.json").read_text())
        contests = summary["elections"][0]["contests"]
        counts = {}
        for contest in contests:
            counts[contest["office"]] = counts.get(contest["office"], 0) + 1
            self.assertEqual(sum(candidate["votes"] for candidate in contest["candidates"]), contest["total_votes"])
            self.assertEqual(contest["winner"]["votes"], max(candidate["votes"] for candidate in contest["candidates"]))
        self.assertEqual(counts, {"President": 1, "U.S. House": 14, "State Senate": 56, "State House": 180})

    def test_virginia_even_year_state_legislative_lanes_are_not_on_ballot(self) -> None:
        registry = json.loads((ROOT_DIR / "data/source-registry/virginia.json").read_text())
        entry = next(item for item in registry["entries"] if item["offices"] == ["Governor", "State Senate", "State House"])
        self.assertTrue(entry["not_on_even_year_ballot"])

    def test_kentucky_candidate_readiness_keeps_uncertain_lanes_out_of_public_contests(self) -> None:
        report = json.loads((ROOT_DIR / "public/results/kentucky-2022-state-candidate-readiness.json").read_text())
        self.assertEqual(report["offices"]["State Senate"]["expected_districts"], 19)
        self.assertEqual(report["offices"]["State House"]["expected_districts"], 100)
        self.assertGreater(report["offices"]["State Senate"]["header_extraction_needed"], 0)
        self.assertGreater(report["offices"]["State House"]["header_extraction_needed"], 0)

    def test_georgia_2020_full_archive_preserves_two_senate_contests(self) -> None:
        summary = json.loads((ROOT_DIR / "public/results/georgia-2020-official-contests.json").read_text())
        contests = summary["elections"][0]["contests"]
        self.assertEqual(len(contests), 253)
        senate = [contest for contest in contests if contest["office"] == "U.S. Senate"]
        self.assertEqual({contest["name"] for contest in senate}, {"Georgia 2020 Regular", "Georgia 2020 Special"})
        for contest in contests:
            self.assertEqual(sum(candidate["votes"] for candidate in contest["candidates"]), contest["total_votes"])
