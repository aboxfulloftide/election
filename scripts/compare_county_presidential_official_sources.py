#!/usr/bin/env python3
"""Compare official county presidential source files against generated JSON rows."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from election_db import ROOT_DIR
from fetch_results import SUMMARY_PATH
from georgia_presidential_config import GEORGIA_PRESIDENTIAL_SOURCES, raw_path as georgia_raw_path
from kentucky_presidential_config import KENTUCKY_PRESIDENTIAL_SOURCES, raw_path as kentucky_raw_path
from merge_georgia_presidential import parse_official_zip as parse_georgia_zip
from merge_kentucky_presidential import parse_official_pdf as parse_kentucky_pdf
from merge_north_carolina_presidential import parse_official_zip as parse_north_carolina_zip
from merge_virginia_presidential import parse_official_csv as parse_virginia_csv
from north_carolina_presidential_config import NORTH_CAROLINA_PRESIDENTIAL_SOURCES, raw_path as north_carolina_raw_path
from virginia_presidential_config import VIRGINIA_PRESIDENTIAL_SOURCES, raw_path as virginia_raw_path
from wisconsin_presidential_config import WISCONSIN_PRESIDENTIAL_SOURCES, raw_path as wisconsin_raw_path
from merge_wisconsin_presidential import parse_official_pdf as parse_wisconsin_pdf


class ComparisonFailure(Exception):
    pass


def load_summary() -> dict[str, Any]:
    return json.loads((ROOT_DIR / SUMMARY_PATH).read_text(encoding="utf-8"))


def party_votes(result: dict[str, Any]) -> dict[str, int]:
    return {party: int(votes) for party, votes in result.get("parties", {}).items() if int(votes) != 0}


def compare_by_county_name(
    summary: dict[str, Any],
    *,
    state_po: str,
    year: int,
    source_name: str,
    official_rows: dict[str, dict[str, int]],
) -> list[str]:
    failures: list[str] = []
    counties = {county["county_name"].upper(): county for county in summary.get("counties", []) if county.get("state_po") == state_po}

    for county_name, parties in official_rows.items():
        county = counties.get(county_name)
        if county is None:
            failures.append(f"{state_po} {year} {county_name}: official county missing from summary")
            continue
        result = county.get("results", {}).get(str(year))
        if not result:
            failures.append(f"{state_po} {year} {county_name}: summary result missing")
            continue
        if not result.get("official") or result.get("source_name") != source_name:
            failures.append(f"{state_po} {year} {county_name}: summary result is not marked official from {source_name}")
            continue
        if party_votes(result) != {party: votes for party, votes in parties.items() if votes != 0}:
            failures.append(f"{state_po} {year} {county_name}: party votes do not match official source")
    return failures


def compare_virginia(summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    counties = {
        (county["county_name"].upper(), "city" if str(county["fips"]).startswith("51") and len(str(county["fips"])) >= 3 and str(county["fips"])[2] in {"5", "6", "7", "8", "9"} else "county"): county
        for county in summary.get("counties", [])
        if county.get("state_po") == "VA"
    }
    for year, source in VIRGINIA_PRESIDENTIAL_SOURCES.items():
        rows = parse_virginia_csv(ROOT_DIR / virginia_raw_path(source))
        for key, parties in rows.items():
            county = counties.get(key)
            if county is None:
                failures.append(f"VA {year} {key}: official locality missing from summary")
                continue
            result = county.get("results", {}).get(str(year))
            if not result or not result.get("official") or result.get("source_name") != "Virginia Department of Elections":
                failures.append(f"VA {year} {key}: summary result is not marked official from Virginia Department of Elections")
                continue
            if party_votes(result) != {party: votes for party, votes in parties.items() if votes != 0}:
                failures.append(f"VA {year} {key}: party votes do not match official source")
    return failures


def optional_compare(label: str, callback: Callable[[], list[str]]) -> list[str]:
    try:
        return callback()
    except FileNotFoundError:
        return [f"{label}: official source file is missing"]


def compare_sources(summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    for year, source in GEORGIA_PRESIDENTIAL_SOURCES.items():
        failures.extend(
            optional_compare(
                f"GA {year}",
                lambda year=year, source=source: compare_by_county_name(
                    summary,
                    state_po="GA",
                    year=year,
                    source_name="Georgia Secretary of State",
                    official_rows=parse_georgia_zip(ROOT_DIR / georgia_raw_path(source)),
                ),
            )
        )

    for year, source in KENTUCKY_PRESIDENTIAL_SOURCES.items():
        ky_counties = {county["county_name"].upper() for county in summary.get("counties", []) if county.get("state_po") == "KY"}
        failures.extend(
            optional_compare(
                f"KY {year}",
                lambda year=year, source=source, ky_counties=ky_counties: compare_by_county_name(
                    summary,
                    state_po="KY",
                    year=year,
                    source_name="Kentucky State Board of Elections",
                    official_rows=parse_kentucky_pdf(ROOT_DIR / kentucky_raw_path(source), ky_counties),
                ),
            )
        )

    for year, source in NORTH_CAROLINA_PRESIDENTIAL_SOURCES.items():
        failures.extend(
            optional_compare(
                f"NC {year}",
                lambda year=year, source=source: compare_by_county_name(
                    summary,
                    state_po="NC",
                    year=year,
                    source_name="North Carolina State Board of Elections",
                    official_rows=parse_north_carolina_zip(ROOT_DIR / north_carolina_raw_path(source)),
                ),
            )
        )

    failures.extend(optional_compare("VA", lambda: compare_virginia(summary)))

    for year, source in WISCONSIN_PRESIDENTIAL_SOURCES.items():
        wi_counties = {county["county_name"].upper() for county in summary.get("counties", []) if county.get("state_po") == "WI"}
        failures.extend(
            optional_compare(
                f"WI {year}",
                lambda year=year, source=source, wi_counties=wi_counties: compare_by_county_name(
                    summary,
                    state_po="WI",
                    year=year,
                    source_name="Wisconsin Elections Commission",
                    official_rows=parse_wisconsin_pdf(ROOT_DIR / wisconsin_raw_path(source), wi_counties),
                ),
            )
        )
    return failures


def main() -> int:
    failures = compare_sources(load_summary())
    if failures:
        raise ComparisonFailure("\n".join(failures[:40]))
    print("Official county presidential source comparisons passed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ComparisonFailure as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
