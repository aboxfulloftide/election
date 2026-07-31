#!/usr/bin/env python3
"""Generate normalized North Carolina federal/state contest summaries."""

from __future__ import annotations

import csv
import io
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any
from zipfile import ZipFile

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/north-carolina"
OUTPUT_PATH = ROOT_DIR / "public/results/north-carolina-statewide-summary.json"

SOURCES = {
    2020: ("results_pct_20201103.zip", "https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2020_11_03/results_pct_20201103.zip"),
    2024: ("results_pct_20241105.zip", "https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2024_11_05/results_pct_20241105.zip"),
}

PARTY_MAP = {
    "DEM": "DEMOCRAT",
    "REP": "REPUBLICAN",
    "LIB": "LIBERTARIAN",
    "GRE": "GREEN",
    "CST": "CONSTITUTION",
}


def int_value(value: str) -> int:
    return int((value or "0").replace(",", "").strip() or 0)


def office_for_contest(name: str) -> tuple[str, int | None, str | None] | None:
    normalized = name.strip().upper()
    if normalized == "US PRESIDENT":
        return "President", None, None
    if normalized == "US SENATE":
        return "U.S. Senate", None, None
    if normalized == "NC GOVERNOR":
        return "Governor", None, None
    patterns = (
        (r"US HOUSE OF REPRESENTATIVES DISTRICT (\d+)", "U.S. House", "Congressional"),
        (r"NC STATE SENATE DISTRICT (\d+)", "State Senate", "State Senate"),
        (r"NC HOUSE OF REPRESENTATIVES DISTRICT (\d+)", "State House", "State House"),
    )
    for pattern, office, label in patterns:
        match = re.fullmatch(pattern, normalized)
        if match:
            district = int(match.group(1))
            return office, district, f"{district} {label} District"
    return None


def parse_source(year: int, filename: str, source_url: str) -> dict[str, Any]:
    path = RAW_DIR / filename
    if not path.exists():
        raise RuntimeError(f"Missing North Carolina source: {path.relative_to(ROOT_DIR)}")
    with ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.endswith(".txt")]
        if len(members) != 1:
            raise RuntimeError(f"Expected one result text file in {filename}, found {len(members)}")
        text = archive.read(members[0]).decode("utf-8-sig", errors="replace")

    totals: dict[tuple[str, int | None], dict[tuple[str, str], int]] = defaultdict(lambda: defaultdict(int))
    contests: dict[tuple[str, int | None], str] = {}
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    required = {"Contest Name", "Choice", "Choice Party", "Total Votes", "County"}
    if not required <= set(reader.fieldnames or []):
        raise RuntimeError(f"North Carolina {year} source is missing required columns")
    for row in reader:
        parsed = office_for_contest(row["Contest Name"])
        if parsed is None:
            continue
        office, district, district_label = parsed
        key = (office, district)
        candidate = row["Choice"].strip()
        if not candidate:
            continue
        party = PARTY_MAP.get(row["Choice Party"].strip().upper(), "OTHER")
        totals[key][(candidate, party)] += int_value(row["Total Votes"])
        contests[key] = district_label or office

    output_contests = []
    for contest_id, ((office, district), candidate_totals) in enumerate(sorted(totals.items(), key=lambda item: (item[0][0], item[0][1] or 0)), start=1):
        candidates = [
            {"candidate": candidate, "party": party, "votes": votes}
            for (candidate, party), votes in candidate_totals.items()
        ]
        candidates.sort(key=lambda item: (-item["votes"], item["candidate"]))
        if not candidates:
            continue
        contest = {
            "contest_id": contest_id,
            "office": office,
            "name": f"North Carolina {year} {contests[(office, district)]}",
            "state": "North Carolina",
            "state_po": "NC",
            "year": year,
            "election_date": f"11/03/{year}" if year == 2020 else f"11/05/{year}",
            "source_url": source_url,
            "source_format": "ncsbe-precinct-results-txt",
            "quality_grade": "A",
            "total_votes": sum(candidate["votes"] for candidate in candidates),
            "winner": candidates[0],
            "margin_votes": candidates[0]["votes"] - candidates[1]["votes"] if len(candidates) > 1 else 0,
            "candidates": candidates,
        }
        if district is not None:
            contest["district_number"] = district
            contest["district_label"] = contests[(office, district)]
        output_contests.append(contest)
    return {
        "source": {
            "name": "North Carolina State Board of Elections official precinct results",
            "url": source_url,
            "official": True,
            "quality_grade": "A",
        },
        "election": {"state": "North Carolina", "state_po": "NC", "year": year, "name": f"North Carolina {year} General Election"},
        "contests": output_contests,
    }


def main() -> int:
    elections = [parse_source(year, filename, url) for year, (filename, url) in SOURCES.items()]
    summary = {
        "source": {"name": "North Carolina State Board of Elections", "url": "https://www.ncsbe.gov/results-data/election-results/historical-election-results-data", "official": True, "quality_grade": "A"},
        "state_po": "NC",
        "elections": elections,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT_DIR)} with {sum(len(e['contests']) for e in elections)} contests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
