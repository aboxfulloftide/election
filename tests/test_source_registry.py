from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from report_source_registry import load_registry, report_markdown


class SourceRegistryTests(TestCase):
    def test_registry_loads_and_has_cohort_states(self) -> None:
        states = load_registry()
        self.assertEqual(
            [state["state_po"] for state in states],
            ["FL", "CA", "PA", "TX", "OH", "GA", "KY", "NC", "VA", "WI"],
        )

    def test_registry_has_imported_and_backlog_entries(self) -> None:
        entries = [entry for state in load_registry() for entry in state["entries"]]
        statuses = {entry["status"] for entry in entries}
        self.assertIn("imported", statuses)
        self.assertIn("source_identified", statuses)
        self.assertTrue(any(entry["format"] == "spreadsheet-statement-of-vote" and entry["status"] == "imported" for entry in entries))

    def test_report_groups_backlog_by_format(self) -> None:
        report = report_markdown(load_registry())
        self.assertIn("## Backlog By Parser Family", report)
        self.assertIn("`state-portal-mixed`", report)
        self.assertIn("Recommended Bulk Lanes", report)
