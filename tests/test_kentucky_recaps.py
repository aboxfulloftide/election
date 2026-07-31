from __future__ import annotations

import sys
import json
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from download_kentucky_general_recaps import LinkParser, destination
from download_kentucky_certified import SOURCES
from ocr_kentucky_recaps import candidates, output_path


class KentuckyRecapDownloaderTests(TestCase):
    def test_parser_keeps_only_general_recap_documents(self) -> None:
        parser = LinkParser()
        parser.feed(
            '<a href="/results/2020-2029/2024ElectionReports/GeneralRecaps/Adair.pdf">Adair</a>'
            '<a href="/results/2020-2029/2024ElectionReports/Primary/Adair.pdf">Primary</a>'
            '<a href="/results/2020-2029/2024ElectionReports/GeneralRecaps/Rockcastle%20County.xlsx">Rockcastle</a>'
        )

        self.assertEqual(len(parser.links), 2)
        self.assertIn("GeneralRecaps", parser.links[0])
        self.assertTrue(parser.links[1].endswith(".xlsx"))

    def test_destination_is_year_scoped_and_safe(self) -> None:
        path = destination(
            2022,
            "https://elect.ky.gov/results/2020-2029/2022ElectionReports/GeneralRecaps/Butler%20County.pdf",
        )

        self.assertEqual(path, ROOT_DIR / "data/raw/official/kentucky/2022_Butler_County.pdf")

    def test_schema_audit_tracks_unusable_staged_reports(self) -> None:
        audit = json.loads(
            (ROOT_DIR / "public/results/kentucky-recap-schema-audit.json").read_text()
        )
        self.assertEqual(audit["summary"]["2022"]["content_status_counts"]["blank"], 67)
        self.assertEqual(audit["summary"]["2024"]["blank_files"], ["data/raw/official/kentucky/2024_Elliott.pdf"])
        self.assertEqual(audit["summary"]["2024"]["mail_in_only_files"], ["data/raw/official/kentucky/2024_Magoffin.pdf"])

    def test_ocr_selects_blank_reports_without_reprocessing_usable_reports(self) -> None:
        selected = candidates(2022, ["2022_Allen_County.pdf"])
        self.assertEqual(selected, [ROOT_DIR / "data/raw/official/kentucky/2022_Allen_County.pdf"])
        self.assertEqual(output_path(selected[0]), ROOT_DIR / "data/raw/official/kentucky/ocr/2022_Allen_County.txt")

    def test_certified_source_uses_official_2022_results_page(self) -> None:
        self.assertEqual(SOURCES[2022]["filename"], "2022_certified_general_election_results.pdf")
        self.assertIn("2022.aspx", SOURCES[2022]["page"])
