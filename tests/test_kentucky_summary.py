from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from generate_kentucky_statewide_summary import office_for_heading
from check_kentucky_summary import validate_summary


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

    def test_source_file_counts_reflect_each_contest_scope(self) -> None:
        summary = json.loads(
            (ROOT_DIR / "public/results/kentucky-statewide-summary.json").read_text()
        )
        contests = {
            (contest["year"], contest["office"], contest.get("district_number")): contest
            for election in summary["elections"]
            for contest in election["contests"]
        }
        self.assertEqual(contests[(2022, "U.S. Senate", None)]["source_files"], 49)
        self.assertEqual(contests[(2024, "President", None)]["source_files"], 119)
        self.assertLess(contests[(2022, "U.S. House", 1)]["source_files"], 118)
        self.assertEqual(validate_summary(summary), [])

    def test_certified_house_override_is_complete_and_official(self) -> None:
        summary = json.loads(
            (ROOT_DIR / "public/results/kentucky-statewide-summary.json").read_text()
        )
        contests = {
            contest.get("district_number"): contest
            for election in summary["elections"]
            if election["election"]["year"] == 2022
            for contest in election["contests"]
            if contest["office"] == "U.S. House"
        }
        self.assertEqual(set(contests), {1, 2, 3, 4, 5, 6})
        self.assertTrue(all(contest["official"] for contest in contests.values()))
        self.assertTrue(all(contest["source_format"] == "ky-certified-pdf-ocr" for contest in contests.values()))
        self.assertEqual(contests[6]["total_votes"], 246818)
