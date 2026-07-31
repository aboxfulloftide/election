from __future__ import annotations

import json
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]


class LegacyStructuredSummaryTests(TestCase):
    def assert_contests_reconcile(self, summary: dict) -> None:
        contests = [contest for election in summary["elections"] for contest in election["contests"]]
        self.assertTrue(contests)
        for contest in contests:
            votes = [candidate["votes"] for candidate in contest["candidates"]]
            self.assertEqual(sum(votes), contest["total_votes"], contest["name"])
            self.assertEqual(contest["winner"]["votes"], max(votes), contest["name"])
            self.assertEqual(
                contest["margin_votes"],
                sorted(votes, reverse=True)[0] - (sorted(votes, reverse=True)[1] if len(votes) > 1 else sorted(votes, reverse=True)[0]),
                contest["name"],
            )

    def test_idaho_summary_has_only_supported_federal_and_governor_lanes(self) -> None:
        summary = json.loads((ROOT_DIR / "public/results/idaho-legacy-2014-2018-summary.json").read_text())
        self.assertEqual([len(election["contests"]) for election in summary["elections"]], [4, 4, 3])
        self.assert_contests_reconcile(summary)
        self.assertEqual(
            {contest["office"] for election in summary["elections"] for contest in election["contests"]},
            {"President", "U.S. Senate", "U.S. House", "Governor"},
        )
        self.assertEqual(
            [contest["total_votes"] for contest in summary["elections"][2]["contests"] if contest["office"] == "Governor"],
            [605131],
        )

    def test_delaware_summary_has_all_2018_target_district_lanes(self) -> None:
        summary = json.loads((ROOT_DIR / "public/results/delaware-legacy-2018-summary.json").read_text())
        contests = summary["elections"][0]["contests"]
        self.assertEqual(len(contests), 53)
        self.assertEqual(sum(contest["office"] == "State Senate" for contest in contests), 10)
        self.assertEqual(sum(contest["office"] == "State House" for contest in contests), 41)
        self.assert_contests_reconcile(summary)

    def test_illinois_summary_preserves_partial_district_scope(self) -> None:
        summary = json.loads((ROOT_DIR / "public/results/illinois-legacy-2018-summary.json").read_text())
        contest = summary["elections"][0]["contests"][0]
        self.assertEqual(contest["office"], "U.S. House")
        self.assertEqual(contest["district_number"], 2)
        self.assertEqual(contest["candidates"][0]["party"], "DEMOCRAT")
        self.assert_contests_reconcile(summary)
