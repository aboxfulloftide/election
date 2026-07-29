#!/usr/bin/env python3
"""Merge official Georgia county presidential rows into the summary."""

from __future__ import annotations

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
from fetch_results import SUMMARY_PATH, parse_int
from georgia_presidential_config import GEORGIA_PRESIDENTIAL_SOURCES, SOURCE_NAME, SOURCE_URL, raw_path


PARTY_MARKERS = {
    "(DEM)": "DEMOCRAT",
    "(REP)": "REPUBLICAN",
    "(LIB)": "LIBERTARIAN",
    "(GRN)": "GREEN",
}


def sorted_parties(parties: dict[str, int]) -> list[tuple[str, int]]:
    order = {"DEMOCRAT": 0, "REPUBLICAN": 1, "LIBERTARIAN": 2, "GREEN": 3, "OTHER": 4}
    return sorted(parties.items(), key=lambda item: (-item[1], order.get(item[0], 99), item[0]))


def party_code(choice_name: str) -> str:
    upper = choice_name.upper()
    for marker, party in PARTY_MARKERS.items():
        if marker in upper:
            return party
    return "OTHER"


def county_name_from_summary_zip(member_name: str) -> str:
    name = Path(member_name).name
    county = re.sub(r"_\d+_\d+-summary\.zip$", "", name)
    return county.replace("_", " ").upper()


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


def parse_summary_csv(text: str) -> dict[str, int]:
    parties: dict[str, int] = defaultdict(int)
    for row in csv.DictReader(io.StringIO(text)):
        if not str(row.get("contest name", "")).startswith("President of the United States"):
            continue
        parties[party_code(row.get("choice name", ""))] += parse_int(row.get("total votes"))
    return dict(parties)


def parse_official_zip(path: Path) -> dict[str, dict[str, int]]:
    counties: dict[str, dict[str, int]] = {}
    with zipfile.ZipFile(path) as outer:
        for member_name in outer.namelist():
            if not member_name.endswith("-summary.zip"):
                continue
            county_name = county_name_from_summary_zip(member_name)
            with zipfile.ZipFile(io.BytesIO(outer.read(member_name))) as inner:
                csv_names = [name for name in inner.namelist() if name.endswith(".csv")]
                if len(csv_names) != 1:
                    raise RuntimeError(f"Expected one summary CSV in {member_name}, found {len(csv_names)}")
                text = inner.read(csv_names[0]).decode("utf-8-sig", errors="replace")
            counties[county_name] = parse_summary_csv(text)

    if not counties:
        raise RuntimeError(f"No Georgia county summary ZIPs found in {path}")
    return counties


def merge_official_rows(summary: dict[str, Any]) -> dict[str, int]:
    ga_counties = {county["county_name"].upper(): county for county in summary.get("counties", []) if county.get("state_po") == "GA"}
    stats = {
        "replaced": 0,
        "missing_counties": 0,
        "extra_counties": 0,
    }

    for year, source in GEORGIA_PRESIDENTIAL_SOURCES.items():
        path = ROOT_DIR / raw_path(source)
        if not path.exists():
            raise RuntimeError(f"Missing official Georgia file: {path.relative_to(ROOT_DIR)}. Run npm run data:official:ga:download first.")
        official_rows = parse_official_zip(path)
        stats["missing_counties"] += len(set(ga_counties) - set(official_rows))
        stats["extra_counties"] += len(set(official_rows) - set(ga_counties))

        for county_name in sorted(set(ga_counties) & set(official_rows)):
            county = ga_counties[county_name]
            county.setdefault("results", {})[str(year)] = build_result(official_rows[county_name], source.url)
            stats["replaced"] += 1

    source = summary.setdefault("source", {})
    official_sources = source.setdefault("official_state_sources", [])
    record = {
        "name": SOURCE_NAME,
        "url": SOURCE_URL,
        "state_po": "GA",
        "years": sorted(GEORGIA_PRESIDENTIAL_SOURCES),
        "quality_grade": "A",
        "notes": "Official Georgia Secretary of State recount summary ZIPs aggregated to county presidential totals and used before non-authoritative supplemental CSV rows.",
    }
    official_sources[:] = [item for item in official_sources if item.get("name") != SOURCE_NAME or item.get("state_po") != "GA"]
    official_sources.append(record)
    return stats


def main() -> int:
    output_path = ROOT_DIR / SUMMARY_PATH
    summary = json.loads(output_path.read_text(encoding="utf-8"))
    stats = merge_official_rows(summary)
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(
        "Merged official Georgia presidential returns: "
        f"{stats['replaced']} county-year rows replaced, "
        f"{stats['missing_counties']} missing official counties, "
        f"{stats['extra_counties']} unmatched official counties."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
