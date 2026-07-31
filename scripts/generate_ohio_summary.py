#!/usr/bin/env python3
"""Generate Ohio statewide/district summaries from official SOS workbooks."""

from __future__ import annotations

import html
import json
import re
from typing import Any

from ohio_config import COUNTY_PRESIDENTIAL_SUMMARY_PATH, OHIO_WORKBOOKS, OUTPUT_PATH, ROOT_DIR, OhioSourceWorkbook
from xlsx_reader import read_xlsx_sheets


PARTY_MAP = {
    "D": "DEMOCRAT",
    "R": "REPUBLICAN",
    "L": "LIBERTARIAN",
    "G": "GREEN",
}
COUNTY_ALIASES = {
    "DEFIANCE": "DEFIANCE",
}


def clean_text(value: Any) -> str:
    return " ".join(html.unescape(str(value or "")).replace("\xa0", " ").split())


def int_value(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return int(clean_text(value).replace(",", ""))


def normalize_county_name(value: Any) -> str:
    normalized = clean_text(value).upper()
    return COUNTY_ALIASES.get(normalized, normalized)


def load_ohio_counties() -> dict[str, dict[str, str]]:
    summary = json.loads(COUNTY_PRESIDENTIAL_SUMMARY_PATH.read_text(encoding="utf-8"))
    counties = {
        normalize_county_name(county["county_name"]): {"fips": county["fips"], "county_name": county["county_name"]}
        for county in summary["counties"]
        if county["state_po"] == "OH"
    }
    if len(counties) != 88:
        raise RuntimeError(f"Expected 88 Ohio counties in county presidential summary, found {len(counties)}")
    return counties


def parse_candidate_label(value: Any) -> tuple[str, str]:
    label = clean_text(value).removesuffix("*").strip()
    if "(WI)" in label:
        return clean_text(label.replace("(WI)", "").strip()), "WRITE-IN"
    match = re.match(r"^(.+?)\s+\(([A-Z])\)$", label)
    if match:
        return clean_text(match.group(1)), PARTY_MAP.get(match.group(2), match.group(2))
    return label, "NONPARTISAN"


def office_for_contest(contest_name: str) -> tuple[str, int | None, str | None]:
    normalized = clean_text(contest_name)
    if normalized == "President and Vice President":
        return "President", None, None
    if normalized == "Governor and Lieutenant Governor":
        return "Governor", None, None
    if normalized == "U.S. Senator":
        return "U.S. Senate", None, None
    match = re.match(r"Representative to Congress - District\s+(\d+)$", normalized)
    if match:
        district = int(match.group(1))
        return "U.S. House", district, f"{district} Congressional District"
    match = re.match(r"State Senator - District\s+(\d+)$", normalized)
    if match:
        district = int(match.group(1))
        return "State Senate", district, f"{district} State Senate District"
    match = re.match(r"State Representative - District\s+(\d+)$", normalized)
    if match:
        district = int(match.group(1))
        return "State House", district, f"{district} State House District"
    raise RuntimeError(f"Unsupported Ohio contest name: {contest_name}")


def is_target_contest(contest_name: str) -> bool:
    try:
        office_for_contest(contest_name)
    except RuntimeError:
        return False
    return True


def group_contest_columns(rows: list[list[Any]]) -> list[tuple[str, list[int]]]:
    heading_row = rows[0]
    groups: list[tuple[str, list[int]]] = []
    current_name = ""
    current_columns: list[int] = []
    for column in range(6, max(len(heading_row), len(rows[1]))):
        heading = clean_text(heading_row[column] if column < len(heading_row) else "")
        if heading:
            if current_name and current_columns:
                groups.append((current_name, current_columns))
            current_name = heading
            current_columns = [column]
        elif current_name:
            current_columns.append(column)
    if current_name and current_columns:
        groups.append((current_name, current_columns))
    return [(name, columns) for name, columns in groups if is_target_contest(name)]


def materialize_candidates(candidate_labels: list[Any], votes: list[int]) -> list[dict[str, Any]]:
    candidates = []
    for label, vote in zip(candidate_labels, votes):
        candidate, party = parse_candidate_label(label)
        if not candidate:
            continue
        candidates.append({"candidate": candidate, "party": party, "votes": vote})
    return sorted(candidates, key=lambda item: item["votes"], reverse=True)


def build_sheet_contests(
    workbook: OhioSourceWorkbook,
    rows: list[list[Any]],
    county_lookup: dict[str, dict[str, str]],
    contest_start_id: int,
) -> tuple[list[dict[str, Any]], int]:
    if len(rows) < 5:
        raise RuntimeError(f"Ohio workbook sheet has too few rows for {workbook.election_name}")
    contests = []
    contest_id = contest_start_id
    header = rows[1]
    total_row = rows[2]
    county_rows = [row for row in rows[4:] if row and clean_text(row[0]) and normalize_county_name(row[0]) in county_lookup]
    for contest_name, columns in group_contest_columns(rows):
        office, district_number, district_label = office_for_contest(contest_name)
        candidate_labels = [header[column] if column < len(header) else "" for column in columns]
        contest_candidates = materialize_candidates(candidate_labels, [int_value(total_row[column] if column < len(total_row) else 0) for column in columns])
        counties = []
        county_vote_totals = [0] * len(columns)
        for row in county_rows:
            raw_votes = [int_value(row[column] if column < len(row) else 0) for column in columns]
            if not any(raw_votes):
                continue
            county_info = county_lookup[normalize_county_name(row[0])]
            county_candidates = materialize_candidates(candidate_labels, raw_votes)
            county_total = sum(candidate["votes"] for candidate in county_candidates)
            for index, vote in enumerate(raw_votes):
                county_vote_totals[index] += vote
            counties.append(
                {
                    "fips": county_info["fips"],
                    "county_name": county_info["county_name"],
                    "total_votes": county_total,
                    "winner": county_candidates[0],
                    "margin_votes": county_candidates[0]["votes"] - county_candidates[1]["votes"] if len(county_candidates) > 1 else 0,
                    "candidates": county_candidates,
                }
            )
        workbook_totals = [candidate["votes"] for candidate in materialize_candidates(candidate_labels, [int_value(total_row[column] if column < len(total_row) else 0) for column in columns])]
        county_totals_sorted = [candidate["votes"] for candidate in materialize_candidates(candidate_labels, county_vote_totals)]
        if workbook_totals != county_totals_sorted:
            raise RuntimeError(f"County totals do not match Ohio workbook totals for {contest_name}")
        total_votes = sum(candidate["votes"] for candidate in contest_candidates)
        contest: dict[str, Any] = {
            "contest_id": contest_id,
            "office": office,
            "name": f"Ohio {workbook.year} {district_label or office}",
            "state": "Ohio",
            "state_po": "OH",
            "year": workbook.year,
            "election_date": workbook.election_date,
            "source_election_name": workbook.election_name,
            "source_url": workbook.source_url,
            "source_format": "ohio-sos-xlsx",
            "quality_grade": "A",
            "total_votes": total_votes,
            "winner": contest_candidates[0],
            "margin_votes": contest_candidates[0]["votes"] - contest_candidates[1]["votes"] if len(contest_candidates) > 1 else 0,
            "candidates": contest_candidates,
            "counties": counties,
        }
        if district_number is not None:
            contest["district_number"] = district_number
            contest["district_label"] = district_label
        contests.append(contest)
        contest_id += 1
    return contests, contest_id


def build_election_summary(workbook: OhioSourceWorkbook, county_lookup: dict[str, dict[str, str]], contest_start_id: int) -> tuple[dict[str, Any], int]:
    sheets = read_xlsx_sheets(ROOT_DIR / workbook.raw_path)
    contests = []
    contest_id = contest_start_id
    for sheet_name in workbook.sheets:
        sheet_contests, contest_id = build_sheet_contests(workbook, sheets[sheet_name], county_lookup, contest_id)
        contests.extend(sheet_contests)
    return (
        {
            "source": {
                "name": "Ohio Secretary of State official statewide results by county",
                "url": workbook.source_url,
                "official": True,
                "quality_grade": "A",
            },
            "election": {
                "state": "Ohio",
                "state_po": "OH",
                "year": workbook.year,
                "election_date": workbook.election_date,
                "name": workbook.election_name,
            },
            "contests": contests,
        },
        contest_id,
    )


def build_summary() -> dict[str, Any]:
    county_lookup = load_ohio_counties()
    elections = []
    contest_id = 1
    for workbook in OHIO_WORKBOOKS:
        election, contest_id = build_election_summary(workbook, county_lookup, contest_id)
        elections.append(election)
    return {
        "source": {
            "name": "Ohio Secretary of State official statewide results by county",
            "url": "https://data.ohiosos.gov/portal/past-election-results",
            "official": True,
            "quality_grade": "A",
        },
        "state_po": "OH",
        "elections": elections,
    }


def main() -> None:
    summary = build_summary()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    contest_count = sum(len(election["contests"]) for election in summary["elections"])
    print(f"Wrote {OUTPUT_PATH} with {contest_count} Ohio contests.")


if __name__ == "__main__":
    main()
