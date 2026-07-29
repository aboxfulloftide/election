from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from merge_county_presidential_supplement import merge_supplement


class CountyPresidentialSupplementTests(TestCase):
    def test_merge_fills_only_missing_rows(self) -> None:
        summary = {
            "source": {"name": "MIT Election Data and Science Lab"},
            "counties": [
                {"fips": "01001", "state": "ALABAMA", "state_po": "AL", "county_name": "AUTAUGA", "results": {}},
                {
                    "fips": "01003",
                    "state": "ALABAMA",
                    "state_po": "AL",
                    "county_name": "BALDWIN",
                    "results": {"2024": {"totalvotes": 1, "parties": {"OTHER": 1}}},
                },
            ],
        }

        rows = {
            "01001": {"votes_dem": "7", "votes_gop": "11", "total_votes": "20"},
            "01003": {"votes_dem": "100", "votes_gop": "200", "total_votes": "300"},
        }

        with patch("merge_county_presidential_supplement.YEARS", (2024,)):
            with patch("merge_county_presidential_supplement.raw_path", return_value=Path(__file__)):
                with patch("merge_county_presidential_supplement.read_supplement_rows", return_value=rows):
                    stats = merge_supplement(summary)

        self.assertEqual(stats["inserted"], 1)
        inserted = summary["counties"][0]["results"]["2024"]
        self.assertTrue(inserted["supplemental"])
        self.assertEqual(inserted["parties"], {"DEMOCRAT": 7, "REPUBLICAN": 11, "OTHER": 2})
        self.assertEqual(inserted["winner_party"], "REPUBLICAN")
        self.assertEqual(summary["counties"][1]["results"]["2024"]["totalvotes"], 1)
        self.assertEqual(summary["source"]["supplements"][0]["quality_grade"], "D")
