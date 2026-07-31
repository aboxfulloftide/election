from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from generate_texas_mayor_summary import (
    build_contest,
    cache_stem,
    parse_electionware_mayor_csv,
    parse_electionware_media_html,
    parse_electionware_summary_pdf_text,
    parse_harris_cumulative_pdf_text,
    parse_houston_citysec_combined_pdf_text,
    parse_san_antonio_canvass_pdf_text,
    parse_austin_resolution_pdf_text,
    parse_dallas_resolution_pdf_text,
    parse_dallas_master_list_pdf_text,
    parse_tables,
)
from texas_mayor_config import FORT_WORTH_SOURCE, TexasMayorElectionFile


class TexasMayorSummaryTests(TestCase):
    def test_cache_stem_is_stable_and_filename_safe(self) -> None:
        stem = cache_stem("https://example.test/reports/Canvassing%20Report-May2023.pdf?id=7")

        self.assertRegex(stem, r"^[a-f0-9]{16}-Canvassing-Report-May2023.pdf$")

    def test_parse_dallas_master_list_reads_historical_place_11_mayor_rows(self) -> None:
        election_file = TexasMayorElectionFile(
            year=1987,
            election_date="1987-04-18",
            election_stage="runoff",
            election_name="Dallas mayor runoff",
            url="https://example.test/electmasterlist.pdf",
            format="dallas-master-list-pdf",
        )
        text = """
        Council-Manager
        1987-1989 Run Off Election
        Place No. 11/Mayor: Annette Strauss 61,978
                              Fred Meyer 48,710
        Councilmembers:
        Place No. 1: Charles Tandy 7,818
        """

        candidates = parse_dallas_master_list_pdf_text(text, election_file)

        self.assertEqual(candidates[0], {"candidate": "Annette Strauss", "party": "NONPARTISAN", "votes": 61978})
        self.assertEqual(candidates[1], {"candidate": "Fred Meyer", "party": "NONPARTISAN", "votes": 48710})

    def test_parse_dallas_master_list_selects_runoff_block_when_both_are_present(self) -> None:
        election_file = TexasMayorElectionFile(
            year=1987,
            election_date="1987-04-18",
            election_stage="runoff",
            election_name="Dallas mayor runoff",
            url="https://example.test/electmasterlist.pdf",
            format="dallas-master-list-pdf",
        )
        text = """
        Election: Saturday, April 04, 1987
        Run Off Election: Saturday, April 18, 1987
        Place No. 11/Mayor: Annette Strauss 48,077
                              Fred Meyer 29,379
        Councilmembers:
        Place No. 11/Mayor: Annette Strauss 61,978
                              Fred Meyer 48,710
        Councilmembers:
        """

        candidates = parse_dallas_master_list_pdf_text(text, election_file)

        self.assertEqual(candidates[0]["votes"], 61978)
        self.assertEqual(candidates[1]["votes"], 48710)

    def test_parse_table_with_mayor_label_inside_table(self) -> None:
        page = """
        <h3><span><a href="https://example.test/2025">General Election, May 3, 2025</a></span></h3>
        <p>Results</p>
        <table>
          <tr><td><p><span>Mayor</span></p></td><td></td><td></td><td></td></tr>
          <tr><td><strong>Candidate</strong></td><td><strong>Tarrant County</strong></td><td><strong>Denton County</strong></td><td><strong>Vote Total</strong></td></tr>
          <tr><td>Mattie Parker</td><td>26,104</td><td>278</td><td>26,382</td></tr>
          <tr><td>Josh Lucas</td><td>7,005</td><td>57</td><td>7,062</td></tr>
          <tr><td><span>District 2</span></td><td></td><td></td><td></td></tr>
        </table>
        """

        tables = parse_tables(page)
        contest = build_contest(FORT_WORTH_SOURCE, tables[0], 1)

        self.assertIsNotNone(contest)
        assert contest is not None
        self.assertEqual(contest["year"], 2025)
        self.assertEqual(contest["election_date"], "2025-05-03")
        self.assertEqual(contest["election_stage"], "general")
        self.assertEqual(contest["total_votes"], 33444)
        self.assertEqual(contest["winner"]["candidate"], "Mattie Parker")
        self.assertEqual(contest["candidates"][0]["county_votes"], {"Tarrant County": 26104, "Denton County": 278})

    def test_parse_table_with_mayor_label_before_table(self) -> None:
        page = """
        <h4><span><a href="https://example.test/2023">General Election, May 6, 2023</a></span></h4>
        <p>Results</p>
        <p><span>Mayor</span></p>
        <table>
          <tr><td><strong>Candidate</strong></td><td><strong>Tarrant County</strong></td><td><strong>Parker County</strong></td><td><strong>Vote Total</strong></td></tr>
          <tr><td>Mattie Parker</td><td>29,345</td><td>355</td><td>29,700</td></tr>
          <tr><td>Alyson Kennedy</td><td>2,209</td><td>20</td><td>2,229</td></tr>
        </table>
        """

        tables = parse_tables(page)
        contest = build_contest(FORT_WORTH_SOURCE, tables[0], 7)

        self.assertIsNotNone(contest)
        assert contest is not None
        self.assertEqual(contest["contest_id"], 7)
        self.assertEqual(contest["source_url"], "https://example.test/2023")
        self.assertEqual(contest["total_votes"], 31929)
        self.assertEqual(contest["margin_votes"], 27471)
        self.assertEqual(contest["winner"], contest["candidates"][0])

    def test_parse_san_antonio_precinct_csv_aggregates_mayor_sections(self) -> None:
        csv_text = """
Summary Results Report,,,,,,,,,,OFFICIAL RESULTS,,,
1001 BS 1,,,,,,,,,,,,,
,For Mayor City of San Antonio,,,,,,,,,,,,
,,,TOTAL,,VOTE %,,Election Day,,Absentee,,,Early Voting,
Rolando Pablos,,4,,3.03%,,0,,0,,,4,,
Gina Ortiz Jones,,42,,31.82%,,13,,3,,,26,,
Total Votes Cast,,46,,100.00%,,13,,3,,,30,,
1002 BS 2,,,,,,,,,,,,,
,For Mayor City of San Antonio,,,,,,,,,,,,
,,,TOTAL,,VOTE %,,Election Day,,Absentee,,,Early Voting,
Rolando Pablos,,9,,45.00%,,2,,0,,,7,,
Gina Ortiz Jones,,11,,55.00%,,3,,0,,,8,,
Total Votes Cast,,20,,100.00%,,5,,0,,,15,,
"""

        candidates = sorted(parse_electionware_mayor_csv(csv_text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Gina Ortiz Jones", "party": "NONPARTISAN", "votes": 53})
        self.assertEqual(candidates[1], {"candidate": "Rolando Pablos", "party": "NONPARTISAN", "votes": 13})

    def test_parse_san_antonio_summary_pdf_text_reads_candidate_lines(self) -> None:
        text = """
Summary Results Report OFFICIAL RESULTS
City of San Antonio Runoff Election Vote Center 182of 182
For Mayor City of San Antonio
Vote For 1
Rolando Pablos                                65,245 45.68% 16,343 1,488 47,414
Gina ortiz Jones                              77,587 54.32% 23,853 2,888 50,846
Antonio "Tony" Diaz                            1,358 0.91% 545 54 759
Denise Gutierrez-Homer                         2,711 1.82% 870 143 1,698
Total Votes Cast                             112,832 100.00% f0,196 4,376 98,260
For Council, District 1 City of San Antonio
"""

        candidates = sorted(parse_electionware_summary_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Gina Ortiz Jones", "party": "NONPARTISAN", "votes": 77587})
        self.assertEqual(candidates[1], {"candidate": "Rolando Pablos", "party": "NONPARTISAN", "votes": 65245})
        self.assertIn({"candidate": 'Antonio "Tony" Diaz', "party": "NONPARTISAN", "votes": 1358}, candidates)
        self.assertIn({"candidate": "Denise Gutierrez-Homer", "party": "NONPARTISAN", "votes": 2711}, candidates)

    def test_parse_san_antonio_media_html_reads_dot_leader_rows(self) -> None:
        page = """
        <HTML><PRE>
Mayor City of San Antonio
Vote For  1
 Ron Nirenberg .  .  .  .  .  .  .  .  .     61,741   51.11        45,999        15,742
 Greg Brockhouse  .  .  .  .  .  .  .  .     59,051   48.89        43,207        15,844
    Over Votes .  .  .  .  .  .  .  .  .          1                     1             0
CITY OF SAN ANTONIO Member of Council, Place 1
 Ron Nirenberg .  .  .  .  .  .  .  .  .      1,000   90.00           900           100
        </PRE></HTML>
        """

        candidates = sorted(parse_electionware_media_html(page), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Ron Nirenberg", "party": "NONPARTISAN", "votes": 61741})
        self.assertEqual(candidates[1], {"candidate": "Greg Brockhouse", "party": "NONPARTISAN", "votes": 59051})

    def test_parse_san_antonio_media_html_reads_plain_mayor_archive_heading(self) -> None:
        page = """
        <HTML><PRE>
  Mayor
  VOTE FOR 1
   Julian Castro . . . . .              .   .   .   .     47,893      41.99     21,515     26,378
   Carroll Schubert . . . .             .   .   .   .     30,029      26.32     15,645     14,384
   Phil Hardberger . . . .              .   .   .   .     34,280      30.05     17,657     16,623
  City Council DISTRICT 1
   Roger O. Flores . . . .              .   .   .   .       4,709    100.00      1,871      2,838
        </PRE></HTML>
        """

        candidates = sorted(parse_electionware_media_html(page), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Julian Castro", "party": "NONPARTISAN", "votes": 47893})
        self.assertIn({"candidate": "Phil Hardberger", "party": "NONPARTISAN", "votes": 34280}, candidates)
        self.assertNotIn({"candidate": "Roger O. Flores", "party": "NONPARTISAN", "votes": 4709}, candidates)

    def test_parse_san_antonio_media_html_reads_cosa_mayor_archive_heading(self) -> None:
        page = """
        <HTML><PRE>
COSA, Mayor COSA MAYOR
VOTE FOR 1
    (WITH 527 OF 527 PRECINCTS COUNTED)
 R G Griffing . . . . . . . . .                     1,524      2.20       908        616
 Julie Iris Oldham. . . . . . . .                   2,097      3.03     1,308        789
 Patrick McCurdy . . . . . . . .                    5,611      8.10     3,075      2,536
 Michael Idrogo. . . . . . . . .                    1,347      1.95       777        570
 Phil Hardberger . . . . . . . .                   53,553     77.34    32,885     20,668
 Rhett R. Smith. . . . . . . . .                      919      1.33       558        361
 Eiginio Rodriguez. . . . . . . .                   4,189      6.05     2,150      2,039

COSA Place 1 COSA SMD #1
 Kat Swift . . . . . . . . .               .        1,630     29.48       696        934
        </PRE></HTML>
        """

        candidates = sorted(parse_electionware_media_html(page), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Phil Hardberger", "party": "NONPARTISAN", "votes": 53553})
        self.assertIn({"candidate": "Eiginio Rodriguez", "party": "NONPARTISAN", "votes": 4189}, candidates)
        self.assertNotIn({"candidate": "Kat Swift", "party": "NONPARTISAN", "votes": 1630}, candidates)

    def test_parse_san_antonio_canvass_pdf_text_reads_place_11_mayor_rows(self) -> None:
        text = """
FOR MEMBER OF COUNCIL, PLACE NO. 11 (MAYOR):

            "FOR"        Julie Iris Oldham                    919 votes
            "FOR"        Julian Castro                     47,903 votes
            "FOR"        Phil Hardberger                   34,292 votes
            "FOR"        Rhett R. Smith                       - 289

SECTION 3. As a result of said election
"""

        candidates = sorted(parse_san_antonio_canvass_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Julian Castro", "party": "NONPARTISAN", "votes": 47903})
        self.assertIn({"candidate": "Phil Hardberger", "party": "NONPARTISAN", "votes": 34292}, candidates)
        self.assertIn({"candidate": "Rhett R. Smith", "party": "NONPARTISAN", "votes": 289}, candidates)

    def test_parse_san_antonio_canvass_pdf_text_reads_runoff_rows(self) -> None:
        text = """
FOR MEMBER OF COUNCIL, PLACE NO. 11 (MAYOR):

           Phil Hardberger                            66,873    votes
           Julian Castro                              63,168    votes

SECTION 3. It is further declared
"""

        candidates = sorted(parse_san_antonio_canvass_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Phil Hardberger", "party": "NONPARTISAN", "votes": 66873})
        self.assertEqual(candidates[1], {"candidate": "Julian Castro", "party": "NONPARTISAN", "votes": 63168})

    def test_parse_san_antonio_canvass_pdf_text_reads_2003_mayor_rows(self) -> None:
        text = """
        FOR MEMBER OF COUNCIL, PLACE NO. 11 (MAYOR):
        "FOR" Shirley Thompson 9,897 votes
        "FOR" Ed Garza 26,456 votes
        "FOR" Michael Idrogo 2,410 votes
        SECTION 2. As a result of said election
        """

        candidates = sorted(parse_san_antonio_canvass_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Ed Garza", "party": "NONPARTISAN", "votes": 26456})
        self.assertEqual(candidates[-1], {"candidate": "Michael Idrogo", "party": "NONPARTISAN", "votes": 2410})

    def test_parse_san_antonio_canvass_pdf_text_reads_1999_mayor_rows(self) -> None:
        text = """
        FOR MEMBER OF COUNCIL, PLACE NO. 11 (MAYOR):
        "FOR" Eloy Centeno 1,727 votes
        "FOR" Tony R. Garza 2,024 votes
        "FOR" Howard W. Peak 40,506 votes
        "FOR" Louis Podesta 1,724 votes
        "FOR" Joseph V. Rodriguez de Cisneros 1,588 votes
        SECTION 2. It is further declared
        """

        candidates = sorted(parse_san_antonio_canvass_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Howard W. Peak", "party": "NONPARTISAN", "votes": 40506})
        self.assertEqual(sum(item["votes"] for item in candidates), 47569)

    def test_parse_harris_cumulative_pdf_text_reads_final_total_column(self) -> None:
        text = """
City of Houston, Mayor - Vote for none or one
Choice                                     Party      Ballot by Mail      Early Voting         Election Day      EV Provisional   ED Provisional                      Total
John Whitmire                                         8,301   60.73%   77,404   65.78%       43,304     65.24%     161   66.53%      47   69.12%          129,217   65.25%
Sheila Jackson Lee                                    5,367   39.27%   40,274   34.22%       23,076     34.76%      81   33.47%      21   30.88%           68,819   34.75%
                                        Cast Votes:   13,668 100.00%   117,678 100.00%       66,380 100.00%        242 100.00%       68 100.00%           198,036   100.00%
"""

        candidates = sorted(
            parse_harris_cumulative_pdf_text(text, "City of Houston, Mayor - Vote for none or one"),
            key=lambda item: item["votes"],
            reverse=True,
        )

        self.assertEqual(candidates[0], {"candidate": "John Whitmire", "party": "NONPARTISAN", "votes": 129217})
        self.assertEqual(candidates[1], {"candidate": "Sheila Jackson Lee", "party": "NONPARTISAN", "votes": 68819})

    def test_parse_harris_cumulative_pdf_text_accepts_archive_heading_variants(self) -> None:
        text = """
 City of Houston, MAYOR, Vote For 1

                Annise D. Parker                                                 5,975     50.61%                28,043       51.09%             47,841        55.62%    81,859      53.60%
                Gene Locke                                                       5,831     49.39%                26,849       48.91%             38,178        44.38%    70,858      46.40%

                                                   Cast Votes:                  11,806     97.26%                54,892       98.69%             86,019        98.63%   152,717      98.54%
"""

        candidates = sorted(
            parse_harris_cumulative_pdf_text(text, "City of Houston, Mayor - Vote for none or one"),
            key=lambda item: item["votes"],
            reverse=True,
        )

        self.assertEqual(candidates[0], {"candidate": "Annise D. Parker", "party": "NONPARTISAN", "votes": 81859})
        self.assertEqual(candidates[1], {"candidate": "Gene Locke", "party": "NONPARTISAN", "votes": 70858})

    def test_parse_houston_citysec_combined_pdf_text_reads_mayor_summary(self) -> None:
        text = """
CITY OF HOUSTON GENERAL ELECTION
HARRIS, FORT BEND AND MONTGOMERY COUNTIES COMBINED
NOVEMBER 6, 2007

COUNT      PERCENT

MAYOR
AMANDA C. ULMAN                                 8,832       7.52
OUTLAW JOSEY WALES, IV                          7,042       6.00
BILL WHITE                                    101,557      86.48

COUNCIL MEMBER, DISTRICT A
TONI LAWRENCE                                   9,985     100.00
"""

        candidates = sorted(parse_houston_citysec_combined_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "BILL WHITE", "party": "NONPARTISAN", "votes": 101557})
        self.assertIn({"candidate": "AMANDA C. ULMAN", "party": "NONPARTISAN", "votes": 8832}, candidates)
        self.assertNotIn({"candidate": "TONI LAWRENCE", "party": "NONPARTISAN", "votes": 9985}, candidates)

    def test_parse_houston_citysec_combined_pdf_text_normalizes_known_ocr_name(self) -> None:
        text = """
CITY OF HOUSTON GENERAL ELECTION
HARRIS, FORT BEND AND MONTGOMERY COUNTIES COMBINED
NOVEMBER 6, 2001

COUNT      PERCENT

MAYOR
LEE BROWN                                    125,282      43.41
ORLANDO SANCHEZ                              115,967      40.18
,"\\NTHONY M. DUTROW                             235       0.08

COUNCIL MEMBER, DISTRICT A
"""

        candidates = sorted(parse_houston_citysec_combined_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertIn({"candidate": "ANTHONY M. DUTROW", "party": "NONPARTISAN", "votes": 235}, candidates)

    def test_parse_austin_resolution_pdf_text_reads_city_mayor_section(self) -> None:
        text = """
WHEREAS, the returns of the general election have been made to the
Council and show that the votes for Mayor and City Council Members were cast as
follows:
12   Mayor
13   Carmen D. Llanes Pulido            [70,535]70,540
14   Jeffery L. Bowen                   29,383
15   Doug Greco                         16,865
16   Kirk Watson                        [175,090]175,096
17   Kathie Tovo                        [58,278]58,280
18   City Council Member District 2
Vanessa Fuentes                    22,591
"""

        candidates = sorted(parse_austin_resolution_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Kirk Watson", "party": "NONPARTISAN", "votes": 175096})
        self.assertIn({"candidate": "Carmen D. Llanes Pulido", "party": "NONPARTISAN", "votes": 70540}, candidates)

    def test_parse_dallas_resolution_pdf_text_reads_place_15_mayor_section(self) -> None:
        text = """
For Member of Council, Place 15 (Mayor):
Lynn McBee                       11,324
Jason Villalba                    5,444
Scott Griggs                     14,921
Mike Ablon                       10,878
Miguel Solis                      8,647
Alyson Kennedy                      469
Regina Montoya                    8,440
Eric Johnson                     16,402
Albert Black                      4,2r0
Write-In                            136
For Member of Council, Place 1:
Chad West                         9,000
"""

        candidates = sorted(parse_dallas_resolution_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Eric Johnson", "party": "NONPARTISAN", "votes": 16402})
        self.assertEqual(candidates[1], {"candidate": "Scott Griggs", "party": "NONPARTISAN", "votes": 14921})
        self.assertIn({"candidate": "Albert Black", "party": "NONPARTISAN", "votes": 4210}, candidates)
        self.assertIn({"candidate": "Write-In", "party": "NONPARTISAN", "votes": 136}, candidates)
        self.assertNotIn({"candidate": "Chad West", "party": "NONPARTISAN", "votes": 9000}, candidates)

    def test_parse_dallas_resolution_pdf_text_reads_older_place_15_heading(self) -> None:
        text = """
       For Member of Council, Place 15:

              John Cappello                                            504
              Roger Herrera                                            972
              Gary Griffith                                          6,656
              Ed Oakley                                             14,754
              Tom Leppert                                           19,367
              Write-in                                                 103

For Member of Council, Place 1:
        Elba Garcia                   1,543
"""

        candidates = sorted(parse_dallas_resolution_pdf_text(text), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Tom Leppert", "party": "NONPARTISAN", "votes": 19367})
        self.assertIn({"candidate": "Ed Oakley", "party": "NONPARTISAN", "votes": 14754}, candidates)
        self.assertIn({"candidate": "Write-in", "party": "NONPARTISAN", "votes": 103}, candidates)
        self.assertNotIn({"candidate": "Elba Garcia", "party": "NONPARTISAN", "votes": 1543}, candidates)

    def test_parse_dallas_master_list_pdf_text_reads_2002_special_mayor(self) -> None:
        text = """
Place 15/Mayor:                      N/A

Councilmembers:
Place No. 1:                         Elba Garcia                        1,189

Place 15/Mayor:            Laura Miller                     64,224
                           Tom Dunning                      51,302
                           Domingo Garcia                   14,631
                           Marvin Crenshaw                   1,214
                           Jurline Hollins                     226

Councilmember:
Place No. 3:               Mark Housewright                  2,750
"""
        election_file = TexasMayorElectionFile(
            year=2002,
            election_date="2002-01-19",
            election_stage="special",
            election_name="January 19, 2002 Dallas Special Election",
            url="https://example.test/master.pdf",
            format="dallas-master-list-pdf",
        )

        candidates = sorted(parse_dallas_master_list_pdf_text(text, election_file), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Laura Miller", "party": "NONPARTISAN", "votes": 64224})
        self.assertIn({"candidate": "Tom Dunning", "party": "NONPARTISAN", "votes": 51302}, candidates)

    def test_parse_dallas_master_list_pdf_text_reads_2002_special_runoff_mayor(self) -> None:
        text = """
Place 15, Mayor:            Laura Miller                     72,983
                            Tom Dunning                      60,053

Councilmember:
Place No. 3:                Mark Housewright                  4,300
"""
        election_file = TexasMayorElectionFile(
            year=2002,
            election_date="2002-02-16",
            election_stage="runoff",
            election_name="February 16, 2002 Dallas Special Runoff Election",
            url="https://example.test/master.pdf",
            format="dallas-master-list-pdf",
        )

        candidates = sorted(parse_dallas_master_list_pdf_text(text, election_file), key=lambda item: item["votes"], reverse=True)

        self.assertEqual(candidates[0], {"candidate": "Laura Miller", "party": "NONPARTISAN", "votes": 72983})
        self.assertEqual(candidates[1], {"candidate": "Tom Dunning", "party": "NONPARTISAN", "votes": 60053})
