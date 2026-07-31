from __future__ import annotations

import json
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]


class FloridaPrecinctCatalogTests(TestCase):
    def test_catalog_keeps_audit_bundles_but_marks_only_joined_data_map_ready(self) -> None:
        catalog = json.loads((ROOT_DIR / "public/results/florida-precinct-catalog.json").read_text())
        by_key = {(entry["county_fips"], entry["year"]): entry["map_ready"] for entry in catalog["bundles"]}

        self.assertEqual(len(catalog["bundles"]), 5)
        self.assertTrue(by_key[("12011", 2020)])
        self.assertFalse(by_key[("12011", 2022)])
        self.assertTrue(by_key[("12011", 2024)])
        self.assertTrue(by_key[("12086", 2012)])
        self.assertTrue(by_key[("12086", 2014)])
