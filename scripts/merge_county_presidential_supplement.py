#!/usr/bin/env python3
"""Merge supplemental county presidential returns into missing MIT rows."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

from download_county_presidential_supplement import SOURCE_NAME, SOURCE_URL, YEARS, raw_path
from election_db import ROOT_DIR
from fetch_results import SUMMARY_PATH, parse_int


SUPPLEMENT_LICENSE = "MIT"
SUPPLEMENT_QUALITY_GRADE = "D"


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sorted_parties(parties: dict[str, int]) -> list[tuple[str, int]]:
    order = {"DEMOCRAT": 0, "REPUBLICAN": 1, "LIBERTARIAN": 2, "GREEN": 3, "OTHER": 4}
    return sorted(parties.items(), key=lambda item: (-item[1], order.get(item[0], 99), item[0]))


def build_result(row: dict[str, str]) -> dict[str, Any]:
    dem_votes = parse_int(row.get("votes_dem"))
    rep_votes = parse_int(row.get("votes_gop"))
    total_votes = parse_int(row.get("total_votes"))
    other_votes = max(total_votes - dem_votes - rep_votes, 0)
    parties = {
        "DEMOCRAT": dem_votes,
        "REPUBLICAN": rep_votes,
    }
    if other_votes:
        parties["OTHER"] = other_votes

    ordered = sorted_parties(parties)
    winner_party, winner_votes = ordered[0]
    runner_up_votes = ordered[1][1] if len(ordered) > 1 else 0
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
        "supplemental": True,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "quality_grade": SUPPLEMENT_QUALITY_GRADE,
    }


def read_supplement_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = {}
        for row in csv.DictReader(handle):
            fips = str(row.get("county_fips", "")).strip().zfill(5)
            if fips:
                rows[fips] = row
        return rows


def merge_supplement(summary: dict[str, Any]) -> dict[str, int]:
    counties_by_fips = {str(county["fips"]): county for county in summary.get("counties", [])}
    stats = {
        "inserted": 0,
        "existing": 0,
        "missing_source_fips": 0,
        "extra_source_fips": 0,
    }

    for year in YEARS:
        year_key = str(year)
        path = raw_path(year)
        if not path.exists():
            raise RuntimeError(f"Missing supplemental file: {path.relative_to(ROOT_DIR)}. Run npm run data:supplement:download first.")

        rows_by_fips = read_supplement_rows(path)
        missing_fips = {fips for fips, county in counties_by_fips.items() if year_key not in county.get("results", {})}
        stats["missing_source_fips"] += len(missing_fips - set(rows_by_fips))
        stats["extra_source_fips"] += len(set(rows_by_fips) - set(counties_by_fips))

        for fips in sorted(missing_fips & set(rows_by_fips)):
            county = counties_by_fips[fips]
            county.setdefault("results", {})[year_key] = build_result(rows_by_fips[fips])
            stats["inserted"] += 1
        stats["existing"] += len(counties_by_fips) - len(missing_fips)

    source = summary.setdefault("source", {})
    supplements = source.setdefault("supplements", [])
    supplement_record = {
        "name": SOURCE_NAME,
        "url": SOURCE_URL,
        "years": list(YEARS),
        "license": SUPPLEMENT_LICENSE,
        "quality_grade": SUPPLEMENT_QUALITY_GRADE,
        "notes": "Used only to fill missing 2020/2024 county rows absent from the MIT county presidential summary. Source README states these compiled rows are not authoritative.",
    }
    supplements[:] = [item for item in supplements if item.get("name") != SOURCE_NAME]
    supplements.append(supplement_record)

    return stats


def main() -> int:
    output_path = ROOT_DIR / SUMMARY_PATH
    summary = load_summary(output_path)
    stats = merge_supplement(summary)
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(
        "Merged supplemental county presidential returns: "
        f"{stats['inserted']} rows inserted, "
        f"{stats['missing_source_fips']} missing FIPS not filled, "
        f"{stats['extra_source_fips']} supplemental FIPS outside current summary."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
