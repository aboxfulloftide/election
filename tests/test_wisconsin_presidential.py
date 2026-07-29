from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from merge_wisconsin_presidential import line_county_votes, parse_official_pdf


class WisconsinPresidentialTests(TestCase):
    def test_line_county_votes_handles_punctuation_counties(self) -> None:
        parsed = line_county_votes("ST. CROIX 60,642 23,870 35,537 93 286 195", {"ST. CROIX"})
        self.assertEqual(parsed, ("ST. CROIX", [60642, 23870, 35537, 93, 286, 195]))

    def test_parse_official_pdf_maps_major_parties_and_other_from_total(self) -> None:
        text = "DANE 365,929 273,995 85,454 297 1,209 1,721"
        with patch("merge_wisconsin_presidential.pdf_text", return_value=text):
            rows = parse_official_pdf(Path("unused.pdf"), {"DANE"})

        self.assertEqual(
            rows["DANE"],
            {"DEMOCRAT": 273995, "REPUBLICAN": 85454, "LIBERTARIAN": 1209, "GREEN": 1721, "OTHER": 3550},
        )
