from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from normalize_county_presidential_geographies import normalize_summary


class CountyPresidentialGeographyNormalizationTests(TestCase):
    def test_normalize_summary_merges_known_alias_rows_and_marks_bedford_inactive(self) -> None:
        summary = {
            "counties": [
                {"fips": "2938000", "state_po": "MO", "county_name": "KANSAS CITY", "results": {"2020": {"totalvotes": 10}}},
                {"fips": "36000", "state_po": "MO", "county_name": "KANSAS CITY", "results": {"2024": {"totalvotes": 12}}},
                {"fips": "46102", "state_po": "SD", "county_name": "OGLALA LAKOTA", "results": {"2020": {"totalvotes": 20}}},
                {"fips": "46113", "state_po": "SD", "county_name": "SHANNON", "results": {"2012": {"totalvotes": 18}}},
                {"fips": "51515", "state_po": "VA", "county_name": "BEDFORD", "results": {"2012": {"totalvotes": 5}}},
            ]
        }

        stats = normalize_summary(summary)
        by_fips = {county["fips"]: county for county in summary["counties"]}

        self.assertEqual(stats, {"merged": 2, "marked_inactive": 1})
        self.assertNotIn("36000", by_fips)
        self.assertNotIn("46113", by_fips)
        self.assertEqual(by_fips["2938000"]["results"]["2024"]["totalvotes"], 12)
        self.assertEqual(by_fips["2938000"]["fips_aliases"], ["36000"])
        self.assertEqual(by_fips["46102"]["results"]["2012"]["totalvotes"], 18)
        self.assertEqual(by_fips["46102"]["previous_names"], ["SHANNON"])
        self.assertEqual(by_fips["51515"]["valid_to_year"], 2012)
