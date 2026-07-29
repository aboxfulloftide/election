from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from compare_county_presidential_official_sources import compare_by_county_name


class CountyPresidentialOfficialComparisonTests(TestCase):
    def test_compare_by_county_name_flags_party_mismatch(self) -> None:
        summary = {
            "counties": [
                {
                    "state_po": "KY",
                    "county_name": "ADAIR",
                    "results": {
                        "2020": {
                            "official": True,
                            "source_name": "Kentucky State Board of Elections",
                            "parties": {"REPUBLICAN": 1, "DEMOCRAT": 2},
                        }
                    },
                }
            ]
        }

        failures = compare_by_county_name(
            summary,
            state_po="KY",
            year=2020,
            source_name="Kentucky State Board of Elections",
            official_rows={"ADAIR": {"REPUBLICAN": 1, "DEMOCRAT": 3}},
        )

        self.assertEqual(len(failures), 1)
        self.assertIn("party votes do not match", failures[0])
