from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from generate_county_presidential_coverage import build_coverage


class CountyPresidentialCoverageTests(TestCase):
    def test_build_coverage_tracks_missing_counties_by_state(self) -> None:
        summary = {
            "source": {"name": "Test source"},
            "years": [2020, 2024],
            "counties": [
                {"fips": "01001", "state": "Alabama", "state_po": "AL", "county_name": "Autauga", "results": {"2020": {}, "2024": {}}},
                {"fips": "01003", "state": "Alabama", "state_po": "AL", "county_name": "Baldwin", "results": {"2024": {}}},
                {"fips": "02001", "state": "Alaska", "state_po": "AK", "county_name": "District 1", "results": {"2020": {}}},
            ],
        }

        coverage = build_coverage(summary)
        reports = {report["year"]: report for report in coverage["years"]}

        self.assertEqual(reports[2020]["counties_with_results"], 2)
        self.assertEqual(reports[2020]["missing_counties"], 1)
        self.assertEqual(reports[2020]["states_complete"], 1)
        self.assertEqual(reports[2020]["missing_by_state"][0]["state_po"], "AL")
        self.assertEqual(reports[2020]["missing_by_state"][0]["missing_counties"], 1)

        self.assertEqual(reports[2024]["counties_with_results"], 2)
        self.assertEqual(reports[2024]["missing_by_state"][0]["state_po"], "AK")

    def test_build_coverage_excludes_inactive_historical_rows_from_later_years(self) -> None:
        summary = {
            "source": {"name": "Test source"},
            "years": [2012, 2020],
            "counties": [
                {"fips": "51019", "state": "Virginia", "state_po": "VA", "county_name": "Bedford", "results": {"2012": {}, "2020": {}}},
                {
                    "fips": "51515",
                    "state": "Virginia",
                    "state_po": "VA",
                    "county_name": "Bedford City",
                    "valid_to_year": 2012,
                    "results": {"2012": {}},
                },
            ],
        }

        coverage = build_coverage(summary)
        reports = {report["year"]: report for report in coverage["years"]}

        self.assertEqual(reports[2012]["county_count"], 2)
        self.assertEqual(reports[2012]["counties_with_results"], 2)
        self.assertEqual(reports[2020]["county_count"], 1)
        self.assertEqual(reports[2020]["counties_with_results"], 1)
        self.assertEqual(reports[2020]["missing_counties"], 0)
