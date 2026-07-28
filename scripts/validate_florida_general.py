#!/usr/bin/env python3
"""Validate official Florida statewide general-election precinct imports."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from election_db import connect
from florida_precinct_config import FloridaGeneralElection, selected_elections
from import_florida_general import iter_target_rows


def scalar(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> int:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return int(next(iter(row.values()))) if row else 0


def placeholders(values: set[str]) -> str:
    return ", ".join(["%s"] * len(values))


def validate_election(cursor: Any, election: FloridaGeneralElection) -> list[str]:
    office_names = set(election.target_contests.values())
    office_sql = placeholders(office_names)
    office_params = tuple(sorted(office_names))
    expected_rows = len(iter_target_rows(election))
    expected_contests = len(set(election.target_contests.values()))

    checks = {
        "contests": scalar(
            cursor,
            f"""
            SELECT COUNT(DISTINCT c.id) AS value
            FROM results r
            JOIN source_files sf ON sf.id = r.source_file_id
            JOIN contests c ON c.id = r.contest_id
            JOIN elections e ON e.id = c.election_id
            JOIN offices o ON o.id = c.office_id
            JOIN reporting_units ru ON ru.id = r.reporting_unit_id
            WHERE sf.url = %s
              AND e.year = %s
              AND e.election_type = 'general'
              AND ru.state_po = 'FL'
              AND o.name IN ({office_sql})
            """,
            (election.url, election.year, *office_params),
        ),
        "counties": scalar(
            cursor,
            f"""
            SELECT COUNT(DISTINCT ru.county_fips) AS value
            FROM results r
            JOIN source_files sf ON sf.id = r.source_file_id
            JOIN contests c ON c.id = r.contest_id
            JOIN elections e ON e.id = c.election_id
            JOIN offices o ON o.id = c.office_id
            JOIN reporting_units ru ON ru.id = r.reporting_unit_id
            WHERE sf.url = %s
              AND e.year = %s
              AND e.election_type = 'general'
              AND ru.state_po = 'FL'
              AND o.name IN ({office_sql})
            """,
            (election.url, election.year, *office_params),
        ),
        "precincts": scalar(
            cursor,
            f"""
            SELECT COUNT(DISTINCT ru.id) AS value
            FROM results r
            JOIN source_files sf ON sf.id = r.source_file_id
            JOIN contests c ON c.id = r.contest_id
            JOIN elections e ON e.id = c.election_id
            JOIN offices o ON o.id = c.office_id
            JOIN reporting_units ru ON ru.id = r.reporting_unit_id
            WHERE sf.url = %s
              AND e.year = %s
              AND e.election_type = 'general'
              AND ru.unit_type = 'precinct'
              AND ru.state_po = 'FL'
              AND o.name IN ({office_sql})
            """,
            (election.url, election.year, *office_params),
        ),
        "result_rows": scalar(
            cursor,
            f"""
            SELECT COUNT(*) AS value
            FROM results r
            JOIN source_files sf ON sf.id = r.source_file_id
            JOIN contests c ON c.id = r.contest_id
            JOIN elections e ON e.id = c.election_id
            JOIN offices o ON o.id = c.office_id
            JOIN reporting_units ru ON ru.id = r.reporting_unit_id
            WHERE sf.url = %s
              AND e.year = %s
              AND e.election_type = 'general'
              AND ru.state_po = 'FL'
              AND o.name IN ({office_sql})
            """,
            (election.url, election.year, *office_params),
        ),
        "duplicate_result_keys": scalar(
            cursor,
            f"""
            SELECT COUNT(*) AS value
            FROM (
              SELECT r.contest_id, r.contest_candidate_id, r.reporting_unit_id, r.vote_mode, r.source_file_id
              FROM results r
              JOIN source_files sf ON sf.id = r.source_file_id
              JOIN contests c ON c.id = r.contest_id
              JOIN elections e ON e.id = c.election_id
              JOIN offices o ON o.id = c.office_id
              JOIN reporting_units ru ON ru.id = r.reporting_unit_id
              WHERE sf.url = %s
                AND e.year = %s
                AND e.election_type = 'general'
                AND ru.state_po = 'FL'
                AND o.name IN ({office_sql})
              GROUP BY r.contest_id, r.contest_candidate_id, r.reporting_unit_id, r.vote_mode, r.source_file_id
              HAVING COUNT(*) > 1
            ) duplicates
            """,
            (election.url, election.year, *office_params),
        ),
    }

    print(f"Florida {election.year} general validation:")
    for key, value in checks.items():
        print(f"  {key}: {value}")

    failed = []
    if checks["contests"] != expected_contests:
        failed.append(f"expected {expected_contests} contests")
    if checks["counties"] != 67:
        failed.append("expected all 67 Florida counties")
    if checks["precincts"] <= 0:
        failed.append("expected precinct reporting units")
    if checks["result_rows"] != expected_rows:
        failed.append(f"expected {expected_rows} candidate/write-in precinct result rows")
    if checks["duplicate_result_keys"] != 0:
        failed.append("expected no duplicate result keys")
    return failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, help="Florida general election year to validate. Defaults to 2022.")
    parser.add_argument("--all", action="store_true", help="Validate every configured Florida general election.")
    args = parser.parse_args()

    connection = connect()
    cursor = connection.cursor(dictionary=True)
    try:
        failed: list[str] = []
        for election in selected_elections(args.year, args.all):
            failed.extend(f"Florida {election.year}: {message}" for message in validate_election(cursor, election))
        if failed:
            for message in failed:
                print(f"ERROR: {message}", file=sys.stderr)
            return 1
        return 0
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
