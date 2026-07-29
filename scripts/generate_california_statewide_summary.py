#!/usr/bin/env python3
"""Generate California statewide contest summaries from official XLSX files."""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

from california_statewide_config import (
    CALIFORNIA_CONTEST_SOURCES,
    CALIFORNIA_DISTRICT_CONTEST_SOURCES,
    OUTPUT_PATH,
    SOURCE_NAME,
    SOURCE_URL,
    CaliforniaContestSource,
    raw_path,
)
from election_db import ROOT_DIR
from fetch_results import parse_int
from xlsx_reader import read_first_sheet


PARTY_MAP = {
    "DEM": "DEMOCRAT",
    "REP": "REPUBLICAN",
    "LIB": "LIBERTARIAN",
    "GRN": "GREEN",
}

CALIFORNIA_COUNTY_FIPS = {
    "ALAMEDA": "06001",
    "ALPINE": "06003",
    "AMADOR": "06005",
    "BUTTE": "06007",
    "CALAVERAS": "06009",
    "COLUSA": "06011",
    "CONTRA COSTA": "06013",
    "DEL NORTE": "06015",
    "EL DORADO": "06017",
    "FRESNO": "06019",
    "GLENN": "06021",
    "HUMBOLDT": "06023",
    "IMPERIAL": "06025",
    "INYO": "06027",
    "KERN": "06029",
    "KINGS": "06031",
    "LAKE": "06033",
    "LASSEN": "06035",
    "LOS ANGELES": "06037",
    "MADERA": "06039",
    "MARIN": "06041",
    "MARIPOSA": "06043",
    "MENDOCINO": "06045",
    "MERCED": "06047",
    "MODOC": "06049",
    "MONO": "06051",
    "MONTEREY": "06053",
    "NAPA": "06055",
    "NEVADA": "06057",
    "ORANGE": "06059",
    "PLACER": "06061",
    "PLUMAS": "06063",
    "RIVERSIDE": "06065",
    "SACRAMENTO": "06067",
    "SAN BENITO": "06069",
    "SAN BERNARDINO": "06071",
    "SAN DIEGO": "06073",
    "SAN FRANCISCO": "06075",
    "SAN JOAQUIN": "06077",
    "SAN LUIS OBISPO": "06079",
    "SAN MATEO": "06081",
    "SANTA BARBARA": "06083",
    "SANTA CLARA": "06085",
    "SANTA CRUZ": "06087",
    "SHASTA": "06089",
    "SIERRA": "06091",
    "SISKIYOU": "06093",
    "SOLANO": "06095",
    "SONOMA": "06097",
    "STANISLAUS": "06099",
    "SUTTER": "06101",
    "TEHAMA": "06103",
    "TRINITY": "06105",
    "TULARE": "06107",
    "TUOLUMNE": "06109",
    "VENTURA": "06111",
    "YOLO": "06113",
    "YUBA": "06115",
}


def normalize_party(value: Any) -> str:
    return PARTY_MAP.get(str(value or "").strip().upper(), "OTHER")


def sorted_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(candidates, key=lambda candidate: int(candidate["votes"]), reverse=True)


def clean_candidate(value: Any) -> str:
    return str(value or "").replace("\n", " ").replace("*", "").strip()


def district_number(label: str) -> int | None:
    match = re.search(r"\b(\d+)(?:st|nd|rd|th)?\b", label)
    return int(match.group(1)) if match else None


def is_district_header(label: str) -> bool:
    return bool(re.match(r"^\d+(?:st|nd|rd|th)?\s+.+\s+District$", label))


def county_fips(county_name: str) -> str:
    try:
        return CALIFORNIA_COUNTY_FIPS[county_name]
    except KeyError as exc:
        raise RuntimeError(f"Unknown California county: {county_name}") from exc


def contest_county_rows(source: CaliforniaContestSource) -> list[dict[str, Any]]:
    rows = read_first_sheet(ROOT_DIR / raw_path(source))
    if len(rows) < 3:
        raise RuntimeError(f"California workbook is too short: {raw_path(source)}")
    candidates = [clean_candidate(value) for value in rows[0][1:]]
    parties = [normalize_party(value) for value in rows[1][1:]]
    counties: list[dict[str, Any]] = []

    for row in rows[2:]:
        if not row or not row[0]:
            continue
        county_name = str(row[0]).strip().upper()
        if county_name in {"PERCENT", "STATE TOTALS", "TOTALS", "TOTAL"}:
            continue
        candidate_rows: list[dict[str, Any]] = []
        for index, candidate in enumerate(candidates, start=1):
            votes = parse_int(str(row[index] if index < len(row) and row[index] is not None else "0"))
            candidate_rows.append({"candidate": candidate, "party": parties[index - 1], "votes": votes})
        candidate_rows = sorted_candidates(candidate_rows)
        total_votes = sum(candidate["votes"] for candidate in candidate_rows)
        winner_votes = candidate_rows[0]["votes"] if candidate_rows else 0
        runner_up_votes = candidate_rows[1]["votes"] if len(candidate_rows) > 1 else 0
        counties.append(
            {
                "fips": county_fips(county_name),
                "county_name": county_name,
                "total_votes": total_votes,
                "winner": candidate_rows[0],
                "margin_votes": winner_votes - runner_up_votes,
                "candidates": candidate_rows,
            }
        )
    return counties


def county_row(row: list[Any], candidates: list[str], parties: list[str], *, include_fips: bool = True) -> dict[str, Any]:
    county_name = str(row[0]).strip().upper()
    candidate_rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        votes = parse_int(str(row[index] if index < len(row) and row[index] is not None else "0"))
        candidate_rows.append({"candidate": candidate, "party": parties[index - 1], "votes": votes})
    candidate_rows = sorted_candidates(candidate_rows)
    total_votes = sum(candidate["votes"] for candidate in candidate_rows)
    winner_votes = candidate_rows[0]["votes"] if candidate_rows else 0
    runner_up_votes = candidate_rows[1]["votes"] if len(candidate_rows) > 1 else 0
    parsed = {
        "county_name": county_name,
        "total_votes": total_votes,
        "winner": candidate_rows[0],
        "margin_votes": winner_votes - runner_up_votes,
        "candidates": candidate_rows,
    }
    if include_fips:
        parsed["fips"] = county_fips(county_name)
    return parsed


def district_contests(source: CaliforniaContestSource, contest_id_start: int) -> list[dict[str, Any]]:
    rows = read_first_sheet(ROOT_DIR / raw_path(source))
    contests: list[dict[str, Any]] = []
    index = 0
    contest_id = contest_id_start
    while index < len(rows):
        row = rows[index]
        label = str(row[0]).strip() if row and row[0] else ""
        if not is_district_header(label):
            index += 1
            continue
        if index + 2 >= len(rows):
            raise RuntimeError(f"Missing candidate or party rows for {label} in {raw_path(source)}")
        candidates = [clean_candidate(value) for value in rows[index + 1][1:] if value is not None]
        parties = [normalize_party(value) for value in rows[index + 2][1 : 1 + len(candidates)]]
        if not candidates:
            raise RuntimeError(f"Missing candidates for {label} in {raw_path(source)}")
        counties: list[dict[str, Any]] = []
        district_total_row: list[Any] | None = None
        index += 3
        while index < len(rows):
            current = rows[index]
            name = str(current[0]).strip() if current and current[0] else ""
            if not name:
                index += 1
                break
            if is_district_header(name):
                break
            if name == "District Totals":
                district_total_row = current
                index += 1
                continue
            if name.upper() != "PERCENT":
                counties.append(county_row(current, candidates, parties))
            index += 1
        if district_total_row is None:
            raise RuntimeError(f"Missing district totals for {label} in {raw_path(source)}")
        total_county = county_row(["DISTRICT TOTALS", *district_total_row[1:]], candidates, parties, include_fips=False)
        contest = {
            "contest_id": contest_id,
            "office": source.office,
            "district_label": label,
            "district_number": district_number(label),
            "name": f"California {source.year} {label} {source.contest_label}",
            "state": "California",
            "state_po": "CA",
            "total_votes": total_county["total_votes"],
            "winner": total_county["winner"],
            "margin_votes": total_county["margin_votes"],
            "candidates": total_county["candidates"],
            "counties": counties,
            "source_file_url": source.url,
            "quality_grade": "A",
        }
        contests.append(contest)
        contest_id += 1
    return contests


def build_contest(source: CaliforniaContestSource, contest_id: int) -> dict[str, Any]:
    counties = contest_county_rows(source)
    candidate_totals: dict[tuple[str, str], int] = {}
    for county in counties:
        for candidate in county["candidates"]:
            key = (candidate["candidate"], candidate["party"])
            candidate_totals[key] = candidate_totals.get(key, 0) + int(candidate["votes"])
    candidates = sorted_candidates(
        [{"candidate": candidate, "party": party, "votes": votes} for (candidate, party), votes in candidate_totals.items()]
    )
    total_votes = sum(candidate["votes"] for candidate in candidates)
    winner_votes = candidates[0]["votes"] if candidates else 0
    runner_up_votes = candidates[1]["votes"] if len(candidates) > 1 else 0
    return {
        "contest_id": contest_id,
        "office": source.office,
        "district_label": None,
        "name": f"California {source.year} {source.contest_label}",
        "state": "California",
        "state_po": "CA",
        "total_votes": total_votes,
        "winner": candidates[0],
        "margin_votes": winner_votes - runner_up_votes,
        "candidates": candidates,
        "counties": counties,
        "source_file_url": source.url,
        "quality_grade": "A",
    }


def build_summary() -> dict[str, Any]:
    contests = [build_contest(source, index) for index, source in enumerate(CALIFORNIA_CONTEST_SOURCES, start=1)]
    next_contest_id = len(contests) + 1
    for source in CALIFORNIA_DISTRICT_CONTEST_SOURCES:
        parsed = district_contests(source, next_contest_id)
        contests.extend(parsed)
        next_contest_id += len(parsed)
    return {
        "source": {
            "name": SOURCE_NAME,
            "url": SOURCE_URL,
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "quality_grade": "A",
        },
        "elections": [
            {
                "source": {
                    "name": SOURCE_NAME,
                    "url": SOURCE_URL,
                    "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
                    "quality_grade": "A",
                },
                "election": {
                    "year": 2024,
                    "date": "2024-11-05",
                    "type": "general",
                    "state": "California",
                },
                "contests": contests,
            }
        ],
    }


def main() -> int:
    summary = build_summary()
    output_path = ROOT_DIR / OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} with {len(summary['elections'][0]['contests'])} California contests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
