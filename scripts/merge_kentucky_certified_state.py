#!/usr/bin/env python3
"""Promote reconciled certified Kentucky 2022 legislative contests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR
from parse_kentucky_certified import extract_state_candidate_headers, parse_state_legislative_rows


OCR_PATH = ROOT_DIR / "data/raw/official/kentucky/2022_certified_general_election_results_ocr.txt"
SUMMARY_PATH = ROOT_DIR / "public/results/kentucky-statewide-summary.json"
SOURCE_URL = "https://elect.ky.gov/results/2020-2029/Pages/2022.aspx"


def build_contests(text: str, office: str) -> list[dict[str, Any]]:
    rows = {row["district"]: row for row in parse_state_legislative_rows(text, office)}
    headers = {row["district"]: row for row in extract_state_candidate_headers(text, office)}
    if set(rows) != set(headers) or len(rows) != (19 if office == "State Senate" else 100):
        raise RuntimeError(f"{office} certified district/header coverage is incomplete")
    contests = []
    for district in sorted(rows):
        row = rows[district]
        header = headers[district]
        candidates = [
            {"candidate": candidate["candidate"], "party": candidate["party"], "votes": row["summed_columns"][index]}
            for index, candidate in enumerate(header["candidates"])
        ]
        if len(candidates) != len(row["summed_columns"]) or not row["all_columns_match"]:
            raise RuntimeError(f"{office} district {district} candidate columns do not reconcile")
        candidates.sort(key=lambda item: (-item["votes"], item["candidate"]))
        contests.append({
            "office": office,
            "district_number": district,
            "name": f"Kentucky 2022 {district} {office} District",
            "state": "Kentucky",
            "state_po": "KY",
            "year": 2022,
            "source_format": "ky-certified-pdf-ocr",
            "quality_grade": "B",
            "total_votes": sum(item["votes"] for item in candidates),
            "winner": candidates[0],
            "margin_votes": candidates[0]["votes"] - (candidates[1]["votes"] if len(candidates) > 1 else candidates[0]["votes"]),
            "candidates": candidates,
            "source_files": 1,
            "source_url": SOURCE_URL,
            "official": True,
            "certified_reconciled": True,
            "county_rows": row["row_count"],
            "district_label": f"{district} {office} District",
        })
    return contests


def merge(summary: dict[str, Any], text: str) -> dict[str, int]:
    replacements = {office: {contest["district_number"]: contest for contest in build_contests(text, office)} for office in ("State Senate", "State House")}
    next_id = max((contest.get("contest_id", 0) for election in summary["elections"] for contest in election["contests"]), default=0) + 1
    counts = {office: 0 for office in replacements}
    for election in summary["elections"]:
        if election["election"]["year"] != 2022:
            continue
        existing = {(contest.get("office"), contest.get("district_number")): contest for contest in election["contests"]}
        for office, districts in replacements.items():
            for district, contest in districts.items():
                previous = existing.get((office, district))
                contest["contest_id"] = previous.get("contest_id", next_id) if previous else next_id
                if not previous:
                    next_id += 1
                existing[(office, district)] = contest
                counts[office] += 1
        election["contests"] = sorted(existing.values(), key=lambda contest: contest.get("contest_id", 0))
    summary["source"]["certified_state_overrides"] = ["2022 State Senate", "2022 State House"]
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=OCR_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT_DIR / args.input
    summary_path = args.summary if args.summary.is_absolute() else ROOT_DIR / args.summary
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    counts = merge(summary, input_path.read_text(encoding="utf-8"))
    summary_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(f"Promoted certified Kentucky contests: {counts['State Senate']} State Senate, {counts['State House']} State House.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
