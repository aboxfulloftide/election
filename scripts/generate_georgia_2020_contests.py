#!/usr/bin/env python3
"""Normalize Georgia's official 2020 full county summary archive."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR
from fetch_results import parse_int
from georgia_official_config import SOURCE_NAME, SOURCE_URL, GEORGIA_CONTEST_SOURCES, raw_path


PARTIES = {"DEM": "DEMOCRAT", "REP": "REPUBLICAN", "LIB": "LIBERTARIAN", "IND": "INDEPENDENT", "GRN": "GREEN"}
PARTY_RE = re.compile(r"\((DEM|REP|LIB|IND|GRN)\)", re.I)
DISTRICT_RE = re.compile(r"(?:DISTRICT|DIST)\s+(\d+)", re.I)


def normalize_contest(name: str) -> tuple[str, int | None, str] | None:
    base = re.sub(r"\s*\(Vote For \d+\)\s*$", "", name, flags=re.I).strip()
    upper = re.sub(r"\s+", " ", base.upper())
    if upper.startswith("PRESIDENT OF THE UNITED STATES"):
        return "President", None, "President"
    if upper.startswith("US SENATE") or upper.startswith("U.S. SENATE"):
        label = "Special" if "SPECIAL" in upper else "Regular"
        return "U.S. Senate", None, label
    if upper.startswith("US HOUSE") or upper.startswith("U.S. HOUSE"):
        office = "U.S. House"
    elif upper.startswith("STATE SENATE"):
        office = "State Senate"
    elif upper.startswith("STATE HOUSE"):
        office = "State House"
    else:
        return None
    match = DISTRICT_RE.search(base)
    return office, int(match.group(1)) if match else None, office


def parse_choice(name: str) -> tuple[str, str]:
    match = PARTY_RE.search(name)
    party = PARTIES.get(match.group(1).upper(), "OTHER") if match else "OTHER"
    candidate = re.sub(r"\s*\((?:I|DEM|REP|LIB|IND|GRN)\)\s*", " ", name, flags=re.I)
    return re.sub(r"\s+", " ", candidate).strip(), party


def county_name(member: str) -> str:
    return re.sub(r"_\d+_\d+-summary\.zip$", "", Path(member).name).replace("_", " ").upper()


def parse_archive(path: Path) -> tuple[dict[tuple[str, int | None, str], dict[tuple[str, str], int]], dict[tuple[str, int | None, str], set[str]]]:
    values: dict[tuple[str, int | None, str], dict[tuple[str, str], int]] = defaultdict(lambda: defaultdict(int))
    counties: dict[tuple[str, int | None, str], set[str]] = defaultdict(set)
    with zipfile.ZipFile(path) as outer:
        members = [name for name in outer.namelist() if name.endswith("-summary.zip")]
        if len(members) != 159:
            raise RuntimeError(f"Expected 159 Georgia county summary ZIPs, found {len(members)}")
        for member in members:
            with zipfile.ZipFile(io.BytesIO(outer.read(member))) as inner:
                csv_name = next(name for name in inner.namelist() if name.endswith(".csv"))
                rows = csv.DictReader(io.StringIO(inner.read(csv_name).decode("utf-8-sig", errors="replace")))
                for row in rows:
                    contest = normalize_contest(row.get("contest name", ""))
                    if contest is None:
                        continue
                    candidate, party = parse_choice(row.get("choice name", ""))
                    if candidate:
                        values[contest][(candidate, party)] += parse_int(row.get("total votes"))
                        counties[contest].add(county_name(member))
    return values, counties


def build_summary(path: Path) -> dict[str, Any]:
    values, counties = parse_archive(path)
    contests = []
    for contest_id, ((office, district, variant), candidate_values) in enumerate(sorted(values.items(), key=lambda item: (item[0][0], item[0][1] or 0, item[0][2])), 1):
        candidates = [{"candidate": name, "party": party, "votes": votes} for (name, party), votes in candidate_values.items()]
        candidates.sort(key=lambda item: (-item["votes"], item["candidate"]))
        contest_name = f"Georgia 2020 {variant}" if district is None else (f"Georgia 2020 {office} District {district}" if variant == office else f"Georgia 2020 {variant} {office}")
        contest = {
            "contest_id": contest_id,
            "office": office,
            "name": contest_name,
            "state": "Georgia", "state_po": "GA", "year": 2020,
            "source_format": "ga-sos-county-summary-zip", "quality_grade": "A",
            "total_votes": sum(item["votes"] for item in candidates), "winner": candidates[0],
            "margin_votes": candidates[0]["votes"] - (candidates[1]["votes"] if len(candidates) > 1 else candidates[0]["votes"]),
            "candidates": candidates, "source_files": len(counties[(office, district, variant)]),
            "official": True, "source_url": GEORGIA_CONTEST_SOURCES[2020].url,
        }
        if district is not None:
            contest["district_number"] = district
            contest["district_label"] = f"{district} {office} District"
        contests.append(contest)
    return {"source": {"name": SOURCE_NAME, "url": SOURCE_URL, "official": True, "quality_grade": "A", "completeness": "partial"}, "state_po": "GA", "elections": [{"election": {"state": "Georgia", "state_po": "GA", "year": 2020}, "contests": contests}]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT_DIR / raw_path(GEORGIA_CONTEST_SOURCES[2020]))
    parser.add_argument("--output", type=Path, default=ROOT_DIR / "public/results/georgia-2020-official-contests.json")
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
