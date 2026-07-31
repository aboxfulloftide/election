#!/usr/bin/env python3
"""Validate normalized Virginia contest totals and contest coverage."""

from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT_DIR / "public/results/virginia-statewide-summary.json"
EXPECTED_YEARS = {2020, 2024}
EXPECTED_OFFICES = {"President", "U.S. Senate", "U.S. House"}


def validate_summary(summary: dict) -> list[str]:
    failures: list[str] = []
    contests = [contest for election in summary.get("elections", []) for contest in election.get("contests", [])]
    ids = [contest.get("contest_id") for contest in contests]
    if len(contests) != 26:
        failures.append(f"expected 26 contests, found {len(contests)}")
    if len(set(ids)) != len(ids):
        failures.append("contest IDs are not unique")
    years = {contest.get("year") for contest in contests}
    offices = {contest.get("office") for contest in contests}
    if years != EXPECTED_YEARS:
        failures.append(f"expected years {sorted(EXPECTED_YEARS)}, found {sorted(years)}")
    if offices != EXPECTED_OFFICES:
        failures.append(f"expected offices {sorted(EXPECTED_OFFICES)}, found {sorted(offices)}")

    for contest in contests:
        label = f"{contest.get('year')} {contest.get('office')} {contest.get('contest_id')}"
        candidates = contest.get("candidates", [])
        votes = [candidate.get("votes", 0) for candidate in candidates]
        total_votes = contest.get("total_votes")
        if not candidates or any(not isinstance(value, int) or value < 0 for value in votes):
            failures.append(f"{label}: candidate vote totals are invalid")
            continue
        if sum(votes) != total_votes:
            failures.append(f"{label}: candidate votes sum to {sum(votes)}, total is {total_votes}")
        winner = contest.get("winner", {})
        if winner.get("votes") != max(votes):
            failures.append(f"{label}: winner does not have the highest candidate total")
        sorted_votes = sorted(votes, reverse=True)
        expected_margin = sorted_votes[0] - (sorted_votes[1] if len(sorted_votes) > 1 else sorted_votes[0])
        if contest.get("margin_votes") != expected_margin:
            failures.append(f"{label}: margin is {contest.get('margin_votes')}, expected {expected_margin}")

    for year in EXPECTED_YEARS:
        year_contests = [contest for contest in contests if contest.get("year") == year]
        if len(year_contests) != 13:
            failures.append(f"{year}: expected 13 contests, found {len(year_contests)}")
        if len([contest for contest in year_contests if contest.get("office") == "U.S. House"]) != 11:
            failures.append(f"{year}: expected all 11 U.S. House districts")
    return failures


def main() -> int:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    failures = validate_summary(summary)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Virginia statewide contest checks passed for 26 official contests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
