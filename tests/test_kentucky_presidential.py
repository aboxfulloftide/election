from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from kentucky_presidential_config import KentuckyElectionSource
from merge_kentucky_presidential import line_county_votes, merge_official_rows, parse_official_pdf


class KentuckyPresidentialTests(TestCase):
    def test_line_county_votes_handles_multi_word_counties(self) -> None:
        parsed = line_county_votes("McCracken 1,234 2,345 30 4 5 6 7 8 9 10 11 12 13 14 15 16", {"MCCRACKEN"})
        self.assertEqual(parsed, ("MCCRACKEN", [1234, 2345, 30, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]))

    def test_parse_official_pdf_uses_first_presidential_county_rows(self) -> None:
        text = "\n".join(
            [
                "Adair 7,276 1,392 60 25 10 5 0 0 0 0 0 0 0 0 0 0",
                "Adair 6,753 1,623 348 0 0 0 0 0",
                "McCracken 22 33 4 1 1 1 1 1 1 1 1 1 1 1 1 1",
            ]
        )
        with patch("merge_kentucky_presidential.pdf_text", return_value=text):
            rows = parse_official_pdf(Path("unused.pdf"), {"ADAIR", "MCCRACKEN"})

        self.assertEqual(rows["ADAIR"], {"REPUBLICAN": 7276, "DEMOCRAT": 1392, "LIBERTARIAN": 60, "OTHER": 40})
        self.assertEqual(rows["MCCRACKEN"], {"REPUBLICAN": 22, "DEMOCRAT": 33, "LIBERTARIAN": 4, "OTHER": 13})

    def test_merge_official_rows_replaces_existing_supplemental_result(self) -> None:
        source = KentuckyElectionSource(year=2020, url="https://example.test/ky.pdf", file_name="ky.pdf")
        summary = {
            "source": {},
            "counties": [
                {
                    "fips": "21001",
                    "state": "KENTUCKY",
                    "state_po": "KY",
                    "county_name": "ADAIR",
                    "results": {"2020": {"totalvotes": 1, "supplemental": True}},
                }
            ],
        }

        with patch("merge_kentucky_presidential.KENTUCKY_PRESIDENTIAL_SOURCES", {2020: source}):
            with patch("merge_kentucky_presidential.raw_path", return_value=Path(__file__)):
                with patch("merge_kentucky_presidential.parse_official_pdf", return_value={"ADAIR": {"DEMOCRAT": 10, "REPUBLICAN": 26}}):
                    stats = merge_official_rows(summary)

        result = summary["counties"][0]["results"]["2020"]
        self.assertEqual(stats["replaced"], 1)
        self.assertTrue(result["official"])
        self.assertNotIn("supplemental", result)
        self.assertEqual(result["source_name"], "Kentucky State Board of Elections")
        self.assertEqual(result["quality_grade"], "B")
        self.assertEqual(summary["source"]["official_state_sources"][0]["state_po"], "KY")
