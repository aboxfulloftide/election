#!/usr/bin/env python3
"""Merge official Kentucky county presidential rows into the summary."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR
from fetch_results import SUMMARY_PATH, parse_int
from kentucky_presidential_config import KENTUCKY_PRESIDENTIAL_SOURCES, SOURCE_NAME, SOURCE_URL, raw_path


def sorted_parties(parties: dict[str, int]) -> list[tuple[str, int]]:
    order = {"DEMOCRAT": 0, "REPUBLICAN": 1, "LIBERTARIAN": 2, "GREEN": 3, "OTHER": 4}
    return sorted(parties.items(), key=lambda item: (-item[1], order.get(item[0], 99), item[0]))


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
        "quality_grade": "B",
    }


def pdf_text(path: Path) -> str:
    result = subprocess.run(["pdftotext", "-raw", str(path), "-"], check=True, capture_output=True, text=True, errors="replace")
    return result.stdout


def line_county_votes(line: str, county_names: set[str]) -> tuple[str, list[int]] | None:
    for county_name in sorted(county_names, key=len, reverse=True):
        if not line.upper().startswith(county_name + " "):
            continue
        values = re.findall(r"\d[\d,]*", line[len(county_name) :])
        if len(values) >= 16:
            return county_name, [parse_int(value.replace(",", "")) for value in values[:16]]
    return None


def parse_official_pdf(path: Path, county_names: set[str]) -> dict[str, dict[str, int]]:
    rows: dict[str, dict[str, int]] = {}
    for line in pdf_text(path).splitlines():
        parsed = line_county_votes(re.sub(r"\s+", " ", line).strip(), county_names)
        if parsed is None:
            continue
        county_name, values = parsed
        if county_name in rows:
            continue
        parties = {
            "REPUBLICAN": values[0],
            "DEMOCRAT": values[1],
            "LIBERTARIAN": values[2],
        }
        other_votes = sum(values[3:])
        if other_votes:
            parties["OTHER"] = other_votes
        rows[county_name] = parties
    return rows


def merge_official_rows(summary: dict[str, Any]) -> dict[str, int]:
    ky_counties = {county["county_name"].upper(): county for county in summary.get("counties", []) if county.get("state_po") == "KY"}
    stats = {"replaced": 0, "missing_counties": 0, "extra_counties": 0}

    for year, source in KENTUCKY_PRESIDENTIAL_SOURCES.items():
        path = ROOT_DIR / raw_path(source)
        if not path.exists():
            raise RuntimeError(f"Missing official Kentucky file: {path.relative_to(ROOT_DIR)}. Run npm run data:official:ky:download first.")
        official_rows = parse_official_pdf(path, set(ky_counties))
        stats["missing_counties"] += len(set(ky_counties) - set(official_rows))
        stats["extra_counties"] += len(set(official_rows) - set(ky_counties))

        for county_name in sorted(set(ky_counties) & set(official_rows)):
            county = ky_counties[county_name]
            county.setdefault("results", {})[str(year)] = build_result(official_rows[county_name], source.url)
            stats["replaced"] += 1

    source = summary.setdefault("source", {})
    official_sources = source.setdefault("official_state_sources", [])
    record = {
        "name": SOURCE_NAME,
        "url": SOURCE_URL,
        "state_po": "KY",
        "years": sorted(KENTUCKY_PRESIDENTIAL_SOURCES),
        "quality_grade": "B",
        "notes": "Official Kentucky certified general election PDF parsed with pdftotext and used before non-authoritative supplemental CSV rows.",
    }
    official_sources[:] = [item for item in official_sources if item.get("name") != SOURCE_NAME or item.get("state_po") != "KY"]
    official_sources.append(record)
    return stats


def main() -> int:
    output_path = ROOT_DIR / SUMMARY_PATH
    summary = json.loads(output_path.read_text(encoding="utf-8"))
    stats = merge_official_rows(summary)
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(
        "Merged official Kentucky presidential returns: "
        f"{stats['replaced']} county-year rows replaced, "
        f"{stats['missing_counties']} missing official counties, "
        f"{stats['extra_counties']} unmatched official counties."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
