from __future__ import annotations

import json
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]


class VirginiaInventoryTests(TestCase):
    def test_inventory_contains_official_contest_csv_endpoints(self) -> None:
        inventory = json.loads(
            (ROOT_DIR / "public/results/virginia-official-contest-inventory.json").read_text()
        )
        self.assertGreaterEqual(len(inventory["contests"]), 17)
        self.assertEqual(
            {contest["office"] for contest in inventory["contests"]},
            {"President", "U.S. Senate", "U.S. House"},
        )
        self.assertTrue(all(contest["csv_url"].startswith("https://va2.elstats3.civera.com/api/download_contest/") for contest in inventory["contests"]))
