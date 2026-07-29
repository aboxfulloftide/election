#!/usr/bin/env python3
"""Merge official Virginia county/locality presidential rows into the summary."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR
from fetch_results import SUMMARY_PATH, parse_int
from virginia_presidential_config import VIRGINIA_PRESIDENTIAL_SOURCES, SOURCE_NAME, SOURCE_URL, raw_path


PARTY_MAP = {
    "DEMOCRATIC": "DEMOCRAT",
    "REPUBLICAN": "REPUBLICAN",
    "LIBERTARIAN": "LIBERTARIAN",
    "GREEN": "GREEN",
}


def sorted_parties(parties: dict[str, int]) -> list[tuple[str, int]]:
    order = {"DEMOCRAT": 0, "REPUBLICAN": 1, "LIBERTARIAN": 2, "GREEN": 3, "OTHER": 4}
    return sorted(parties.items(), key=lambda item: (-item[1], order.get(item[0], 99), item[0]))


def party_code(value: str) -> str:
    return PARTY_MAP.get(value.strip().upper(), "OTHER")


def locality_key(locality: str) -> tuple[str, str]:
    name = locality.strip().upper()
    if name.endswith(" COUNTY"):
        return (name.removesuffix(" COUNTY"), "county")
    if name.endswith(" CITY"):
        return (name, "city")
    return (name, "other")


def county_key(county: dict[str, Any]) -> tuple[str, str]:
    fips = str(county.get("fips", ""))
    if fips.startswith("51") and len(fips) >= 3 and fips[2] in {"5", "6", "7", "8", "9"}:
        locality_type = "city"
    else:
        locality_type = "county"
    return (str(county["county_name"]).strip().upper(), locality_type)


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


def candidate_columns(header: list[str]) -> range:
    for index, value in enumerate(header):
        if value.strip().upper() == "TOTAL VOTES CAST":
            return range(2, index)
    raise RuntimeError("Virginia CSV is missing a Total Votes Cast column")


def parse_official_csv(path: Path) -> dict[tuple[str, str], dict[str, int]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    if len(rows) < 3:
        raise RuntimeError(f"Virginia CSV is too short: {path}")

    headers = rows[0]
    parties = rows[1]
    columns = candidate_columns(headers)
    localities: dict[tuple[str, str], dict[str, int]] = {}

    for row in rows[2:]:
        if not row or row[0] != "Locality":
            continue
        key = locality_key(row[1])
        party_totals: dict[str, int] = defaultdict(int)
        for column in columns:
            party = party_code(parties[column] if column < len(parties) else "")
            party_totals[party] += parse_int(row[column] if column < len(row) else "")
        localities[key] = dict(party_totals)

    return localities


def merge_official_rows(summary: dict[str, Any]) -> dict[str, int]:
    va_counties = {
        county_key(county): county for county in summary.get("counties", []) if county.get("state_po") == "VA"
    }
    stats = {
        "replaced": 0,
        "missing_localities": 0,
        "extra_localities": 0,
    }

    for year, source in VIRGINIA_PRESIDENTIAL_SOURCES.items():
        path = ROOT_DIR / raw_path(source)
        if not path.exists():
            raise RuntimeError(f"Missing official Virginia file: {path.relative_to(ROOT_DIR)}. Run npm run data:official:va:download first.")
        official_rows = parse_official_csv(path)
        stats["missing_localities"] += len(set(va_counties) - set(official_rows))
        stats["extra_localities"] += len(set(official_rows) - set(va_counties))

        for key in sorted(set(va_counties) & set(official_rows)):
            county = va_counties[key]
            county.setdefault("results", {})[str(year)] = build_result(official_rows[key], source.contest_url)
            stats["replaced"] += 1

    source = summary.setdefault("source", {})
    official_sources = source.setdefault("official_state_sources", [])
    record = {
        "name": SOURCE_NAME,
        "url": SOURCE_URL,
        "state_po": "VA",
        "years": sorted(VIRGINIA_PRESIDENTIAL_SOURCES),
        "quality_grade": "A",
        "notes": "Official Virginia historical election CSV downloads aggregated by locality and used before non-authoritative supplemental CSV rows.",
    }
    official_sources[:] = [item for item in official_sources if item.get("name") != SOURCE_NAME or item.get("state_po") != "VA"]
    official_sources.append(record)
    return stats


def main() -> int:
    output_path = ROOT_DIR / SUMMARY_PATH
    summary = json.loads(output_path.read_text(encoding="utf-8"))
    stats = merge_official_rows(summary)
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(
        "Merged official Virginia presidential returns: "
        f"{stats['replaced']} county-year rows replaced, "
        f"{stats['missing_localities']} missing official localities, "
        f"{stats['extra_localities']} unmatched official localities."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
