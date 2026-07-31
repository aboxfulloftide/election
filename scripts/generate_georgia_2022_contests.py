#!/usr/bin/env python3
"""Normalize Georgia 2022 official county summary ZIPs into contest totals."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR
from georgia_official_config import SOURCE_NAME, SOURCE_URL, GEORGIA_CONTEST_SOURCES, raw_path
from fetch_results import parse_int


PARTIES = {"DEM": "DEMOCRAT", "REP": "REPUBLICAN", "LIB": "LIBERTARIAN", "IND": "INDEPENDENT", "GRN": "GREEN"}
OFFICES = {
    "PRESIDENT": "President",
    "US SENATE": "U.S. Senate",
    "U.S. SENATE": "U.S. Senate",
    "GOVERNOR": "Governor",
    "US HOUSE": "U.S. House",
    "U.S. HOUSE": "U.S. House",
    "STATE SENATE": "State Senate",
    "STATE HOUSE": "State House",
}
DISTRICT_RE = re.compile(r"(?:DISTRICT|DIST)\s+(\d+)", re.I)
PARTY_RE = re.compile(r"\((DEM|REP|LIB|IND|GRN)\)", re.I)


def normalize_contest(contest_name: str) -> tuple[str, int | None] | None:
    base = re.sub(r"\s*\(Vote For \d+\)\s*$", "", contest_name, flags=re.I).strip()
    upper = re.sub(r"\s+", " ", base.upper())
    office_key = next((key for key in OFFICES if upper.startswith(key)), None)
    if office_key is None:
        return None
    district = int(DISTRICT_RE.search(base).group(1)) if DISTRICT_RE.search(base) else None
    return OFFICES[office_key], district


def parse_choice(choice_name: str) -> tuple[str, str]:
    match = PARTY_RE.search(choice_name)
    party = PARTIES.get(match.group(1).upper(), "OTHER") if match else "OTHER"
    candidate = re.sub(r"\s*\((?:I|DEM|REP|LIB|IND|GRN)\)\s*", " ", choice_name, flags=re.I)
    return re.sub(r"\s+", " ", candidate).strip(), party


def county_name(member_name: str) -> str:
    name = Path(member_name).name
    return re.sub(r"_\d+_\d+-summary\.zip$", "", name).replace("_", " ").upper()


def parse_official_zip(path: Path) -> dict[tuple[str, int | None], dict[tuple[str, str], int]]:
    contests: dict[tuple[str, int | None], dict[tuple[str, str], int]] = defaultdict(lambda: defaultdict(int))
    county_counts: dict[tuple[str, int | None], set[str]] = defaultdict(set)
    with zipfile.ZipFile(path) as outer:
        members = [name for name in outer.namelist() if name.endswith("-summary.zip")]
        if not members:
            raise RuntimeError(f"No county summary ZIPs found in {path}")
        for member in members:
            county = county_name(member)
            with zipfile.ZipFile(io.BytesIO(outer.read(member))) as inner:
                csv_names = [name for name in inner.namelist() if name.endswith(".csv")]
                if len(csv_names) != 1:
                    raise RuntimeError(f"Expected one summary CSV in {member}, found {len(csv_names)}")
                text = inner.read(csv_names[0]).decode("utf-8-sig", errors="replace")
            for row in csv.DictReader(io.StringIO(text)):
                contest = normalize_contest(row.get("contest name", ""))
                if contest is None:
                    continue
                candidate, party = parse_choice(row.get("choice name", ""))
                if not candidate:
                    continue
                contests[contest][(candidate, party)] += parse_int(row.get("total votes"))
                county_counts[contest].add(county)
    parse_official_zip.counties = county_counts
    return contests


def build_summary(path: Path) -> dict[str, Any]:
    parsed = parse_official_zip(path)
    contests = []
    for contest_id, ((office, district), values) in enumerate(sorted(parsed.items(), key=lambda item: (item[0][0], item[0][1] or 0)), 1):
        candidates = [{"candidate": name, "party": party, "votes": votes} for (name, party), votes in values.items()]
        candidates.sort(key=lambda item: (-item["votes"], item["candidate"]))
        if not candidates:
            continue
        contest = {
            "contest_id": contest_id,
            "office": office,
            "name": f"Georgia 2022 {office}" if district is None else f"Georgia 2022 {office} District {district}",
            "state": "Georgia",
            "state_po": "GA",
            "year": 2022,
            "source_format": "ga-sos-county-summary-zip",
            "quality_grade": "A",
            "total_votes": sum(item["votes"] for item in candidates),
            "winner": candidates[0],
            "margin_votes": candidates[0]["votes"] - (candidates[1]["votes"] if len(candidates) > 1 else candidates[0]["votes"]),
            "candidates": candidates,
            "source_files": len(getattr(parse_official_zip, "counties", {}).get((office, district), set())),
            "official": True,
            "source_url": GEORGIA_CONTEST_SOURCES[2022].url,
        }
        if district is not None:
            contest["district_number"] = district
            contest["district_label"] = f"{district} {office} District"
        contests.append(contest)
    return {
        "source": {"name": SOURCE_NAME, "url": SOURCE_URL, "official": True, "quality_grade": "A", "completeness": "partial"},
        "state_po": "GA",
        "elections": [{"election": {"state": "Georgia", "state_po": "GA", "year": 2022}, "contests": contests}],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT_DIR / raw_path(GEORGIA_CONTEST_SOURCES[2022]))
    parser.add_argument("--output", type=Path, default=ROOT_DIR / "public/results/georgia-2022-official-contests.json")
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT_DIR / args.input
    output_path = args.output if args.output.is_absolute() else ROOT_DIR / args.output
    summary = build_summary(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {len(summary['elections'][0]['contests'])} contests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
