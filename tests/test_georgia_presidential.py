from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from georgia_presidential_config import GeorgiaElectionSource
from merge_georgia_presidential import merge_official_rows, parse_official_zip


class GeorgiaPresidentialTests(TestCase):
    def test_parse_official_zip_reads_nested_county_summary_csvs(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "ga.zip"
            nested = io.BytesIO()
            with zipfile.ZipFile(nested, "w") as inner:
                inner.writestr(
                    "summary.csv",
                    "\n".join(
                        [
                            '"line number","contest name","choice name","party name","total votes"',
                            '1,"President of the United States (Vote For 1)","Donald J. Trump (I) (Rep)","NP",20',
                            '2,"President of the United States (Vote For 1)","Joseph R. Biden (Dem)","NP",10',
                            '3,"President of the United States (Vote For 1)","Jo Jorgensen (Lib)","NP",2',
                            '4,"Public Service Commissioner","Someone (Rep)","NP",999',
                        ]
                    ),
                )
            with zipfile.ZipFile(path, "w") as outer:
                outer.writestr("Election/summary/Ben_Hill_107241_272759-summary.zip", nested.getvalue())

            rows = parse_official_zip(path)

        self.assertEqual(rows, {"BEN HILL": {"REPUBLICAN": 20, "DEMOCRAT": 10, "LIBERTARIAN": 2}})

    def test_merge_official_rows_replaces_existing_supplemental_result(self) -> None:
        source = GeorgiaElectionSource(
            year=2020,
            url="https://example.test/ga.zip",
            file_name="ga.zip",
            notes="test",
        )
        summary = {
            "source": {},
            "counties": [
                {
                    "fips": "13001",
                    "state": "GEORGIA",
                    "state_po": "GA",
                    "county_name": "APPLING",
                    "results": {"2020": {"totalvotes": 1, "supplemental": True}},
                }
            ],
        }

        with patch("merge_georgia_presidential.GEORGIA_PRESIDENTIAL_SOURCES", {2020: source}):
            with patch("merge_georgia_presidential.raw_path", return_value=Path(__file__)):
                with patch(
                    "merge_georgia_presidential.parse_official_zip",
                    return_value={"APPLING": {"DEMOCRAT": 10, "REPUBLICAN": 26}},
                ):
                    stats = merge_official_rows(summary)

        result = summary["counties"][0]["results"]["2020"]
        self.assertEqual(stats["replaced"], 1)
        self.assertTrue(result["official"])
        self.assertNotIn("supplemental", result)
        self.assertEqual(result["source_name"], "Georgia Secretary of State")
        self.assertEqual(result["quality_grade"], "A")
        self.assertEqual(summary["source"]["official_state_sources"][0]["state_po"], "GA")
