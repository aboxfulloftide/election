from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from register_county_presidential_geography_aliases import ALIASES


class CountyPresidentialGeographyAliasesTests(TestCase):
    def test_alias_registry_contains_current_json_normalization_rules(self) -> None:
        keys = {(alias.state_po, alias.target_fips, alias.alias_type, alias.alias_value) for alias in ALIASES}

        self.assertIn(("MO", "2938000", "fips", "36000"), keys)
        self.assertIn(("SD", "46102", "fips", "46113"), keys)
        self.assertIn(("SD", "46102", "name", "SHANNON"), keys)
