#!/usr/bin/env python3
"""Generate Pennsylvania contest summaries from official precinct returns."""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from typing import Any

from pennsylvania_config import OUTPUT_PATH, PENNSYLVANIA_GENERAL_SOURCES, SOURCE_PAGE_URL, PennsylvaniaGeneralSource, readme_path, results_path


OFFICE_MAP = {
    "USP": "President",
    "USS": "U.S. Senate",
    "GOV": "Governor",
    "USC": "U.S. House",
    "STS": "State Senate",
    "STH": "State House",
}
DISTRICT_OFFICES = {"USC", "STS", "STH"}
PARTY_MAP = {
    "DEM": "DEMOCRAT",
    "REP": "REPUBLICAN",
    "LIB": "LIBERTARIAN",
    "GRN": "GREEN",
    "CST": "CONSTITUTION",
}


FIELDS = [
    "election_year",
    "election_type",
    "county_code",
    "precinct_code",
    "candidate_office_rank",
    "candidate_district",
    "candidate_party_rank",
    "candidate_ballot_position",
    "candidate_office_code",
    "candidate_party_code",
    "candidate_number",
    "candidate_last_name",
    "candidate_first_name",
    "candidate_middle_name",
    "candidate_suffix",
    "vote_total",
    "yes_vote_total",
    "no_vote_total",
    "us_congressional_district",
    "state_senatorial_district",
    "state_house_district",
    "municipality_type_code",
    "municipality_name",
    "municipality_breakdown_code_1",
    "municipality_breakdown_name_1",
    "municipality_breakdown_code_2",
    "municipality_breakdown_name_2",
    "bi_county_code",
    "mcd_code",
    "fips_code",
    "vtd_code",
    "ballot_question",
    "record_type",
    "previous_precinct_code",
    "previous_us_congressional_district",
    "previous_state_senatorial_district",
    "previous_state_house_district",
]


def parse_counties(readme_text: str) -> dict[int, str]:
    match = re.search(r"County Code Table\s*-+\s*(.*?)\n\n", readme_text, flags=re.S)
    if match is None:
        raise RuntimeError("Could not find Pennsylvania county table in readme")
    counties: dict[int, str] = {}
    for line in match.group(1).splitlines():
        row = line.strip()
        if not row:
            continue
        code, name = row[:2], row[3:].strip()
        if code.isdigit() and name:
            counties[int(code)] = name.upper()
    if len(counties) != 67:
        raise RuntimeError(f"Expected 67 Pennsylvania counties, found {len(counties)}")
    return counties


def int_value(value: str) -> int:
    return int(value.strip() or "0")


def candidate_name(row: dict[str, str]) -> str:
    parts = [
        row["candidate_first_name"].strip(),
        row["candidate_middle_name"].strip(),
        row["candidate_last_name"].strip(),
        row["candidate_suffix"].strip(),
    ]
    return " ".join(part for part in parts if part)


def normalize_party(value: str) -> str:
    value = value.strip().upper()
    return PARTY_MAP.get(value, value or "OTHER")


def district_label(office_code: str, district: int) -> str | None:
    if office_code == "USC":
        return f"{district} Congressional District"
    if office_code == "STS":
        return f"{district} State Senate District"
    if office_code == "STH":
        return f"{district} State House District"
    return None


def sorted_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(candidates, key=lambda candidate: int(candidate["votes"]), reverse=True)


def contest_key(row: dict[str, str]) -> tuple[str, int]:
    office_code = row["candidate_office_code"].strip().upper()
    district = int_value(row["candidate_district"]) if office_code in DISTRICT_OFFICES else 0
    return office_code, district


def parse_rows(source: PennsylvaniaGeneralSource) -> tuple[dict[int, str], dict[tuple[str, int], dict[str, Any]]]:
    counties = parse_counties(readme_path(source).read_text(encoding="utf-8", errors="replace"))
    contests: dict[tuple[str, int], dict[str, Any]] = {}
    with results_path(source).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, fieldnames=FIELDS)
        for row in reader:
            office_code = row["candidate_office_code"].strip().upper()
            if office_code not in OFFICE_MAP:
                continue
            key = contest_key(row)
            district = key[1]
            county_code = int_value(row["county_code"])
            county_name = counties[county_code]
            contest = contests.setdefault(
                key,
                {
                    "office_code": office_code,
                    "office": OFFICE_MAP[office_code],
                    "district_number": district or None,
                    "district_label": district_label(office_code, district),
                    "candidates": defaultdict(int),
                    "counties": {},
                    "source_file_url": source.results_url,
                    "quality_grade": "A",
                },
            )
            candidate_key = (candidate_name(row), normalize_party(row["candidate_party_code"]))
            votes = int_value(row["vote_total"])
            contest["candidates"][candidate_key] += votes
            county = contest["counties"].setdefault(
                county_code,
                {"fips": f"42{int_value(row['fips_code']):03d}", "county_name": county_name, "candidates": defaultdict(int)},
            )
            county["candidates"][candidate_key] += votes
    return counties, contests


def materialize_candidates(candidate_totals: dict[tuple[str, str], int]) -> list[dict[str, Any]]:
    return sorted_candidates(
        [{"candidate": candidate, "party": party, "votes": votes} for (candidate, party), votes in candidate_totals.items()]
    )


def materialize_contest(raw: dict[str, Any], contest_id: int, source: PennsylvaniaGeneralSource) -> dict[str, Any]:
    candidates = materialize_candidates(raw["candidates"])
    total_votes = sum(candidate["votes"] for candidate in candidates)
    margin_votes = candidates[0]["votes"] - candidates[1]["votes"] if len(candidates) > 1 else 0
    counties = []
    for county_code, county in sorted(raw["counties"].items()):
        county_candidates = materialize_candidates(county["candidates"])
        county_total = sum(candidate["votes"] for candidate in county_candidates)
        counties.append(
            {
                "fips": county["fips"],
                "county_name": county["county_name"],
                "total_votes": county_total,
                "winner": county_candidates[0],
                "margin_votes": county_candidates[0]["votes"] - county_candidates[1]["votes"] if len(county_candidates) > 1 else 0,
                "candidates": county_candidates,
            }
        )
    contest = {
        "contest_id": contest_id,
        "office": raw["office"],
        "district_label": raw["district_label"],
        "name": f"Pennsylvania {source.year} {raw['district_label'] or raw['office']}",
        "state": "Pennsylvania",
        "state_po": "PA",
        "total_votes": total_votes,
        "winner": candidates[0],
        "margin_votes": margin_votes,
        "candidates": candidates,
        "counties": counties,
        "source_file_url": raw["source_file_url"],
        "quality_grade": raw["quality_grade"],
    }
    if raw["district_number"] is not None:
        contest["district_number"] = raw["district_number"]
    return contest


def build_election(source: PennsylvaniaGeneralSource) -> dict[str, Any]:
    _, raw_contests = parse_rows(source)
    contests = [
        materialize_contest(raw, index + 1, source)
        for index, (_, raw) in enumerate(sorted(raw_contests.items(), key=lambda item: (OFFICE_MAP[item[0][0]], item[0][1])))
    ]
    return {
        "source": {
            "name": "Pennsylvania Department of State",
            "url": source.results_url,
            "homepage": SOURCE_PAGE_URL,
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "quality_grade": "A",
        },
        "election": {
            "year": source.year,
            "date": source.election_date,
            "type": "general",
            "state": "Pennsylvania",
            "state_po": "PA",
        },
        "contests": contests,
    }


def build_summary() -> dict[str, Any]:
    return {
        "source": {
            "name": "Pennsylvania Department of State",
            "url": SOURCE_PAGE_URL,
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "quality_grade": "A",
        },
        "elections": [build_election(source) for source in sorted(PENNSYLVANIA_GENERAL_SOURCES, key=lambda item: item.year, reverse=True)],
    }


def main() -> int:
    summary = build_summary()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    contest_count = sum(len(election["contests"]) for election in summary["elections"])
    print(f"Wrote {OUTPUT_PATH.relative_to(OUTPUT_PATH.parents[2])} with {contest_count} Pennsylvania contests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
