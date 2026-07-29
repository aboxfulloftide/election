#!/usr/bin/env python3
"""Generate coverage metadata for the county presidential summary."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR
from fetch_results import SUMMARY_PATH


COVERAGE_PATH = Path("public/results/county-presidential-coverage.json")


def pct(part: int, whole: int) -> float:
    return round((part / whole) * 100, 2) if whole else 0.0


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_active_for_year(county: dict[str, Any], year: int) -> bool:
    valid_from = county.get("valid_from_year")
    valid_to = county.get("valid_to_year")
    if isinstance(valid_from, int) and year < valid_from:
        return False
    if isinstance(valid_to, int) and year > valid_to:
        return False
    return True


def build_coverage(summary: dict[str, Any]) -> dict[str, Any]:
    years = [int(year) for year in summary.get("years", [])]
    counties = summary.get("counties", [])

    year_reports: list[dict[str, Any]] = []
    for year in years:
        year_key = str(year)
        present_by_state: dict[str, int] = defaultdict(int)
        states: dict[str, dict[str, Any]] = {}
        counties_with_results = 0
        active_counties = 0

        for county in counties:
            if not is_active_for_year(county, year):
                continue
            state_po = str(county["state_po"])
            state = states.setdefault(
                state_po,
                {
                    "state_po": state_po,
                    "state": county.get("state") or state_po,
                    "county_count": 0,
                },
            )
            state["county_count"] += 1
            active_counties += 1
            if year_key not in county.get("results", {}):
                continue
            counties_with_results += 1
            present_by_state[str(county["state_po"])] += 1

        missing_by_state: list[dict[str, Any]] = []
        complete_states = 0
        for state_po, state in states.items():
            total = int(state["county_count"])
            present = present_by_state.get(state_po, 0)
            missing = total - present
            if missing == 0:
                complete_states += 1
            if missing:
                missing_by_state.append(
                    {
                        "state_po": state_po,
                        "state": state["state"],
                        "counties_with_results": present,
                        "county_count": total,
                        "missing_counties": missing,
                        "coverage_pct": pct(present, total),
                    }
                )

        missing_by_state.sort(key=lambda item: (-int(item["missing_counties"]), str(item["state_po"])))
        year_reports.append(
            {
                "year": year,
                "states_with_results": len(present_by_state),
                "states_complete": complete_states,
                "state_count": len(states),
                "counties_with_results": counties_with_results,
                "county_count": active_counties,
                "missing_counties": active_counties - counties_with_results,
                "coverage_pct": pct(counties_with_results, active_counties),
                "missing_by_state": missing_by_state,
            }
        )

    return {
        "source": {
            "name": summary.get("source", {}).get("name"),
            "summary_path": str(SUMMARY_PATH),
            "note": "Coverage is derived from county/year rows present in the generated county presidential summary, excluding rows marked inactive for a given year.",
        },
        "years": year_reports,
    }


def main() -> int:
    summary = load_summary(ROOT_DIR / SUMMARY_PATH)
    coverage = build_coverage(summary)
    output_path = ROOT_DIR / COVERAGE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(coverage, separators=(",", ":")), encoding="utf-8")

    latest = coverage["years"][-1] if coverage["years"] else None
    if latest:
        print(
            f"Wrote {COVERAGE_PATH} through {latest['year']}: "
            f"{latest['counties_with_results']}/{latest['county_count']} counties covered."
        )
    else:
        print(f"Wrote {COVERAGE_PATH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
