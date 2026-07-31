from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from generate_texas_summary import (
    PdfContestAccumulator,
    build_pdf_contest,
    office_for_race,
    parse_pdf_candidate_label,
    parse_race_options,
    parse_race_page,
    pdf_office_for_race,
)
from texas_config import TexasCanvassPdfElection


class TexasSummaryTests(TestCase):
    def test_parse_race_options_filters_supported_offices(self) -> None:
        page = """
        <SELECT NAME='lboRace'>
          <OPTION value="832">U. S. Senator
          <OPTION value="63">U. S. Representative District 1
          <OPTION value="833">Governor
          <OPTION value="95">Justice, Supreme Court, Place 2
        </SELECT>
        """

        self.assertEqual(
            parse_race_options(page),
            [(832, "U. S. Senator"), (63, "U. S. Representative District 1"), (833, "Governor")],
        )

    def test_parse_race_page_reads_candidate_and_county_rows(self) -> None:
        page = """
        <TABLE>
          <TR><TH>...</TH><TH>Ted Cruz</TH><TH>Beto O'Rourke</TH><TH>...</TH><TH>...</TH><TH>...</TH></TR>
          <TR><TH>...</TH><TH></TH><TH></TH><TH>Total</TH><TH>Total</TH><TH>...</TH></TR>
          <TR><TH>County</TH><TH>REP</TH><TH>DEM</TH><TH>Votes</TH><TH>Voters</TH><TH>TurnOut</TH></TR>
          <TR><TD>ALL COUNTIES</TD><TD>15</TD><TD>10</TD><TD>25</TD><TD>100</TD><TD>25.00%</TD></TR>
          <TR><TD><FONT>ANDERSON</FONT></TD><TD><FONT>11</FONT></TD><TD><FONT>3</FONT></TD><TD><FONT>14</FONT></TD><TD>20</TD><TD>70.00%</TD></TR>
        </TABLE>
        """

        candidates, counties = parse_race_page(page)

        self.assertEqual(candidates, [{"candidate": "Ted Cruz", "party": "REPUBLICAN"}, {"candidate": "Beto O'Rourke", "party": "DEMOCRAT"}])
        self.assertEqual(counties, [{"county_name": "ANDERSON", "candidate_votes": [11, 3], "total_votes": 14}])

    def test_office_for_race_maps_districts(self) -> None:
        self.assertEqual(office_for_race("State Senator, District 10"), ("State Senate", 10, "10 State Senate District"))

    def test_pdf_helpers_map_offices_and_candidate_parties(self) -> None:
        self.assertEqual(pdf_office_for_race("PRESIDENT/VICE-PRESIDENT"), ("President", None, None))
        self.assertEqual(pdf_office_for_race("U. S. SENATOR"), ("U.S. Senate", None, None))
        self.assertEqual(pdf_office_for_race("STATE REPRESENTATIVE DISTRICT 33"), ("State House", 33, "33 State House District"))
        self.assertEqual(parse_pdf_candidate_label("TED CRUZ (I) [REP]"), {"candidate": "TED CRUZ", "party": "REPUBLICAN"})
        self.assertEqual(parse_pdf_candidate_label("TRACY ANDRUS [WRI]"), {"candidate": "TRACY ANDRUS", "party": "WRITE-IN"})

    def test_build_pdf_contest_materializes_district_county_rows(self) -> None:
        election = TexasCanvassPdfElection(
            year=2024,
            election_date="2024-11-05",
            election_name="2024 November 5th General Election",
            source_url="https://example.test/texas",
            raw_path="data/raw/texas/example.pdf",
        )
        county_lookup = {"ANDERSON": {"fips": "48001", "county_name": "Anderson County"}}
        parsed = PdfContestAccumulator(
            name="STATE REPRESENTATIVE DISTRICT 1",
            labels=["ALICE EXAMPLE [REP]", "BOB EXAMPLE [DEM]"],
            rows={"ANDERSON": {"votes": [12, 7], "total_votes": 19}},
            county_order=["ANDERSON"],
        )

        contest = build_pdf_contest(election, parsed, county_lookup, 42)

        self.assertIsNotNone(contest)
        assert contest is not None
        self.assertEqual(contest["office"], "State House")
        self.assertEqual(contest["district_number"], 1)
        self.assertEqual(contest["total_votes"], 19)
        self.assertEqual(contest["counties"][0]["winner"]["candidate"], "ALICE EXAMPLE")
        self.assertEqual(contest["quality_grade"], "B")

    def test_build_pdf_contest_materializes_statewide_county_rows(self) -> None:
        election = TexasCanvassPdfElection(
            year=2024,
            election_date="2024-11-05",
            election_name="2024 November 5th General Election",
            source_url="https://example.test/texas",
            raw_path="data/raw/texas/example.pdf",
        )
        parsed = PdfContestAccumulator(
            name="PRESIDENT/VICE-PRESIDENT",
            labels=["ALICE EXAMPLE [REP]", "BOB EXAMPLE [DEM]"],
            rows={"ANDERSON": {"votes": [12, 7], "total_votes": 19}},
            county_order=["ANDERSON"],
        )
        county_lookup = {"ANDERSON": {"fips": "48001", "county_name": "Anderson County"}}

        contest = build_pdf_contest(election, parsed, county_lookup, 1)

        self.assertIsNotNone(contest)
        assert contest is not None
        self.assertEqual(contest["office"], "President")
        self.assertEqual(contest["total_votes"], 19)
        self.assertNotIn("district_number", contest)
