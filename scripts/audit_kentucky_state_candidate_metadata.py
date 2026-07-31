#!/usr/bin/env python3
"""Report which certified Kentucky 2022 legislative districts have candidate metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR
from parse_kentucky_certified import extract_state_candidate_headers


SUMMARY_PATH = ROOT_DIR / "public/results/kentucky-statewide-summary.json"
CERTIFIED_PATH = ROOT_DIR / "data/raw/official/kentucky/2022_certified_senate_reconciliation.json"
OUTPUT_PATH = ROOT_DIR / "public/results/kentucky-2022-state-candidate-readiness.json"


def build_report(summary: dict[str, Any], certified: dict[str, Any], certified_text: str) -> dict[str, Any]:
    report: dict[str, Any] = {"state_po": "KY", "year": 2022, "offices": {}}
    for office, key in (("State Senate", "state_senate_county_rows"), ("State House", "state_house_county_rows")):
        contests = {
            contest["district_number"]: contest
            for election in summary["elections"]
            if election["election"]["year"] == 2022
            for contest in election["contests"]
            if contest["office"] == office
        }
        certified_rows = {row["district"]: row for row in certified[key]}
        headers = {row["district"]: row for row in extract_state_candidate_headers(certified_text, office)}
        lanes = []
        for district in sorted(certified_rows):
            existing = contests.get(district)
            width = len(certified_rows[district].get("summed_columns", []))
            candidate_count = len(existing.get("candidates", [])) if existing else 0
            extracted_candidates = headers.get(district, {}).get("candidates", [])
            extracted_count = len(extracted_candidates)
            lanes.append({
                "district": district,
                "candidate_metadata": "certified_header" if extracted_count == width else "recap_summary" if existing and candidate_count == width else "needs_header_extraction",
                "candidate_count": candidate_count,
                "extracted_candidates": extracted_candidates,
                "certified_columns": width,
                "certified_totals_reconciled": certified_rows[district].get("all_columns_match") is True,
            })
        report["offices"][office] = {
            "expected_districts": len(certified_rows),
            "candidate_metadata_ready": sum(item["candidate_metadata"] in {"recap_summary", "certified_header"} for item in lanes),
            "certified_header_ready": sum(item["candidate_metadata"] == "certified_header" for item in lanes),
            "recap_metadata_ready": sum(item["candidate_metadata"] == "recap_summary" for item in lanes),
            "header_extraction_needed": sum(item["candidate_metadata"] == "needs_header_extraction" for item in lanes),
            "districts": lanes,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    certified = json.loads(CERTIFIED_PATH.read_text(encoding="utf-8"))
    certified_text = (CERTIFIED_PATH.parent / "2022_certified_general_election_results_ocr.txt").read_text(encoding="utf-8")
    report = build_report(summary, certified, certified_text)
    output = args.output if args.output.is_absolute() else ROOT_DIR / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {output.relative_to(ROOT_DIR)}")
    for office, result in report["offices"].items():
        print(
            f"{office}: {result['candidate_metadata_ready']} candidate metadata ready "
            f"({result['certified_header_ready']} certified headers), "
            f"{result['header_extraction_needed']} need header extraction"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
