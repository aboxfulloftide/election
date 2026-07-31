from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from generate_kentucky_statewide_summary import office_for_heading


class KentuckySummaryTests(TestCase):
    def test_office_headings_support_kentucky_pdf_case_and_district_labels(self) -> None:
        self.assertEqual(
            office_for_heading("UNITED STATES REPRESENTATIVE in CONGRESS 1st Congressional District - (Vote for One)"),
            ("U.S. House", 1, "1 Congressional District"),
        )
        self.assertEqual(
            office_for_heading("STATE SENATOR 16th Senatorial District - (Vote for One)"),
            ("State Senate", 16, "16 State Senate District"),
        )

    def test_generated_summary_excludes_straight_party_and_local_contests(self) -> None:
        summary = json.loads(
            (ROOT_DIR / "public/results/kentucky-statewide-summary.json").read_text()
        )
        active_offices = {
            contest["office"]
            for election in summary["elections"]
            for contest in election["contests"]
        }
        self.assertTrue(
            active_offices <= {"President", "U.S. Senate", "U.S. House", "State Senate", "State House"}
        )
        candidates = [
            candidate["candidate"]
            for election in summary["elections"]
            for contest in election["contests"]
            for candidate in contest["candidates"]
        ]
        self.assertNotIn("Republican Party", candidates)
        self.assertNotIn("Democratic Party", candidates)
        self.assertEqual(summary["source"]["completeness"], "partial")
