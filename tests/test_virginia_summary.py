from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from check_virginia_summary import validate_summary


class VirginiaSummaryTests(TestCase):
    def test_generated_summary_matches_verified_inventory(self) -> None:
        summary = json.loads((ROOT_DIR / "public/results/virginia-statewide-summary.json").read_text())
        contests = [contest for election in summary["elections"] for contest in election["contests"]]
        self.assertEqual(len(contests), 26)
        self.assertEqual({contest["office"] for contest in contests}, {"President", "U.S. Senate", "U.S. House"})
        self.assertTrue(all(contest["winner"]["votes"] > 0 for contest in contests))
        self.assertEqual(validate_summary(summary), [])

    def test_validator_catches_total_vote_mismatch(self) -> None:
        summary = json.loads((ROOT_DIR / "public/results/virginia-statewide-summary.json").read_text())
        summary["elections"][0]["contests"][0]["total_votes"] += 1
        failures = validate_summary(summary)
        self.assertTrue(any("candidate votes sum" in failure for failure in failures))
