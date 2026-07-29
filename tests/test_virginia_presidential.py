from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from merge_virginia_presidential import merge_official_rows, parse_official_csv
from virginia_presidential_config import VirginiaElectionSource


class VirginiaPresidentialTests(TestCase):
    def test_parse_official_csv_aggregates_locality_rows(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "va.csv"
            path.write_text(
                "\n".join(
                    [
                        ',,"Kamala D. Harris",Donald J. Trump,Jill E. Stein,Write-Ins,Total Votes Cast',
                        ",,Democratic,Republican,Green,,",
                        "State,Virginia,100,90,5,1,196",
                        "Locality,Bedford County,10,20,1,2,33",
                        "Locality,Alexandria City,30,10,2,1,43",
                        "Precinct,Sample Precinct,999,999,999,999,3996",
                    ]
                ),
                encoding="utf-8",
            )

            rows = parse_official_csv(path)

        self.assertEqual(
            rows,
            {
                ("BEDFORD", "county"): {"DEMOCRAT": 10, "REPUBLICAN": 20, "GREEN": 1, "OTHER": 2},
                ("ALEXANDRIA CITY", "city"): {"DEMOCRAT": 30, "REPUBLICAN": 10, "GREEN": 2, "OTHER": 1},
            },
        )

    def test_merge_official_rows_replaces_county_without_using_retired_bedford_city(self) -> None:
        source = VirginiaElectionSource(
            year=2024,
            contest_url="https://example.test/va-contest",
            download_url="https://example.test/va.csv",
            file_name="va.csv",
        )
        summary = {
            "source": {},
            "counties": [
                {
                    "fips": "51019",
                    "state": "VIRGINIA",
                    "state_po": "VA",
                    "county_name": "BEDFORD",
                    "results": {"2024": {"totalvotes": 1, "supplemental": True}},
                },
                {
                    "fips": "51515",
                    "state": "VIRGINIA",
                    "state_po": "VA",
                    "county_name": "BEDFORD",
                    "results": {},
                },
            ],
        }

        with patch("merge_virginia_presidential.VIRGINIA_PRESIDENTIAL_SOURCES", {2024: source}):
            with patch("merge_virginia_presidential.raw_path", return_value=Path(__file__)):
                with patch(
                    "merge_virginia_presidential.parse_official_csv",
                    return_value={("BEDFORD", "county"): {"DEMOCRAT": 10, "REPUBLICAN": 26}},
                ):
                    stats = merge_official_rows(summary)

        county_result = summary["counties"][0]["results"]["2024"]
        city_result = summary["counties"][1]["results"]
        self.assertEqual(stats["replaced"], 1)
        self.assertEqual(stats["missing_localities"], 1)
        self.assertTrue(county_result["official"])
        self.assertNotIn("supplemental", county_result)
        self.assertEqual(county_result["source_name"], "Virginia Department of Elections")
        self.assertEqual(county_result["source_url"], "https://example.test/va-contest")
        self.assertEqual(city_result, {})
        self.assertEqual(summary["source"]["official_state_sources"][0]["state_po"], "VA")
