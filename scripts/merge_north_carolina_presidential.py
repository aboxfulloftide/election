#!/usr/bin/env python3
"""Merge official North Carolina county presidential rows into the summary."""

from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR
from fetch_results import SUMMARY_PATH, parse_int
from north_carolina_presidential_config import NORTH_CAROLINA_PRESIDENTIAL_SOURCES, SOURCE_NAME, SOURCE_URL, raw_path


PARTY_MAP = {
    "DEM": "DEMOCRAT",
    "REP": "REPUBLICAN",
    "LIB": "LIBERTARIAN",
    "GRE": "GREEN",
}


def sorted_parties(parties: dict[str, int]) -> list[tuple[str, int]]:
    order = {"DEMOCRAT": 0, "REPUBLICAN": 1, "LIBERTARIAN": 2, "GREEN": 3, "OTHER": 4}
    return sorted(parties.items(), key=lambda item: (-item[1], order.get(item[0], 99), item[0]))


def party_code(value: str) -> str:
    return PARTY_MAP.get(value.strip().upper(), "OTHER")


def build_result(parties: dict[str, int], source_url: str) -> dict[str, Any]:
    total_votes = sum(parties.values())
    ordered = sorted_parties(parties)
    winner_party, winner_votes = ordered[0]
    runner_up_votes = ordered[1][1] if len(ordered) > 1 else 0
    dem_votes = parties.get("DEMOCRAT", 0)
    rep_votes = parties.get("REPUBLICAN", 0)
    margin_votes = winner_votes - runner_up_votes

    return {
        "totalvotes": total_votes,
        "parties": parties,
        "winner_party": winner_party,
        "winner_votes": winner_votes,
        "margin_votes": margin_votes,
        "margin_pct": round((margin_votes / total_votes) * 100, 2) if total_votes else 0,
        "dem_share": round((dem_votes / total_votes) * 100, 2) if total_votes else 0,
        "rep_share": round((rep_votes / total_votes) * 100, 2) if total_votes else 0,
        "two_party_margin": round(((dem_votes - rep_votes) / total_votes) * 100, 2) if total_votes else 0,
        "official": True,
        "source_name": SOURCE_NAME,
        "source_url": source_url,
        "quality_grade": "A",
    }


def parse_official_zip(path: Path) -> dict[str, dict[str, int]]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != 1:
            raise RuntimeError(f"Expected one results file in {path}, found {len(names)}")
        text = archive.read(names[0]).decode("utf-8-sig", errors="replace")

    counties: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in csv.DictReader(io.StringIO(text), delimiter="\t"):
        if row.get("Contest Name") != "US PRESIDENT":
            continue
        county_name = (row.get("County") or "").strip().upper()
        if not county_name:
            continue
        party = party_code(row.get("Choice Party") or "")
        counties[county_name][party] += parse_int(row.get("Total Votes"))
    return {county: dict(parties) for county, parties in counties.items()}


def merge_official_rows(summary: dict[str, Any]) -> dict[str, int]:
    nc_counties = {county["county_name"].upper(): county for county in summary.get("counties", []) if county.get("state_po") == "NC"}
    stats = {
        "replaced": 0,
        "missing_counties": 0,
        "extra_counties": 0,
    }

    for year, source in NORTH_CAROLINA_PRESIDENTIAL_SOURCES.items():
        path = ROOT_DIR / raw_path(source)
        if not path.exists():
            raise RuntimeError(f"Missing official North Carolina file: {path.relative_to(ROOT_DIR)}. Run npm run nc:presidential:download first.")
        official_rows = parse_official_zip(path)
        stats["missing_counties"] += len(set(nc_counties) - set(official_rows))
        stats["extra_counties"] += len(set(official_rows) - set(nc_counties))

        for county_name in sorted(set(nc_counties) & set(official_rows)):
            county = nc_counties[county_name]
            county.setdefault("results", {})[str(year)] = build_result(official_rows[county_name], source.url)
            stats["replaced"] += 1

    source = summary.setdefault("source", {})
    official_sources = source.setdefault("official_state_sources", [])
    record = {
        "name": SOURCE_NAME,
        "url": SOURCE_URL,
        "state_po": "NC",
        "years": sorted(NORTH_CAROLINA_PRESIDENTIAL_SOURCES),
        "quality_grade": "A",
        "notes": "Official North Carolina precinct results ZIPs aggregated to county presidential totals and used before non-authoritative supplemental CSV rows.",
    }
    official_sources[:] = [item for item in official_sources if item.get("name") != SOURCE_NAME or item.get("state_po") != "NC"]
    official_sources.append(record)
    return stats


def main() -> int:
    output_path = ROOT_DIR / SUMMARY_PATH
    summary = json.loads(output_path.read_text(encoding="utf-8"))
    stats = merge_official_rows(summary)
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(
        "Merged official North Carolina presidential returns: "
        f"{stats['replaced']} county-year rows replaced, "
        f"{stats['missing_counties']} missing official counties, "
        f"{stats['extra_counties']} unmatched official counties."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
