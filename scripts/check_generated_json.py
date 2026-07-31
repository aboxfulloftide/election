#!/usr/bin/env python3
"""Validate committed app-ready JSON result files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from generate_county_presidential_coverage import COVERAGE_PATH, build_coverage


ROOT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT_DIR / "public/results"
FLORIDA_YEARS = {2012, 2014, 2016, 2018, 2020, 2022, 2024}
FLORIDA_GEOMETRY_LAYERS = {
    "fl-2022-congressional-districts": ("congressional_district", "P000C0109"),
    "fl-2022-state-house-districts": ("state_house_district", "H000H8013"),
    "fl-2022-state-senate-districts": ("state_senate_district", "S027S8058"),
}
FLORIDA_OFFICE_GEOMETRY_LAYERS = {
    "U.S. House": "fl-2022-congressional-districts",
    "State House": "fl-2022-state-house-districts",
    "State Senate": "fl-2022-state-senate-districts",
}
FLORIDA_DISTRICT_DRILLDOWN_YEARS = {2022, 2024}
CALIFORNIA_YEARS = {2018, 2020, 2022, 2024}
CALIFORNIA_GEOMETRY_LINKED_YEARS = {2022, 2024}
CALIFORNIA_GEOMETRY_LAYERS = {
    "ca-2022-congressional-districts": ("congressional_district", 52),
    "ca-2022-state-assembly-districts": ("state_assembly_district", 80),
    "ca-2022-state-senate-districts": ("state_senate_district", 40),
}
CALIFORNIA_DISTRICT_OFFICES = {"U.S. House", "State Senate", "State Assembly"}
FLORIDA_MAYOR_PLACES = {"Hialeah", "Jacksonville", "Miami", "Miami Beach", "Orlando", "Sunny Isles Beach", "Tampa"}
PENNSYLVANIA_YEARS = {2020, 2022, 2024}
PENNSYLVANIA_EXPECTED_OFFICE_COUNTS = {
    2024: {"President": 1, "U.S. Senate": 1, "U.S. House": 17, "State Senate": 25, "State House": 203},
    2022: {"Governor": 1, "U.S. Senate": 1, "U.S. House": 17, "State Senate": 25, "State House": 203},
    2020: {"President": 1, "U.S. House": 18, "State Senate": 25, "State House": 203},
}
TEXAS_YEARS = {2018, 2020, 2022, 2024}
TEXAS_EXPECTED_OFFICE_COUNTS = {
    2018: {"Governor": 1, "U.S. Senate": 1, "U.S. House": 36, "State Senate": 15, "State House": 150},
    2020: {"President": 1, "U.S. Senate": 1, "U.S. House": 36, "State Senate": 16, "State House": 150},
    2022: {"Governor": 1, "U.S. House": 38, "State Senate": 21, "State House": 92},
    2024: {"President": 1, "U.S. Senate": 1, "U.S. House": 38, "State Senate": 15, "State House": 150},
}
TEXAS_MAYOR_YEARS = {
    1981,
    1983,
    1985,
    1987,
    1989,
    1991,
    1995,
    1999,
    2001,
    2002,
    2003,
    2005,
    2007,
    2009,
    2011,
    2013,
    2015,
    2017,
    2019,
    2021,
    2022,
    2023,
    2024,
    2025,
}
TEXAS_MAYOR_PLACES = {"Austin", "Dallas", "Fort Worth", "Houston", "San Antonio"}
TEXAS_CURRENT_YEAR = 2026
TEXAS_CURRENT_OFFICES = {"U.S. Senate", "U.S. House", "State Senate", "State House"}
OHIO_YEARS = {2020, 2022, 2024}
OHIO_EXPECTED_OFFICE_COUNTS = {
    2020: {"President": 1, "U.S. House": 16, "State Senate": 16, "State House": 99},
    2022: {"Governor": 1, "U.S. Senate": 1, "U.S. House": 15, "State Senate": 17, "State House": 99},
    2024: {"President": 1, "U.S. Senate": 1, "U.S. House": 15, "State Senate": 16, "State House": 99},
}


class CheckFailure(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CheckFailure(f"{path.relative_to(ROOT_DIR)} is missing") from exc
    except json.JSONDecodeError as exc:
        raise CheckFailure(f"{path.relative_to(ROOT_DIR)} is not valid JSON: {exc}") from exc


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def require_int(value: Any, label: str, *, minimum: int = 0) -> None:
    require(isinstance(value, int), f"{label} must be an integer")
    require(value >= minimum, f"{label} must be >= {minimum}")


def require_source(source: Any, path: Path) -> None:
    path_label = display_path(path)
    require(isinstance(source, dict), f"{path_label} source must be an object")
    require(isinstance(source.get("name"), str) and source["name"], f"{path_label} source.name is required")
    require(isinstance(source.get("quality_grade"), str), f"{path_label} source.quality_grade is required")


def validate_candidate(candidate: Any, label: str) -> int:
    require(isinstance(candidate, dict), f"{label} must be an object")
    require(isinstance(candidate.get("candidate"), str) and candidate["candidate"], f"{label}.candidate is required")
    require(isinstance(candidate.get("party"), str) and candidate["party"], f"{label}.party is required")
    require_int(candidate.get("votes"), f"{label}.votes")
    return int(candidate["votes"])


def validate_florida_contests(summary: dict[str, Any], path: Path) -> None:
    require_source(summary.get("source"), path)
    election = summary.get("election")
    path_label = display_path(path)
    require(isinstance(election, dict), f"{path_label} election must be an object")
    require(election.get("state_po") in (None, "FL"), f"{path_label} election state must be Florida")
    require_int(election.get("year"), f"{path_label} election.year", minimum=1900)

    contests = summary.get("contests")
    require(isinstance(contests, list) and contests, f"{path_label} contests must be a non-empty list")
    seen_contests: set[int] = set()

    for index, contest in enumerate(contests):
        label = f"{path_label} contests[{index}]"
        require(isinstance(contest, dict), f"{label} must be an object")
        require_int(contest.get("contest_id"), f"{label}.contest_id", minimum=1)
        require(contest["contest_id"] not in seen_contests, f"{label}.contest_id is duplicated")
        seen_contests.add(contest["contest_id"])
        require(isinstance(contest.get("office"), str) and contest["office"], f"{label}.office is required")
        require(contest.get("state_po") == "FL", f"{label}.state_po must be FL")
        validate_florida_contest_geometry(contest, int(election["year"]), label)

        candidates = contest.get("candidates")
        require(isinstance(candidates, list) and candidates, f"{label}.candidates must be non-empty")
        candidate_votes = [validate_candidate(candidate, f"{label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
        require(candidate_votes == sorted(candidate_votes, reverse=True), f"{label}.candidates must be sorted by votes desc")
        require_int(contest.get("total_votes"), f"{label}.total_votes")
        require(sum(candidate_votes) == contest["total_votes"], f"{label}.total_votes must equal candidate vote sum")
        require(contest.get("winner") == candidates[0], f"{label}.winner must be the top candidate")
        expected_margin = candidate_votes[0] - candidate_votes[1] if len(candidate_votes) > 1 else 0
        require(contest.get("margin_votes") == expected_margin, f"{label}.margin_votes is incorrect")

        county_vote_total = 0
        counties = contest.get("counties")
        require(isinstance(counties, list), f"{label}.counties must be a list")
        for county_index, county in enumerate(counties):
            county_label = f"{label}.counties[{county_index}]"
            require(isinstance(county, dict), f"{county_label} must be an object")
            require(isinstance(county.get("fips"), str) and len(county["fips"]) == 5, f"{county_label}.fips must be a 5-character string")
            require(isinstance(county.get("county_name"), str) and county["county_name"], f"{county_label}.county_name is required")
            county_candidates = county.get("candidates")
            require(isinstance(county_candidates, list) and county_candidates, f"{county_label}.candidates must be non-empty")
            votes = [
                validate_candidate(candidate, f"{county_label}.candidates[{candidate_index}]")
                for candidate_index, candidate in enumerate(county_candidates)
            ]
            require_int(county.get("total_votes"), f"{county_label}.total_votes")
            require(sum(votes) == county["total_votes"], f"{county_label}.total_votes must equal candidate vote sum")
            require(county.get("winner") == county_candidates[0], f"{county_label}.winner must be the top candidate")
            county_vote_total += county["total_votes"]
        require(county_vote_total == contest["total_votes"], f"{label}.counties must sum to contest total_votes")


def validate_florida_contest_geometry(contest: dict[str, Any], year: int, label: str) -> None:
    office = contest["office"]
    district_label = contest.get("district_label")
    expected_layer_key = FLORIDA_OFFICE_GEOMETRY_LAYERS.get(office)
    if expected_layer_key is None or district_label is None:
        require("geometry" not in contest, f"{label}.geometry should only be present for district contests")
        return

    if year < 2022:
        require("geometry" not in contest, f"{label}.geometry should not use 2022 geometry for pre-2022 contests")
        return

    geometry = contest.get("geometry")
    require(isinstance(geometry, dict), f"{label}.geometry is required for 2022-cycle district contests")
    require_int(geometry.get("geometry_id"), f"{label}.geometry.geometry_id", minimum=1)
    require(geometry.get("layer_key") == expected_layer_key, f"{label}.geometry.layer_key is incorrect")
    require(geometry.get("geometry_url") == f"/results/geometry/{expected_layer_key}.geojson", f"{label}.geometry.geometry_url is incorrect")
    require(isinstance(geometry.get("official_id"), str) and geometry["official_id"].startswith("FL:"), f"{label}.geometry.official_id is required")
    require_int(geometry.get("district_number"), f"{label}.geometry.district_number", minimum=1)
    require(geometry.get("valid_from") == 2022, f"{label}.geometry.valid_from must be 2022")


def validate_county_presidential(path: Path) -> None:
    summary = load_json(path)
    require(isinstance(summary, dict), f"{path.relative_to(ROOT_DIR)} must be an object")
    require_source(summary.get("source"), path)
    years = summary.get("years")
    require(isinstance(years, list) and years, "county presidential years must be a non-empty list")
    require(years == sorted(years), "county presidential years must be sorted")
    require(all(isinstance(year, int) for year in years), "county presidential years must be integers")

    counties = summary.get("counties")
    require(isinstance(counties, list) and counties, "county presidential counties must be non-empty")
    seen_fips: set[str] = set()
    for index, county in enumerate(counties):
        label = f"{path.relative_to(ROOT_DIR)} counties[{index}]"
        require(isinstance(county, dict), f"{label} must be an object")
        fips = county.get("fips")
        require(
            isinstance(fips, str) and fips.isdigit() and 5 <= len(fips) <= 7,
            f"{label}.fips must be a 5- to 7-digit geography id",
        )
        require(fips not in seen_fips, f"{label}.fips is duplicated")
        seen_fips.add(fips)
        require(isinstance(county.get("state_po"), str) and len(county["state_po"]) == 2, f"{label}.state_po is required")
        require(isinstance(county.get("county_name"), str) and county["county_name"], f"{label}.county_name is required")
        results = county.get("results")
        require(isinstance(results, dict) and results, f"{label}.results must be non-empty")
        for year, result in results.items():
            result_label = f"{label}.results[{year}]"
            require(str(year).isdigit(), f"{result_label} key must be a year")
            require(isinstance(result, dict), f"{result_label} must be an object")
            parties = result.get("parties")
            require(isinstance(parties, dict) and parties, f"{result_label}.parties must be non-empty")
            party_votes = {party: votes for party, votes in parties.items()}
            for party, votes in party_votes.items():
                require(isinstance(party, str) and party, f"{result_label}.parties has an empty party")
                require_int(votes, f"{result_label}.parties[{party}]")
            require_int(result.get("totalvotes"), f"{result_label}.totalvotes")
            ordered = sorted(party_votes.items(), key=lambda item: item[1], reverse=True)
            require(result.get("winner_party") == ordered[0][0], f"{result_label}.winner_party is incorrect")
            require(result.get("winner_votes") == ordered[0][1], f"{result_label}.winner_votes is incorrect")
            expected_margin = ordered[0][1] - ordered[1][1] if len(ordered) > 1 else 0
            require(result.get("margin_votes") == expected_margin, f"{result_label}.margin_votes is incorrect")
            if result.get("supplemental"):
                require(isinstance(result.get("source_name"), str) and result["source_name"], f"{result_label}.source_name is required for supplemental rows")
                require(isinstance(result.get("source_url"), str) and result["source_url"].startswith("https://"), f"{result_label}.source_url is required for supplemental rows")
                require(isinstance(result.get("quality_grade"), str) and result["quality_grade"], f"{result_label}.quality_grade is required for supplemental rows")
            if result.get("official"):
                require(isinstance(result.get("source_name"), str) and result["source_name"], f"{result_label}.source_name is required for official rows")
                require(isinstance(result.get("source_url"), str) and result["source_url"].startswith("https://"), f"{result_label}.source_url is required for official rows")
                require(isinstance(result.get("quality_grade"), str) and result["quality_grade"], f"{result_label}.quality_grade is required for official rows")


def validate_county_presidential_coverage(summary_path: Path, coverage_path: Path) -> None:
    summary = load_json(summary_path)
    coverage = load_json(coverage_path)
    expected = build_coverage(summary)
    require(coverage == expected, f"{display_path(coverage_path)} is stale or does not match {display_path(summary_path)}")


def validate_florida_year_file(path: Path) -> None:
    summary = load_json(path)
    require(isinstance(summary, dict), f"{path.relative_to(ROOT_DIR)} must be an object")
    validate_florida_contests(summary, path)


def validate_florida_combined(path: Path) -> None:
    summary = load_json(path)
    require(isinstance(summary, dict), f"{path.relative_to(ROOT_DIR)} must be an object")
    require_source(summary.get("source"), path)
    elections = summary.get("elections")
    require(isinstance(elections, list) and elections, "combined Florida elections must be non-empty")
    years = {election.get("election", {}).get("year") for election in elections if isinstance(election, dict)}
    require(years == FLORIDA_YEARS, f"combined Florida years must be {sorted(FLORIDA_YEARS)}")
    for index, election_summary in enumerate(elections):
        validate_florida_contests(election_summary, Path(f"{display_path(path)}#elections[{index}]"))


def validate_california_combined(path: Path) -> None:
    summary = load_json(path)
    path_label = display_path(path)
    require(isinstance(summary, dict), f"{path_label} must be an object")
    require_source(summary.get("source"), path)
    elections = summary.get("elections")
    require(isinstance(elections, list) and elections, f"{path_label}.elections must be non-empty")
    years = {election.get("election", {}).get("year") for election in elections if isinstance(election, dict)}
    require(years == CALIFORNIA_YEARS, f"{path_label}.elections must cover {sorted(CALIFORNIA_YEARS)}")
    for election_index, election_summary in enumerate(elections):
        election_label = f"{path_label}.elections[{election_index}]"
        require(isinstance(election_summary, dict), f"{election_label} must be an object")
        require_source(election_summary.get("source"), Path(election_label))
        election = election_summary.get("election")
        require(isinstance(election, dict), f"{election_label}.election must be an object")
        require(election.get("year") in CALIFORNIA_YEARS, f"{election_label}.election.year must be a supported California year")
        require(election.get("state") == "California", f"{election_label}.election.state must be California")
        contests = election_summary.get("contests")
        require(isinstance(contests, list) and contests, f"{election_label}.contests must be non-empty")
        for contest_index, contest in enumerate(contests):
            label = f"{election_label}.contests[{contest_index}]"
            require(isinstance(contest, dict), f"{label} must be an object")
            require(contest.get("state_po") == "CA", f"{label}.state_po must be CA")
            require(isinstance(contest.get("office"), str) and contest["office"], f"{label}.office is required")
            require_int(contest.get("contest_id"), f"{label}.contest_id", minimum=1)
            candidates = contest.get("candidates")
            require(isinstance(candidates, list) and candidates, f"{label}.candidates must be non-empty")
            candidate_votes = [validate_candidate(candidate, f"{label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
            require(candidate_votes == sorted(candidate_votes, reverse=True), f"{label}.candidates must be sorted by votes desc")
            require_int(contest.get("total_votes"), f"{label}.total_votes", minimum=1)
            require(sum(candidate_votes) == contest["total_votes"], f"{label}.total_votes must equal candidate vote sum")
            district_label = contest.get("district_label")
            if district_label is None:
                require("district_number" not in contest, f"{label}.district_number should only be present for district contests")
            else:
                require(isinstance(district_label, str) and district_label, f"{label}.district_label is required")
                require_int(contest.get("district_number"), f"{label}.district_number", minimum=1)
            counties = contest.get("counties")
            require(isinstance(counties, list) and counties, f"{label}.counties must be non-empty")
            if district_label is None:
                require(len(counties) == 58, f"{label}.counties must contain 58 counties")
            county_total = 0
            for county_index, county in enumerate(counties):
                county_label = f"{label}.counties[{county_index}]"
                require(isinstance(county, dict), f"{county_label} must be an object")
                require(isinstance(county.get("fips"), str) and len(county["fips"]) == 5, f"{county_label}.fips must be a 5-character string")
                require(county["fips"].startswith("06"), f"{county_label}.fips must be a California FIPS")
                require(isinstance(county.get("county_name"), str) and county["county_name"], f"{county_label}.county_name is required")
                county_candidates = county.get("candidates")
                require(isinstance(county_candidates, list) and county_candidates, f"{county_label}.candidates must be non-empty")
                votes = [validate_candidate(candidate, f"{county_label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(county_candidates)]
                require_int(county.get("total_votes"), f"{county_label}.total_votes")
                require(sum(votes) == county["total_votes"], f"{county_label}.total_votes must equal candidate vote sum")
                county_total += county["total_votes"]
            require(county_total == contest["total_votes"], f"{label}.counties must sum to contest total_votes")


def validate_florida_mayors(path: Path) -> None:
    summary = load_json(path)
    path_label = display_path(path)
    require(isinstance(summary, dict), f"{path_label} must be an object")
    require_source(summary.get("source"), path)
    require(summary.get("state_po") == "FL", f"{path_label}.state_po must be FL")
    elections = summary.get("elections")
    require(isinstance(elections, list) and elections, f"{path_label}.elections must be non-empty")
    seen_contest_ids: set[int] = set()
    seen_places: set[str] = set()
    contest_total = 0
    for election_index, election_summary in enumerate(elections):
        election_label = f"{path_label}.elections[{election_index}]"
        require(isinstance(election_summary, dict), f"{election_label} must be an object")
        require_source(election_summary.get("source"), Path(election_label))
        election = election_summary.get("election")
        require(isinstance(election, dict), f"{election_label}.election must be an object")
        require(election.get("state_po") == "FL", f"{election_label}.election.state_po must be FL")
        require(isinstance(election.get("county"), str) and election["county"], f"{election_label}.election.county is required")
        require(isinstance(election.get("county_fips"), str) and len(election["county_fips"]) == 5, f"{election_label}.election.county_fips is required")
        contests = election_summary.get("contests")
        require(isinstance(contests, list), f"{election_label}.contests must be a list")
        for contest_index, contest in enumerate(contests):
            contest_total += 1
            label = f"{election_label}.contests[{contest_index}]"
            require(isinstance(contest, dict), f"{label} must be an object")
            require_int(contest.get("contest_id"), f"{label}.contest_id", minimum=1)
            require(contest["contest_id"] not in seen_contest_ids, f"{label}.contest_id is duplicated")
            seen_contest_ids.add(contest["contest_id"])
            require(contest.get("state_po") == "FL", f"{label}.state_po must be FL")
            require(contest.get("county") == election["county"], f"{label}.county must match election county")
            require(contest.get("county_fips") == election["county_fips"], f"{label}.county_fips must match election county_fips")
            require(isinstance(contest.get("place"), str) and contest["place"], f"{label}.place is required")
            seen_places.add(contest["place"])
            require(contest.get("office") == "Mayor", f"{label}.office must be Mayor")
            require(contest.get("election_stage") in {"general", "runoff", "special"}, f"{label}.election_stage is invalid")
            require(isinstance(contest.get("source_url"), str) and contest["source_url"].startswith("https://"), f"{label}.source_url is required")
            candidates = contest.get("candidates")
            require(isinstance(candidates, list) and candidates, f"{label}.candidates must be non-empty")
            votes = [validate_candidate(candidate, f"{label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
            require(votes == sorted(votes, reverse=True), f"{label}.candidates must be sorted by votes desc")
            require_int(contest.get("total_votes"), f"{label}.total_votes", minimum=1)
            require(sum(votes) == contest["total_votes"], f"{label}.total_votes must equal candidate vote sum")
            require(contest.get("winner") == candidates[0], f"{label}.winner must be the top candidate")
            expected_margin = votes[0] - votes[1] if len(votes) > 1 else 0
            require(contest.get("margin_votes") == expected_margin, f"{label}.margin_votes is incorrect")
    require(contest_total >= 17, f"{path_label} should contain at least seventeen mayor contests")
    require(FLORIDA_MAYOR_PLACES <= seen_places, f"{path_label} is missing expected places: {sorted(FLORIDA_MAYOR_PLACES - seen_places)}")


def validate_pennsylvania_combined(path: Path) -> None:
    summary = load_json(path)
    path_label = display_path(path)
    require(isinstance(summary, dict), f"{path_label} must be an object")
    require_source(summary.get("source"), path)
    elections = summary.get("elections")
    require(isinstance(elections, list) and elections, f"{path_label}.elections must be non-empty")
    years = {election.get("election", {}).get("year") for election in elections if isinstance(election, dict)}
    require(years == PENNSYLVANIA_YEARS, f"{path_label}.elections must cover {sorted(PENNSYLVANIA_YEARS)}")
    for election_index, election_summary in enumerate(elections):
        election_label = f"{path_label}.elections[{election_index}]"
        require(isinstance(election_summary, dict), f"{election_label} must be an object")
        require_source(election_summary.get("source"), Path(election_label))
        election = election_summary.get("election")
        require(isinstance(election, dict), f"{election_label}.election must be an object")
        year = election.get("year")
        require(year in PENNSYLVANIA_YEARS, f"{election_label}.election.year is unsupported")
        require(election.get("state_po") == "PA", f"{election_label}.election.state_po must be PA")
        contests = election_summary.get("contests")
        require(isinstance(contests, list) and contests, f"{election_label}.contests must be non-empty")
        office_counts: dict[str, int] = {}
        for contest_index, contest in enumerate(contests):
            label = f"{election_label}.contests[{contest_index}]"
            require(isinstance(contest, dict), f"{label} must be an object")
            require(contest.get("state_po") == "PA", f"{label}.state_po must be PA")
            office = contest.get("office")
            require(isinstance(office, str) and office, f"{label}.office is required")
            office_counts[office] = office_counts.get(office, 0) + 1
            require_int(contest.get("contest_id"), f"{label}.contest_id", minimum=1)
            candidates = contest.get("candidates")
            require(isinstance(candidates, list) and candidates, f"{label}.candidates must be non-empty")
            votes = [validate_candidate(candidate, f"{label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
            require(votes == sorted(votes, reverse=True), f"{label}.candidates must be sorted by votes desc")
            require_int(contest.get("total_votes"), f"{label}.total_votes", minimum=1)
            require(sum(votes) == contest["total_votes"], f"{label}.total_votes must equal candidate vote sum")
            require(contest.get("winner") == candidates[0], f"{label}.winner must be the top candidate")
            expected_margin = votes[0] - votes[1] if len(votes) > 1 else 0
            require(contest.get("margin_votes") == expected_margin, f"{label}.margin_votes is incorrect")
            if office in {"U.S. House", "State Senate", "State House"}:
                require(isinstance(contest.get("district_label"), str) and contest["district_label"], f"{label}.district_label is required")
                require_int(contest.get("district_number"), f"{label}.district_number", minimum=1)
            counties = contest.get("counties")
            require(isinstance(counties, list) and counties, f"{label}.counties must be non-empty")
            if office in {"President", "Governor", "U.S. Senate"}:
                require(len(counties) == 67, f"{label}.counties must include all 67 counties")
            county_total = 0
            for county_index, county in enumerate(counties):
                county_label = f"{label}.counties[{county_index}]"
                require(isinstance(county, dict), f"{county_label} must be an object")
                require(isinstance(county.get("fips"), str) and county["fips"].startswith("42"), f"{county_label}.fips must be a Pennsylvania FIPS")
                require(isinstance(county.get("county_name"), str) and county["county_name"], f"{county_label}.county_name is required")
                county_candidates = county.get("candidates")
                require(isinstance(county_candidates, list) and county_candidates, f"{county_label}.candidates must be non-empty")
                county_votes = [validate_candidate(candidate, f"{county_label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(county_candidates)]
                require_int(county.get("total_votes"), f"{county_label}.total_votes")
                require(sum(county_votes) == county["total_votes"], f"{county_label}.total_votes must equal candidate vote sum")
                county_total += county["total_votes"]
            require(county_total == contest["total_votes"], f"{label}.counties must sum to contest total_votes")
        require(office_counts == PENNSYLVANIA_EXPECTED_OFFICE_COUNTS[year], f"{election_label}.office counts are incorrect: {office_counts}")


def validate_texas_combined(path: Path) -> None:
    summary = load_json(path)
    path_label = display_path(path)
    require(isinstance(summary, dict), f"{path_label} must be an object")
    require_source(summary.get("source"), path)
    elections = summary.get("elections")
    require(isinstance(elections, list) and elections, f"{path_label}.elections must be non-empty")
    years = {election.get("election", {}).get("year") for election in elections if isinstance(election, dict)}
    require(years == TEXAS_YEARS, f"{path_label}.elections must cover {sorted(TEXAS_YEARS)}")
    for election_index, election_summary in enumerate(elections):
        election_label = f"{path_label}.elections[{election_index}]"
        require(isinstance(election_summary, dict), f"{election_label} must be an object")
        require_source(election_summary.get("source"), Path(election_label))
        election = election_summary.get("election")
        require(isinstance(election, dict), f"{election_label}.election must be an object")
        year = election.get("year")
        require(year in TEXAS_YEARS, f"{election_label}.election.year is unsupported")
        require(election.get("state_po") == "TX", f"{election_label}.election.state_po must be TX")
        contests = election_summary.get("contests")
        require(isinstance(contests, list) and contests, f"{election_label}.contests must be non-empty")
        office_counts: dict[str, int] = {}
        seen_contest_ids: set[int] = set()
        for contest_index, contest in enumerate(contests):
            label = f"{election_label}.contests[{contest_index}]"
            require(isinstance(contest, dict), f"{label} must be an object")
            require(contest.get("state_po") == "TX", f"{label}.state_po must be TX")
            office = contest.get("office")
            require(isinstance(office, str) and office, f"{label}.office is required")
            office_counts[office] = office_counts.get(office, 0) + 1
            require_int(contest.get("contest_id"), f"{label}.contest_id", minimum=1)
            require(contest["contest_id"] not in seen_contest_ids, f"{label}.contest_id is duplicated")
            seen_contest_ids.add(contest["contest_id"])
            candidates = contest.get("candidates")
            require(isinstance(candidates, list) and candidates, f"{label}.candidates must be non-empty")
            votes = [validate_candidate(candidate, f"{label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
            require(votes == sorted(votes, reverse=True), f"{label}.candidates must be sorted by votes desc")
            require_int(contest.get("total_votes"), f"{label}.total_votes", minimum=1)
            require(sum(votes) == contest["total_votes"], f"{label}.total_votes must equal candidate vote sum")
            require(contest.get("winner") == candidates[0], f"{label}.winner must be the top candidate")
            expected_margin = votes[0] - votes[1] if len(votes) > 1 else 0
            require(contest.get("margin_votes") == expected_margin, f"{label}.margin_votes is incorrect")
            if office in {"U.S. House", "State Senate", "State House"}:
                require(isinstance(contest.get("district_label"), str) and contest["district_label"], f"{label}.district_label is required")
                require_int(contest.get("district_number"), f"{label}.district_number", minimum=1)
            counties = contest.get("counties")
            require(isinstance(counties, list) and counties, f"{label}.counties must be non-empty")
            if office in {"President", "Governor", "U.S. Senate"}:
                require(len(counties) == 254, f"{label}.counties must include all 254 Texas counties")
            county_total = 0
            for county_index, county in enumerate(counties):
                county_label = f"{label}.counties[{county_index}]"
                require(isinstance(county, dict), f"{county_label} must be an object")
                require(isinstance(county.get("fips"), str) and county["fips"].startswith("48"), f"{county_label}.fips must be a Texas FIPS")
                require(isinstance(county.get("county_name"), str) and county["county_name"], f"{county_label}.county_name is required")
                county_candidates = county.get("candidates")
                require(isinstance(county_candidates, list) and county_candidates, f"{county_label}.candidates must be non-empty")
                county_votes = [validate_candidate(candidate, f"{county_label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(county_candidates)]
                require_int(county.get("total_votes"), f"{county_label}.total_votes")
                require(sum(county_votes) == county["total_votes"], f"{county_label}.total_votes must equal candidate vote sum")
                county_total += county["total_votes"]
            require(county_total == contest["total_votes"], f"{label}.counties must sum to contest total_votes")
        require(office_counts == TEXAS_EXPECTED_OFFICE_COUNTS[year], f"{election_label}.office counts are incorrect: {office_counts}")


def validate_texas_mayors(path: Path) -> None:
    summary = load_json(path)
    path_label = display_path(path)
    require(isinstance(summary, dict), f"{path_label} must be an object")
    require_source(summary.get("source"), path)
    require(summary.get("state_po") == "TX", f"{path_label}.state_po must be TX")
    places = summary.get("places")
    require(isinstance(places, list) and places, f"{path_label}.places must be non-empty")
    seen_places: set[str] = set()
    seen_years: set[int] = set()
    seen_contest_ids: set[int] = set()
    contest_total = 0
    for place_index, place_summary in enumerate(places):
        place_label = f"{path_label}.places[{place_index}]"
        require(isinstance(place_summary, dict), f"{place_label} must be an object")
        require_source(place_summary.get("source"), Path(place_label))
        require(place_summary.get("state_po") == "TX", f"{place_label}.state_po must be TX")
        place = place_summary.get("place")
        require(isinstance(place, str) and place, f"{place_label}.place is required")
        seen_places.add(place)
        contests = place_summary.get("contests")
        require(isinstance(contests, list) and contests, f"{place_label}.contests must be non-empty")
        for contest_index, contest in enumerate(contests):
            contest_total += 1
            label = f"{place_label}.contests[{contest_index}]"
            require(isinstance(contest, dict), f"{label} must be an object")
            require_int(contest.get("contest_id"), f"{label}.contest_id", minimum=1)
            require(contest["contest_id"] not in seen_contest_ids, f"{label}.contest_id is duplicated")
            seen_contest_ids.add(contest["contest_id"])
            require(contest.get("state_po") == "TX", f"{label}.state_po must be TX")
            require(contest.get("place") == place, f"{label}.place must match parent place")
            require(contest.get("office") == "Mayor", f"{label}.office must be Mayor")
            require(contest.get("election_stage") in {"general", "runoff", "special"}, f"{label}.election_stage is invalid")
            year = contest.get("year")
            require(year in TEXAS_MAYOR_YEARS, f"{label}.year is unsupported")
            seen_years.add(year)
            require(isinstance(contest.get("election_date"), str) and contest["election_date"], f"{label}.election_date is required")
            require(isinstance(contest.get("source_url"), str) and contest["source_url"].startswith("https://"), f"{label}.source_url is required")
            candidates = contest.get("candidates")
            require(isinstance(candidates, list) and candidates, f"{label}.candidates must be non-empty")
            votes = [validate_candidate(candidate, f"{label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
            require(votes == sorted(votes, reverse=True), f"{label}.candidates must be sorted by votes desc")
            require_int(contest.get("total_votes"), f"{label}.total_votes", minimum=1)
            require(sum(votes) == contest["total_votes"], f"{label}.total_votes must equal candidate vote sum")
            require(contest.get("winner") == candidates[0], f"{label}.winner must be the top candidate")
            expected_margin = votes[0] - votes[1] if len(votes) > 1 else 0
            require(contest.get("margin_votes") == expected_margin, f"{label}.margin_votes is incorrect")
            county_portions = contest.get("county_portions")
            require(isinstance(county_portions, list), f"{label}.county_portions must be a list")
    require(TEXAS_MAYOR_PLACES <= seen_places, f"{path_label} is missing expected places: {sorted(TEXAS_MAYOR_PLACES - seen_places)}")
    require(TEXAS_MAYOR_YEARS <= seen_years, f"{path_label} is missing expected years: {sorted(TEXAS_MAYOR_YEARS - seen_years)}")
    require(contest_total >= 63, f"{path_label} should contain at least sixty-three mayor contests")


def validate_texas_current(path: Path) -> None:
    summary = load_json(path)
    path_label = display_path(path)
    require(isinstance(summary, dict), f"{path_label} must be an object")
    require_source(summary.get("source"), path)
    require(summary.get("scope") == "statewide_current", f"{path_label}.scope must be statewide_current")
    require(summary.get("geography") == "statewide", f"{path_label}.geography must be statewide")
    election = summary.get("election")
    require(isinstance(election, dict), f"{path_label}.election must be an object")
    require(election.get("state_po") == "TX", f"{path_label}.election.state_po must be TX")
    require(election.get("year") == TEXAS_CURRENT_YEAR, f"{path_label}.election.year must be {TEXAS_CURRENT_YEAR}")
    contests = summary.get("contests")
    require(isinstance(contests, list) and contests, f"{path_label}.contests must be non-empty")
    seen_contest_ids: set[int] = set()
    offices: set[str] = set()
    for contest_index, contest in enumerate(contests):
        label = f"{path_label}.contests[{contest_index}]"
        require(isinstance(contest, dict), f"{label} must be an object")
        require_int(contest.get("contest_id"), f"{label}.contest_id", minimum=1)
        require(contest["contest_id"] not in seen_contest_ids, f"{label}.contest_id is duplicated")
        seen_contest_ids.add(contest["contest_id"])
        require(contest.get("state_po") == "TX", f"{label}.state_po must be TX")
        office = contest.get("office")
        require(office in TEXAS_CURRENT_OFFICES, f"{label}.office is unsupported")
        offices.add(office)
        require(contest.get("year") == TEXAS_CURRENT_YEAR, f"{label}.year must be {TEXAS_CURRENT_YEAR}")
        require(contest.get("election_stage") == "primary_runoff", f"{label}.election_stage must be primary_runoff")
        require(contest.get("source_format") == "current-results-html", f"{label}.source_format is incorrect")
        candidates = contest.get("candidates")
        require(isinstance(candidates, list) and len(candidates) >= 2, f"{label}.candidates must contain at least two candidates")
        votes = [validate_candidate(candidate, f"{label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
        require(votes == sorted(votes, reverse=True), f"{label}.candidates must be sorted by votes desc")
        require_int(contest.get("total_votes"), f"{label}.total_votes", minimum=1)
        require(sum(votes) == contest["total_votes"], f"{label}.total_votes must equal candidate vote sum")
        require(contest.get("winner") == candidates[0], f"{label}.winner must be the top candidate")
        expected_margin = votes[0] - votes[1]
        require(contest.get("margin_votes") == expected_margin, f"{label}.margin_votes is incorrect")
        require(contest.get("counties") == [], f"{label}.counties must be empty for statewide-only current HTML")
        if office in {"U.S. House", "State Senate", "State House"}:
            require_int(contest.get("district_number"), f"{label}.district_number", minimum=1)
            require(isinstance(contest.get("district_label"), str) and contest["district_label"], f"{label}.district_label is required")
    require("U.S. Senate" in offices, f"{path_label} must include U.S. Senate")
    require("U.S. House" in offices, f"{path_label} must include U.S. House")


def validate_ohio_combined(path: Path) -> None:
    summary = load_json(path)
    path_label = display_path(path)
    require(isinstance(summary, dict), f"{path_label} must be an object")
    require_source(summary.get("source"), path)
    require(summary.get("state_po") == "OH", f"{path_label}.state_po must be OH")
    elections = summary.get("elections")
    require(isinstance(elections, list) and elections, f"{path_label}.elections must be non-empty")
    years = {election.get("election", {}).get("year") for election in elections if isinstance(election, dict)}
    require(years == OHIO_YEARS, f"{path_label}.elections must cover {sorted(OHIO_YEARS)}")
    seen_contest_ids: set[int] = set()
    for election_index, election_summary in enumerate(elections):
        election_label = f"{path_label}.elections[{election_index}]"
        require(isinstance(election_summary, dict), f"{election_label} must be an object")
        require_source(election_summary.get("source"), Path(election_label))
        election = election_summary.get("election")
        require(isinstance(election, dict), f"{election_label}.election must be an object")
        year = election.get("year")
        require(year in OHIO_YEARS, f"{election_label}.election.year is unsupported")
        require(election.get("state_po") == "OH", f"{election_label}.election.state_po must be OH")
        contests = election_summary.get("contests")
        require(isinstance(contests, list) and contests, f"{election_label}.contests must be non-empty")
        office_counts: dict[str, int] = {}
        for contest_index, contest in enumerate(contests):
            label = f"{election_label}.contests[{contest_index}]"
            require(isinstance(contest, dict), f"{label} must be an object")
            require(contest.get("state_po") == "OH", f"{label}.state_po must be OH")
            require(contest.get("year") == year, f"{label}.year must match election year")
            office = contest.get("office")
            require(isinstance(office, str) and office, f"{label}.office is required")
            office_counts[office] = office_counts.get(office, 0) + 1
            require_int(contest.get("contest_id"), f"{label}.contest_id", minimum=1)
            require(contest["contest_id"] not in seen_contest_ids, f"{label}.contest_id is duplicated")
            seen_contest_ids.add(contest["contest_id"])
            candidates = contest.get("candidates")
            require(isinstance(candidates, list) and candidates, f"{label}.candidates must be non-empty")
            votes = [validate_candidate(candidate, f"{label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
            require(votes == sorted(votes, reverse=True), f"{label}.candidates must be sorted by votes desc")
            require_int(contest.get("total_votes"), f"{label}.total_votes", minimum=1)
            require(sum(votes) == contest["total_votes"], f"{label}.total_votes must equal candidate vote sum")
            require(contest.get("winner") == candidates[0], f"{label}.winner must be the top candidate")
            expected_margin = votes[0] - votes[1] if len(votes) > 1 else 0
            require(contest.get("margin_votes") == expected_margin, f"{label}.margin_votes is incorrect")
            if office in {"U.S. House", "State Senate", "State House"}:
                require(isinstance(contest.get("district_label"), str) and contest["district_label"], f"{label}.district_label is required")
                require_int(contest.get("district_number"), f"{label}.district_number", minimum=1)
            counties = contest.get("counties")
            require(isinstance(counties, list) and counties, f"{label}.counties must be a list")
            if office in {"President", "U.S. Senate"}:
                require(len(counties) == 88, f"{label}.counties must include all 88 Ohio counties")
            require(counties, f"{label}.counties must be non-empty")
            county_total = 0
            for county_index, county in enumerate(counties):
                county_label = f"{label}.counties[{county_index}]"
                require(isinstance(county, dict), f"{county_label} must be an object")
                require(isinstance(county.get("fips"), str) and county["fips"].startswith("39"), f"{county_label}.fips must be an Ohio FIPS")
                require(isinstance(county.get("county_name"), str) and county["county_name"], f"{county_label}.county_name is required")
                county_candidates = county.get("candidates")
                require(isinstance(county_candidates, list) and county_candidates, f"{county_label}.candidates must be non-empty")
                county_votes = [validate_candidate(candidate, f"{county_label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(county_candidates)]
                require(county_votes == sorted(county_votes, reverse=True), f"{county_label}.candidates must be sorted by votes desc")
                require_int(county.get("total_votes"), f"{county_label}.total_votes")
                require(sum(county_votes) == county["total_votes"], f"{county_label}.total_votes must equal candidate vote sum")
                require(county.get("winner") == county_candidates[0], f"{county_label}.winner must be the top candidate")
                county_total += county["total_votes"]
            require(county_total == contest["total_votes"], f"{label}.counties must sum to contest total_votes")
        require(office_counts == OHIO_EXPECTED_OFFICE_COUNTS[year], f"{election_label}.office counts are incorrect: {office_counts}")


def validate_geometry_manifest(path: Path) -> None:
    manifest = load_json(path)
    require(isinstance(manifest, dict), f"{path.relative_to(ROOT_DIR)} must be an object")
    require_source(manifest.get("source"), path)
    layers = manifest.get("layers")
    require(isinstance(layers, list), "geometry layers must be a list")
    layer_keys = {layer.get("layer_key") for layer in layers if isinstance(layer, dict)}
    require(layer_keys == set(FLORIDA_GEOMETRY_LAYERS), "geometry manifest must contain all configured Florida layers")
    for index, layer in enumerate(layers):
        label = f"{path.relative_to(ROOT_DIR)} layers[{index}]"
        require(isinstance(layer, dict), f"{label} must be an object")
        layer_key = layer.get("layer_key")
        require(layer_key in FLORIDA_GEOMETRY_LAYERS, f"{label}.layer_key is unknown")
        geo_type, plan_id = FLORIDA_GEOMETRY_LAYERS[layer_key]
        require(layer.get("geo_type") == geo_type, f"{label}.geo_type is incorrect")
        require(layer.get("official_plan_id") == plan_id, f"{label}.official_plan_id is incorrect")
        require(layer.get("state_po") == "FL", f"{label}.state_po must be FL")
        require(layer.get("valid_from") == 2022, f"{label}.valid_from must be 2022")
        require_int(layer.get("feature_count"), f"{label}.feature_count", minimum=1)
        expected_url = f"/results/geometry/{layer_key}.geojson"
        require(layer.get("geometry_url") == expected_url, f"{label}.geometry_url must be {expected_url}")
        validate_geometry_geojson(RESULTS_DIR / "geometry" / f"{layer_key}.geojson", layer, int(layer["feature_count"]))
        require(isinstance(layer.get("source_file_url"), str) and layer["source_file_url"].startswith("https://"), f"{label}.source_file_url is required")
        require(isinstance(layer.get("checksum_sha256"), str) and len(layer["checksum_sha256"]) == 64, f"{label}.checksum_sha256 must be SHA-256")


def validate_california_geometry_manifest(path: Path) -> None:
    manifest = load_json(path)
    path_label = display_path(path)
    require(isinstance(manifest, dict), f"{path_label} must be an object")
    require_source(manifest.get("source"), path)
    layers = manifest.get("layers")
    require(isinstance(layers, list), f"{path_label}.layers must be a list")
    layer_keys = {layer.get("layer_key") for layer in layers if isinstance(layer, dict)}
    require(layer_keys == set(CALIFORNIA_GEOMETRY_LAYERS), f"{path_label}.layers must contain all configured California layers")
    for index, layer in enumerate(layers):
        label = f"{path_label}.layers[{index}]"
        require(isinstance(layer, dict), f"{label} must be an object")
        layer_key = layer.get("layer_key")
        require(layer_key in CALIFORNIA_GEOMETRY_LAYERS, f"{label}.layer_key is unknown")
        expected_geo_type, expected_count = CALIFORNIA_GEOMETRY_LAYERS[layer_key]
        require(layer.get("geo_type") == expected_geo_type, f"{label}.geo_type is incorrect")
        require(layer.get("state_po") == "CA", f"{label}.state_po must be CA")
        require(layer.get("valid_from") == 2022, f"{label}.valid_from must be 2022")
        require_int(layer.get("feature_count"), f"{label}.feature_count", minimum=1)
        require(layer["feature_count"] == expected_count, f"{label}.feature_count must be {expected_count}")
        require(layer.get("geometry_url") == f"/results/geometry/{layer_key}.geojson", f"{label}.geometry_url is incorrect")
        require(layer.get("office") in CALIFORNIA_DISTRICT_OFFICES, f"{label}.office is incorrect")
        require(isinstance(layer.get("source_file_url"), str) and layer["source_file_url"].startswith("https://"), f"{label}.source_file_url is required")
        validate_california_geometry_geojson(RESULTS_DIR / "geometry" / f"{layer_key}.geojson", layer, expected_count)


def validate_california_geometry_geojson(path: Path, layer: dict[str, Any], expected_feature_count: int) -> None:
    collection = load_json(path)
    path_label = display_path(path)
    require(collection.get("type") == "FeatureCollection", f"{path_label}.type must be FeatureCollection")
    features = collection.get("features")
    require(isinstance(features, list), f"{path_label}.features must be a list")
    require(len(features) == expected_feature_count, f"{path_label}.features length must match expected count")
    seen_ids: set[str] = set()
    seen_numbers: set[int] = set()
    for index, feature in enumerate(features):
        label = f"{path_label}.features[{index}]"
        require(isinstance(feature, dict), f"{label} must be an object")
        feature_id = feature.get("id")
        require(isinstance(feature_id, str) and feature_id.startswith("CA:CRC2020:"), f"{label}.id must be a California CRC id")
        require(feature_id not in seen_ids, f"{label}.id is duplicated")
        seen_ids.add(feature_id)
        properties = feature.get("properties")
        require(isinstance(properties, dict), f"{label}.properties must be an object")
        require(properties.get("layer_key") == layer["layer_key"], f"{label}.properties.layer_key must match manifest")
        require(properties.get("geo_type") == layer["geo_type"], f"{label}.properties.geo_type must match manifest")
        require(properties.get("state_po") == "CA", f"{label}.properties.state_po must be CA")
        require_int(properties.get("geometry_id"), f"{label}.properties.geometry_id", minimum=1)
        require_int(properties.get("district_number"), f"{label}.properties.district_number", minimum=1)
        require(properties["district_number"] not in seen_numbers, f"{label}.properties.district_number is duplicated")
        seen_numbers.add(properties["district_number"])
        require(isinstance(properties.get("district_label"), str) and properties["district_label"], f"{label}.properties.district_label is required")
        geometry = feature.get("geometry")
        require(isinstance(geometry, dict), f"{label}.geometry must be an object")
        require(geometry.get("type") == "MultiPolygon", f"{label}.geometry.type must be MultiPolygon")
        require(isinstance(geometry.get("coordinates"), list) and geometry["coordinates"], f"{label}.geometry.coordinates must be non-empty")


def validate_geometry_geojson(path: Path, layer: dict[str, Any], expected_feature_count: int) -> None:
    collection = load_json(path)
    path_label = display_path(path)
    require(collection.get("type") == "FeatureCollection", f"{path_label}.type must be FeatureCollection")
    features = collection.get("features")
    require(isinstance(features, list), f"{path_label}.features must be a list")
    require(len(features) == expected_feature_count, f"{path_label}.features length must match manifest")
    seen_ids: set[str] = set()
    for index, feature in enumerate(features):
        label = f"{path_label}.features[{index}]"
        require(isinstance(feature, dict), f"{label} must be an object")
        feature_id = feature.get("id")
        require(isinstance(feature_id, str) and feature_id, f"{label}.id is required")
        require(feature_id not in seen_ids, f"{label}.id is duplicated")
        seen_ids.add(feature_id)
        properties = feature.get("properties")
        require(isinstance(properties, dict), f"{label}.properties must be an object")
        require(properties.get("layer_key") == layer["layer_key"], f"{label}.properties.layer_key must match manifest")
        require(properties.get("geo_type") == layer["geo_type"], f"{label}.properties.geo_type must match manifest")
        require(properties.get("official_plan_id") == layer["official_plan_id"], f"{label}.properties.official_plan_id must match manifest")
        require(isinstance(properties.get("district_label"), str) and properties["district_label"], f"{label}.properties.district_label is required")
        require_int(properties.get("district_number"), f"{label}.properties.district_number", minimum=1)
        geometry = feature.get("geometry")
        require(isinstance(geometry, dict), f"{label}.geometry must be an object")
        require(geometry.get("type") == "MultiPolygon", f"{label}.geometry.type must be MultiPolygon")
        coordinates = geometry.get("coordinates")
        require(isinstance(coordinates, list) and coordinates, f"{label}.geometry.coordinates must be non-empty")


def validate_florida_district_drilldown(path: Path) -> None:
    bundle = load_json(path)
    path_label = display_path(path)
    require(isinstance(bundle, dict), f"{path_label} must be an object")
    require_source(bundle.get("source"), path)
    require(bundle.get("state_po") == "FL", f"{path_label}.state_po must be FL")
    election = bundle.get("election")
    require(isinstance(election, dict), f"{path_label}.election must be an object")
    year = election.get("year")
    require(year in FLORIDA_DISTRICT_DRILLDOWN_YEARS, f"{path_label}.election.year must be a supported district year")
    layers = bundle.get("layers")
    require(isinstance(layers, list) and layers, f"{path_label}.layers must be non-empty")
    layer_keys = {layer.get("layer_key") for layer in layers if isinstance(layer, dict)}
    require(layer_keys == set(FLORIDA_GEOMETRY_LAYERS), f"{path_label}.layers must include all Florida district layers")
    for layer_index, layer in enumerate(layers):
        layer_label = f"{path_label}.layers[{layer_index}]"
        require(isinstance(layer, dict), f"{layer_label} must be an object")
        layer_key = layer.get("layer_key")
        require(layer_key in FLORIDA_GEOMETRY_LAYERS, f"{layer_label}.layer_key is unknown")
        expected_office = next(office for office, office_layer_key in FLORIDA_OFFICE_GEOMETRY_LAYERS.items() if office_layer_key == layer_key)
        require(layer.get("office") == expected_office, f"{layer_label}.office is incorrect")
        require(layer.get("geometry_url") == f"/results/geometry/{layer_key}.geojson", f"{layer_label}.geometry_url is incorrect")
        require_int(layer.get("feature_count"), f"{layer_label}.feature_count", minimum=1)
        contests = layer.get("contests")
        require(isinstance(contests, list) and contests, f"{layer_label}.contests must be non-empty")
        require(layer.get("contest_count") == len(contests), f"{layer_label}.contest_count must equal contests length")
        seen_geometry_ids: set[int] = set()
        for contest_index, contest in enumerate(contests):
            contest_label = f"{layer_label}.contests[{contest_index}]"
            require(isinstance(contest, dict), f"{contest_label} must be an object")
            require_int(contest.get("contest_id"), f"{contest_label}.contest_id", minimum=1)
            require(contest.get("office") == expected_office, f"{contest_label}.office is incorrect")
            require_int(contest.get("district_number"), f"{contest_label}.district_number", minimum=1)
            require_int(contest.get("geometry_id"), f"{contest_label}.geometry_id", minimum=1)
            require(contest["geometry_id"] not in seen_geometry_ids, f"{contest_label}.geometry_id is duplicated in layer")
            seen_geometry_ids.add(contest["geometry_id"])
            require(isinstance(contest.get("geometry_official_id"), str) and contest["geometry_official_id"].startswith("FL:"), f"{contest_label}.geometry_official_id is required")
            require_int(contest.get("total_votes"), f"{contest_label}.total_votes", minimum=1)
            candidates = contest.get("candidates")
            require(isinstance(candidates, list) and candidates, f"{contest_label}.candidates must be non-empty")
            votes = [validate_candidate(candidate, f"{contest_label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
            require(sum(votes) == contest["total_votes"], f"{contest_label}.total_votes must equal candidate vote sum")
            require(contest.get("winner") == candidates[0], f"{contest_label}.winner must be the top candidate")
            counties = contest.get("counties")
            require(isinstance(counties, list) and counties, f"{contest_label}.counties must be non-empty")


def validate_florida_district_drilldown_combined(path: Path) -> None:
    combined = load_json(path)
    path_label = display_path(path)
    require(isinstance(combined, dict), f"{path_label} must be an object")
    require_source(combined.get("source"), path)
    require(combined.get("state_po") == "FL", f"{path_label}.state_po must be FL")
    elections = combined.get("elections")
    require(isinstance(elections, list), f"{path_label}.elections must be a list")
    years = {election.get("election", {}).get("year") for election in elections if isinstance(election, dict)}
    require(years == FLORIDA_DISTRICT_DRILLDOWN_YEARS, f"{path_label}.elections must cover 2022 and 2024")
    for index, election in enumerate(elections):
        validate_florida_district_drilldown_object(election, f"{path_label}.elections[{index}]")


def validate_florida_district_drilldown_object(bundle: dict[str, Any], path_label: str) -> None:
    require(isinstance(bundle.get("election"), dict), f"{path_label}.election must be an object")
    require(bundle.get("state_po") == "FL", f"{path_label}.state_po must be FL")
    require(isinstance(bundle.get("layers"), list) and bundle["layers"], f"{path_label}.layers must be non-empty")


def validate_california_district_drilldown(path: Path) -> None:
    bundle = load_json(path)
    path_label = display_path(path)
    require(isinstance(bundle, dict), f"{path_label} must be an object")
    require_source(bundle.get("source"), path)
    require(bundle.get("state_po") == "CA", f"{path_label}.state_po must be CA")
    elections = bundle.get("elections")
    require(isinstance(elections, list) and elections, f"{path_label}.elections must be non-empty")
    years = {election.get("election", {}).get("year") for election in elections if isinstance(election, dict)}
    require(years == CALIFORNIA_GEOMETRY_LINKED_YEARS, f"{path_label}.elections must cover {sorted(CALIFORNIA_GEOMETRY_LINKED_YEARS)}")
    expected_contests = {
        "ca-2022-congressional-districts": 52,
        "ca-2022-state-senate-districts": 20,
        "ca-2022-state-assembly-districts": 80,
    }
    for election_index, election in enumerate(elections):
        election_label = f"{path_label}.elections[{election_index}]"
        require(isinstance(election, dict), f"{election_label} must be an object")
        require(election.get("state_po") == "CA", f"{election_label}.state_po must be CA")
        require(election.get("election", {}).get("year") in CALIFORNIA_GEOMETRY_LINKED_YEARS, f"{election_label}.election.year must be a geometry-linked California year")
        layers = election.get("layers")
        require(isinstance(layers, list) and layers, f"{election_label}.layers must be non-empty")
        layer_keys = {layer.get("layer_key") for layer in layers if isinstance(layer, dict)}
        require(layer_keys == set(CALIFORNIA_GEOMETRY_LAYERS), f"{election_label}.layers must include all California district layers")
        for layer_index, layer in enumerate(layers):
            layer_label = f"{election_label}.layers[{layer_index}]"
            require(isinstance(layer, dict), f"{layer_label} must be an object")
            layer_key = layer.get("layer_key")
            require(layer_key in CALIFORNIA_GEOMETRY_LAYERS, f"{layer_label}.layer_key is unknown")
            require(layer.get("geometry_url") == f"/results/geometry/{layer_key}.geojson", f"{layer_label}.geometry_url is incorrect")
            require_int(layer.get("feature_count"), f"{layer_label}.feature_count", minimum=1)
            require(layer["feature_count"] == CALIFORNIA_GEOMETRY_LAYERS[layer_key][1], f"{layer_label}.feature_count is incorrect")
            contests = layer.get("contests")
            require(isinstance(contests, list), f"{layer_label}.contests must be a list")
            require(layer.get("contest_count") == len(contests), f"{layer_label}.contest_count must equal contests length")
            require(len(contests) == expected_contests[layer_key], f"{layer_label}.contests length is incorrect")
            seen_districts: set[int] = set()
            for contest_index, contest in enumerate(contests):
                contest_label = f"{layer_label}.contests[{contest_index}]"
                require(isinstance(contest, dict), f"{contest_label} must be an object")
                require(contest.get("office") == layer["office"], f"{contest_label}.office must match layer")
                require_int(contest.get("district_number"), f"{contest_label}.district_number", minimum=1)
                require(contest["district_number"] not in seen_districts, f"{contest_label}.district_number is duplicated")
                seen_districts.add(contest["district_number"])
                require_int(contest.get("geometry_id"), f"{contest_label}.geometry_id", minimum=1)
                require(isinstance(contest.get("geometry_official_id"), str) and contest["geometry_official_id"].startswith("CA:CRC2020:"), f"{contest_label}.geometry_official_id is required")
                require_int(contest.get("total_votes"), f"{contest_label}.total_votes", minimum=1)
                candidates = contest.get("candidates")
                require(isinstance(candidates, list) and candidates, f"{contest_label}.candidates must be non-empty")
                votes = [validate_candidate(candidate, f"{contest_label}.candidates[{candidate_index}]") for candidate_index, candidate in enumerate(candidates)]
                require(sum(votes) == contest["total_votes"], f"{contest_label}.total_votes must equal candidate vote sum")
                require(contest.get("winner") == candidates[0], f"{contest_label}.winner must be the top candidate")
                counties = contest.get("counties")
                require(isinstance(counties, list) and counties, f"{contest_label}.counties must be non-empty")


def main() -> int:
    checks = [
        lambda: validate_county_presidential(RESULTS_DIR / "county-presidential-summary.json"),
        lambda: validate_county_presidential_coverage(RESULTS_DIR / "county-presidential-summary.json", ROOT_DIR / COVERAGE_PATH),
        lambda: validate_florida_combined(RESULTS_DIR / "florida-statewide-summary.json"),
        lambda: validate_california_combined(RESULTS_DIR / "california-statewide-summary.json"),
        lambda: validate_geometry_manifest(RESULTS_DIR / "florida-geometry-layers.json"),
        lambda: validate_california_geometry_manifest(RESULTS_DIR / "california-geometry-layers.json"),
        lambda: validate_florida_district_drilldown_combined(RESULTS_DIR / "districts/florida-district-drilldown.json"),
        lambda: validate_california_district_drilldown(RESULTS_DIR / "districts/california-district-drilldown.json"),
        lambda: validate_florida_mayors(RESULTS_DIR / "florida-mayor-summary.json"),
        lambda: validate_pennsylvania_combined(RESULTS_DIR / "pennsylvania-statewide-summary.json"),
        lambda: validate_ohio_combined(RESULTS_DIR / "ohio-statewide-summary.json"),
        lambda: validate_texas_combined(RESULTS_DIR / "texas-statewide-summary.json"),
        lambda: validate_texas_current(RESULTS_DIR / "texas-current-summary.json"),
        lambda: validate_texas_mayors(RESULTS_DIR / "texas-mayor-summary.json"),
    ]
    checks.extend(lambda path=path: validate_florida_year_file(path) for path in sorted(RESULTS_DIR.glob("florida-20??-statewide-summary.json")))
    checks.extend(
        lambda path=path: validate_florida_district_drilldown(path)
        for path in sorted((RESULTS_DIR / "districts").glob("florida-20??-district-drilldown.json"))
    )

    failures: list[str] = []
    for check in checks:
        try:
            check()
        except CheckFailure as exc:
            failures.append(str(exc))

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print("Generated JSON checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
