from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_florida_precinct_join", ROOT_DIR / "scripts/check_florida_precinct_join.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FloridaPrecinctPreflightTests(TestCase):
    def test_preflight_distinguishes_complete_partial_and_blocked_joins(self) -> None:
        complete = MODULE.audit_bundle(ROOT_DIR / "public/results/precincts/florida-broward-2024-precincts.json")
        partial = MODULE.audit_bundle(ROOT_DIR / "public/results/precincts/florida-miami-dade-2014-precincts.json")
        blocked = MODULE.audit_bundle(ROOT_DIR / "public/results/precincts/florida-broward-2022-precincts.json")

        self.assertEqual(complete["unmatched_result_precinct_count"], 0)
        self.assertGreater(partial["unmatched_result_precinct_count"], 0)
        self.assertEqual(blocked["matched_result_precinct_count"], 0)
        self.assertTrue(all(office in MODULE.ALLOWED_OFFICES for office in complete["offices"]))
