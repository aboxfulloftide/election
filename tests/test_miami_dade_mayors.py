from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from florida_mayor_config import FloridaMayorSource
from generate_florida_mayor_summary import build_contest, candidate_from_cell, parse_mayor_races, place_from_race_name


class MiamiDadeMayorTests(TestCase):
    def test_parse_mayor_races_reads_detail_table_totals(self) -> None:
        page = """
        <div id="1" class="Race row">
          <div class="RaceHeader"><div class="row RaceName"><label><label>Miami Mayor</label></label></div></div>
          <table class="DetailResults"><tbody>
            <tr><td class="ChoiceColumn">Jane Doe</td><td>1</td><td class="TotalVotes">1,234</td><td>60.00%</td></tr>
            <tr><td class="ChoiceColumn">John Roe</td><td>2</td><td class="TotalVotes">823</td><td>40.00%</td></tr>
          </tbody></table>
          <div class="GraphicalResults"><div>Jane Doe</div><div>1,234</div></div>
        </div>
        <div id="2" class="Race row">
          <div class="RaceHeader"><div class="row RaceName"><label><label>Miami Question 1</label></label></div></div>
        </div>
        <div id="3" class="Race row">
          <div class="RaceHeader"><div class="row RaceName"><label><label>Surfside Terms Mayor/Comm</label></label></div></div>
          <table class="DetailResults"><tbody>
            <tr><td class="ChoiceColumn">Yes</td><td>1</td><td class="TotalVotes">10</td><td>60.00%</td></tr>
            <tr><td class="ChoiceColumn">No</td><td>2</td><td class="TotalVotes">8</td><td>40.00%</td></tr>
          </tbody></table>
        </div>
        """

        races = parse_mayor_races(page)

        self.assertEqual(len(races), 1)
        self.assertEqual(races[0]["race_name"], "Miami Mayor")
        self.assertEqual(races[0]["rows"][0][-2], "1,234")

    def test_build_contest_sorts_candidates_and_sets_margin(self) -> None:
        source = FloridaMayorSource(
            2021,
            "2021-11-02",
            "Municipal Elections",
            "Miami-Dade",
            "12086",
            "Example SOE",
            "https://example.test",
            "https://example.test/enr",
        )
        race = {
            "source_race_id": "10",
            "race_name": "Miami Mayor",
            "rows": [["A", "0", "50", "50%"], ["B", "0", "70", "70%"]],
        }

        contest = build_contest(source, race, 3)

        self.assertEqual(contest["contest_id"], 3)
        self.assertEqual(contest["place"], "Miami")
        self.assertEqual(contest["total_votes"], 120)
        self.assertEqual(contest["winner"]["candidate"], "B")
        self.assertEqual(contest["margin_votes"], 20)

    def test_place_from_race_name_normalizes_miami_beach_abbreviation(self) -> None:
        self.assertEqual(place_from_race_name("MiaBch Mayor"), "Miami Beach")

    def test_place_from_race_name_uses_default_for_generic_mayor_race(self) -> None:
        self.assertEqual(place_from_race_name("Mayor", "Tampa"), "Tampa")

    def test_candidate_from_cell_preserves_partisan_suffixes(self) -> None:
        self.assertEqual(candidate_from_cell("Donna Deegan (DEM)"), {"candidate": "Donna Deegan", "party": "DEMOCRAT"})
        self.assertEqual(candidate_from_cell("Omega Allen (NPA)"), {"candidate": "Omega Allen", "party": "NONPARTISAN"})
