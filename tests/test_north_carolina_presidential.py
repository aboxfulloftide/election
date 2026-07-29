from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from merge_north_carolina_presidential import merge_official_rows, parse_official_zip
from north_carolina_presidential_config import NorthCarolinaElectionSource


class NorthCarolinaPresidentialTests(TestCase):
    def test_parse_official_zip_aggregates_presidential_rows(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "results.zip"
            content = "\n".join(
                [
                    "County\tElection Date\tPrecinct\tContest Group ID\tContest Type\tContest Name\tChoice\tChoice Party\tVote For\tElection Day\tEarly Voting\tAbsentee by Mail\tProvisional\tTotal Votes\tReal Precinct\t",
                    "WAKE\t11/05/2024\t01\t1\tS\tUS PRESIDENT\tKamala D. Harris\tDEM\t1\t1\t2\t3\t4\t10\tY\t",
                    "WAKE\t11/05/2024\t02\t1\tS\tUS PRESIDENT\tDonald J. Trump\tREP\t1\t5\t6\t7\t8\t26\tY\t",
                    "WAKE\t11/05/2024\t03\t1\tS\tUS PRESIDENT\tWrite-In (Miscellaneous)\t\t1\t1\t0\t0\t0\t1\tY\t",
                    "WAKE\t11/05/2024\t04\t2\tS\tNC GOVERNOR\tSomeone\tDEM\t1\t99\t0\t0\t0\t99\tY\t",
                ]
            )
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("results.txt", content)

            rows = parse_official_zip(path)

        self.assertEqual(rows, {"WAKE": {"DEMOCRAT": 10, "REPUBLICAN": 26, "OTHER": 1}})

    def test_merge_official_rows_replaces_existing_supplemental_result(self) -> None:
        source = NorthCarolinaElectionSource(
            year=2024,
            election_date="11/05/2024",
            url="https://example.test/nc.zip",
            file_name="nc.zip",
        )
        summary = {
            "source": {},
            "counties": [
                {
                    "fips": "37183",
                    "state": "NORTH CAROLINA",
                    "state_po": "NC",
                    "county_name": "WAKE",
                    "results": {"2024": {"totalvotes": 1, "supplemental": True}},
                }
            ],
        }

        with patch("merge_north_carolina_presidential.NORTH_CAROLINA_PRESIDENTIAL_SOURCES", {2024: source}):
            with patch("merge_north_carolina_presidential.raw_path", return_value=Path(__file__)):
                with patch("merge_north_carolina_presidential.parse_official_zip", return_value={"WAKE": {"DEMOCRAT": 10, "REPUBLICAN": 26}}):
                    stats = merge_official_rows(summary)

        result = summary["counties"][0]["results"]["2024"]
        self.assertEqual(stats["replaced"], 1)
        self.assertTrue(result["official"])
        self.assertNotIn("supplemental", result)
        self.assertEqual(result["source_name"], "North Carolina State Board of Elections")
        self.assertEqual(result["quality_grade"], "A")
        self.assertEqual(summary["source"]["official_state_sources"][0]["state_po"], "NC")
