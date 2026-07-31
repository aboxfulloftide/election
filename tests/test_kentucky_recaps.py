from __future__ import annotations

import sys
import json
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from download_kentucky_general_recaps import LinkParser, destination
from download_kentucky_certified import SOURCES
from ocr_kentucky_certified import OCR_PDF_PATH, SOURCE_PATH, TEXT_PATH
from ocr_kentucky_recaps import candidates, output_path
from parse_kentucky_certified import certified_sections, parse_senate, parse_us_house_totals


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

    def test_certified_senate_parser_extracts_county_columns(self) -> None:
        text = """United States Senator
Republican Party Democratic Party Write-in Write-in
Rand PAUL Charles BOOKER
Allen 4,931 2,091 0 0
Anderson 6,887 2,091 0 0
Ballard 2.408 630 0 0
Total Votes 11,818 4,182 0 0
For the office of
United States Representative in Congress
"""
        result = parse_senate(text)
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["column_totals"], [14226, 4812, 0, 0])
        self.assertEqual(result["official_total_votes"], [11818, 4182, 0, 0])

    def test_certified_senate_parser_ignores_date_and_keeps_official_total(self) -> None:
        text = """United States Senator
November 8, 2022
Allen 4,931 2,091 0 0
Total Votes 4,931 2,091
For the office of
"""
        result = parse_senate(text)
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["official_total_votes"], [4931, 2091])

    def test_certified_ocr_paths_are_raw_data_scoped(self) -> None:
        self.assertEqual(SOURCE_PATH, ROOT_DIR / "data/raw/official/kentucky/2022_certified_general_election_results.pdf")
        self.assertEqual(OCR_PDF_PATH, ROOT_DIR / "data/raw/official/kentucky/2022_certified_general_election_results_ocr.pdf")
        self.assertEqual(TEXT_PATH, ROOT_DIR / "data/raw/official/kentucky/2022_certified_general_election_results_ocr.txt")

    def test_certified_section_inventory_identifies_office_lanes(self) -> None:
        text = """For the office of
United States Senator
table
For the office of
United States Representative in Congress
‘4st Congressional District
2nd Congressional District
3rd Congressional District
4th Congressional District
‘th Congressional District
6th Congressional District
For the office of
State Senator
16th Senatorial District
For the office of
State Representative
21st Representative District
"""
        sections = certified_sections(text)
        self.assertEqual([section["office"] for section in sections], ["United States Senator", "United States Representative in Congress", "State Senator", "State Representative"])
        self.assertEqual(sections[1]["districts"], ["1 congressional district", "2 congressional district", "3 congressional district", "4 congressional district", "5 congressional district", "6 congressional district"])
        self.assertTrue(sections[1]["districts_inferred"])
        self.assertEqual(sections[2]["districts"], ["16 senatorial district"])

    def test_certified_house_parser_extracts_printed_district_totals(self) -> None:
        text = """United States Representative in Congress
1st Congressional District
Allen 4,931 2,091
Total Votes 4,931 2,091
2nd Congressional District
Ohio 5,617 1,660
Total Votes 5,617 1,660
For the office of
"""
        self.assertEqual(
            parse_us_house_totals(text),
            [
                {"district": 1, "official_total_votes": [4931, 2091]},
                {"district": 2, "official_total_votes": [5617, 1660]},
            ],
        )
