#!/usr/bin/env python3
"""Normalize Georgia's official 2024 contest-comparison PDF."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR
from georgia_official_config import SOURCE_NAME, SOURCE_URL


INPUT_PATH = ROOT_DIR / "data/raw/official/georgia/contest_results_comparison_with_jurisdiction_details_0.pdf"
OUTPUT_PATH = ROOT_DIR / "public/results/georgia-2024-official-contests.json"
SECTION_RE = re.compile(r"^(President of the US|US House of Representatives - District (\d+)|State Senate - District (\d+)|State House of Representatives - District (\d+))(?:/.*)?$")
CHOICE_RE = re.compile(r"^(.*?)\s+(?:\(I\)\s+)?(?:\((Rep|Dem|Lib|Ind|Grn)\)\s+)?([\d,]+)\s+([\d,]+)\s+(-?[\d,]+)\s*$", re.I)
PARTIES = {"DEM": "DEMOCRAT", "REP": "REPUBLICAN", "LIB": "LIBERTARIAN", "IND": "INDEPENDENT", "GRN": "GREEN"}


def parse_number(value: str) -> int:
    return int(value.replace(",", ""))


def parse_pdf(path: Path) -> tuple[dict[tuple[str, int | None], dict[tuple[str, str], int]], dict[tuple[str, int | None], set[str]]]:
    text = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True, errors="replace").stdout
    values: dict[tuple[str, int | None], dict[tuple[str, str], int]] = defaultdict(lambda: defaultdict(int))
    counties: dict[tuple[str, int | None], set[str]] = defaultdict(set)
    current: tuple[str, int | None] | None = None
    county = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        section = SECTION_RE.match(line)
        if section:
            if section.group(1) == "President of the US":
                current = ("President", None)
            elif section.group(2):
                current = ("U.S. House", int(section.group(2)))
            elif section.group(3):
                current = ("State Senate", int(section.group(3)))
            else:
                current = ("State House", int(section.group(4)))
            county = ""
            continue
        if current is None or not line or line.startswith(("Georgia ", "General Election", "November ", "DetailName", "Ballots Cast", "Last Updated")):
            continue
        choice = CHOICE_RE.match(line)
        if choice:
            candidate = re.sub(r"\s*\(I\)\s*", " ", choice.group(1), flags=re.I)
            candidate = re.sub(r"\s+", " ", candidate).strip()
            party = PARTIES.get(choice.group(2).upper(), "OTHER") if choice.group(2) else "OTHER"
            values[current][(candidate, party)] += parse_number(choice.group(4))
            counties[current].add(county)
            continue
        if line.endswith(" County"):
            county = line.removesuffix(" County").strip().upper()
    if not values:
        raise RuntimeError(f"No target contests parsed from {path}")
    return values, counties


def build_summary(path: Path) -> dict[str, Any]:
    values, counties = parse_pdf(path)
    contests = []
    for contest_id, ((office, district), candidate_values) in enumerate(sorted(values.items(), key=lambda item: (item[0][0], item[0][1] or 0)), 1):
        candidates = [{"candidate": name, "party": party, "votes": votes} for (name, party), votes in candidate_values.items()]
        candidates.sort(key=lambda item: (-item["votes"], item["candidate"]))
        contest = {
            "contest_id": contest_id,
            "office": office,
            "name": f"Georgia 2024 {office}" if district is None else f"Georgia 2024 {office} District {district}",
            "state": "Georgia",
            "state_po": "GA",
            "year": 2024,
            "source_format": "ga-sos-contest-comparison-pdf",
            "quality_grade": "B",
            "total_votes": sum(item["votes"] for item in candidates),
            "winner": candidates[0],
            "margin_votes": candidates[0]["votes"] - (candidates[1]["votes"] if len(candidates) > 1 else candidates[0]["votes"]),
            "candidates": candidates,
            "source_files": len(counties[(office, district)]),
            "official": True,
            "source_url": "https://sos.ga.gov/sites/default/files/2024-11/contest_results_comparison_with_jurisdiction_details_0.pdf",
        }
        if district is not None:
            contest["district_number"] = district
            contest["district_label"] = f"{district} {office} District"
        contests.append(contest)
    return {
        "source": {"name": SOURCE_NAME, "url": SOURCE_URL, "official": True, "quality_grade": "B", "completeness": "partial", "notes": "The 2024 official PDF contains no regular U.S. Senate contest."},
        "state_po": "GA",
        "elections": [{"election": {"state": "Georgia", "state_po": "GA", "year": 2024}, "contests": contests}],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT_DIR / args.input
    output_path = args.output if args.output.is_absolute() else ROOT_DIR / args.output
    summary = build_summary(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {len(summary['elections'][0]['contests'])} contests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
