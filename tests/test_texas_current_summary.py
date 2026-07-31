from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from generate_texas_current_summary import build_summary, parse_current_results


class TexasCurrentSummaryTests(TestCase):
    def test_parse_current_results_reads_election_sections_and_tables(self) -> None:
        page = """
<title> Election Results - Tuesday, May 26, 2026</title>
<button><div>2026 REPUBLICAN PRIMARY RUNOFF ELECTION<span>(Updated 05/27/2026 09:20 AM)</span></div></button>
<div class="election">U. S. SENATOR </div>
<div class="polling">Polling Locations Reporting: 100%</div>
<table class="election">
  <tr class="header"><th class="candidate">Candidate</th><th class="ballot">Ballots Cast</th></tr>
  <tr><td class="candidate">KEN PAXTON</td><td class="ballot">885,949</td></tr>
  <tr><td class="candidate">JOHN CORNYN (I)</td><td class="ballot">501,725</td></tr>
</table>
"""

        contests = parse_current_results(page)

        self.assertEqual(len(contests), 1)
        self.assertEqual(contests[0].election_name, "2026 REPUBLICAN PRIMARY RUNOFF ELECTION")
        self.assertEqual(contests[0].updated_at, "Updated 05/27/2026 09:20 AM")
        self.assertEqual(contests[0].race_name, "U. S. SENATOR")
        self.assertEqual(contests[0].polling_reporting, "Polling Locations Reporting: 100%")
        self.assertEqual(contests[0].candidates[0], {"candidate": "KEN PAXTON", "votes": 885949})

    def test_build_summary_materializes_supported_statewide_contests(self) -> None:
        page = """
<title> Election Results - Tuesday, May 26, 2026</title>
<button><div>2026 DEMOCRATIC PRIMARY RUNOFF ELECTION<span>(Updated 05/27/2026 09:20 AM)</span></div></button>
<div class="election">STATE REPRESENTATIVE DISTRICT 49</div>
<div class="polling">Polling Locations Reporting: 100%</div>
<table class="election">
  <tr class="header"><th class="candidate">Candidate</th><th class="ballot">Ballots Cast</th></tr>
  <tr><td class="candidate">MONTSERRAT GARIBAY</td><td class="ballot">9,879</td></tr>
  <tr><td class="candidate">KATHIE TOVO</td><td class="ballot">5,987</td></tr>
</table>
<div class="election">ATTORNEY GENERAL</div>
<div class="polling">Polling Locations Reporting: 100%</div>
<table class="election">
  <tr class="header"><th class="candidate">Candidate</th><th class="ballot">Ballots Cast</th></tr>
  <tr><td class="candidate">NATHAN JOHNSON</td><td class="ballot">332,243</td></tr>
  <tr><td class="candidate">JOE JAWORSKI</td><td class="ballot">216,849</td></tr>
</table>
"""

        summary = build_summary(page)

        self.assertEqual(summary["election"]["year"], 2026)
        self.assertEqual(summary["election"]["election_date"], "2026-05-26")
        self.assertEqual(len(summary["contests"]), 1)
        contest = summary["contests"][0]
        self.assertEqual(contest["office"], "State House")
        self.assertEqual(contest["district_number"], 49)
        self.assertEqual(contest["winner"], {"candidate": "Montserrat Garibay", "party": "DEMOCRAT", "votes": 9879})
        self.assertEqual(contest["total_votes"], 15866)
