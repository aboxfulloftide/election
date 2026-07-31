#!/usr/bin/env python3
"""Validate normalized Kentucky contest totals and known source coverage."""

from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT_DIR / "public/results/kentucky-statewide-summary.json"
ALLOWED_OFFICES = {"President", "U.S. Senate", "U.S. House", "State Senate", "State House"}


def validate_summary(summary: dict) -> list[str]:
    failures: list[str] = []
    if summary.get("source", {}).get("completeness") != "partial":
        failures.append("summary must remain marked partial until independent reconciliation is complete")
    contests = [contest for election in summary.get("elections", []) for contest in election.get("contests", [])]
    if not contests:
        failures.append("summary contains no contests")

    for contest in contests:
        label = f"{contest.get('year')} {contest.get('office')} {contest.get('district_number', 'statewide')}"
        if contest.get("office") not in ALLOWED_OFFICES:
            failures.append(f"{label}: unsupported office")
        candidates = contest.get("candidates", [])
        votes = [candidate.get("votes", 0) for candidate in candidates]
        if not candidates or any(not isinstance(value, int) or value < 0 for value in votes):
            failures.append(f"{label}: candidate vote totals are invalid")
            continue
        if sum(votes) != contest.get("total_votes"):
            failures.append(f"{label}: candidate votes do not reconcile to total_votes")
        if contest.get("winner", {}).get("votes") != max(votes):
            failures.append(f"{label}: winner does not have the highest candidate total")
        sorted_votes = sorted(votes, reverse=True)
        expected_margin = sorted_votes[0] - (sorted_votes[1] if len(sorted_votes) > 1 else sorted_votes[0])
        if contest.get("margin_votes") != expected_margin:
            failures.append(f"{label}: margin does not reconcile")
        if not isinstance(contest.get("source_files"), int) or contest["source_files"] < 1:
            failures.append(f"{label}: source_files must be a positive count")

    by_key = {(contest.get("year"), contest.get("office"), contest.get("district_number")): contest for contest in contests}
    if by_key.get((2022, "U.S. Senate", None), {}).get("source_files") != 49:
        failures.append("2022 U.S. Senate must have 49 contributing reports")
    if by_key.get((2024, "President", None), {}).get("source_files") != 119:
        failures.append("2024 President must have 119 contributing reports")
    return failures


def main() -> int:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    failures = validate_summary(summary)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Kentucky statewide contest checks passed; source remains partial.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
