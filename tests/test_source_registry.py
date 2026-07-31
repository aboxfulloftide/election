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
        state_pos = [state["state_po"] for state in states]
        self.assertEqual(state_pos[:5], ["FL", "CA", "PA", "TX", "OH"])
        self.assertEqual(set(state_pos[5:]), {"GA", "KY", "NC", "VA", "WI", "AL", "AK", "AZ", "AR", "CO", "CT", "DE", "HI", "ID", "IL"})
        self.assertEqual(len(state_pos), 20)

    def test_registry_has_imported_and_backlog_entries(self) -> None:
        entries = [entry for state in load_registry() for entry in state["entries"]]
        statuses = {entry["status"] for entry in entries}
        self.assertIn("imported", statuses)
        self.assertIn("source_identified", statuses)
        self.assertTrue(any(entry["format"] == "spreadsheet-statement-of-vote" and entry["status"] == "imported" for entry in entries))
        legacy = [entry for entry in entries if entry["id"].endswith("-legacy-source")]
        self.assertEqual(len(legacy), 100)
        self.assertTrue(all(entry["status"] == "source_identified" for entry in legacy))

    def test_report_groups_backlog_by_format(self) -> None:
        report = report_markdown(load_registry())
        self.assertIn("## Backlog By Parser Family", report)
        self.assertIn("`state-portal-mixed`", report)
        self.assertIn("Recommended Bulk Lanes", report)
