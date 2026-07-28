#!/usr/bin/env python3
"""Validate Florida 2022 general statewide contest imports."""

from __future__ import annotations

import sys
from typing import Any

from election_db import connect


def scalar(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> int:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return int(next(iter(row.values()))) if row else 0


def main() -> int:
    connection = connect()
    cursor = connection.cursor(dictionary=True)
    try:
        checks = {
            "contests": scalar(
                cursor,
                """
                SELECT COUNT(DISTINCT c.id) AS value
                FROM contests c
                JOIN elections e ON e.id = c.election_id
                JOIN offices o ON o.id = c.office_id
                JOIN jurisdictions j ON j.id = c.contest_jurisdiction_id
                WHERE e.year = 2022
                  AND e.election_type = 'general'
                  AND j.state_po = 'FL'
                  AND o.name IN ('U.S. Senate', 'Governor')
                """,
            ),
            "counties": scalar(
                cursor,
                """
                SELECT COUNT(DISTINCT ru.county_fips) AS value
                FROM results r
                JOIN contests c ON c.id = r.contest_id
                JOIN elections e ON e.id = c.election_id
                JOIN offices o ON o.id = c.office_id
                JOIN reporting_units ru ON ru.id = r.reporting_unit_id
                WHERE e.year = 2022
                  AND e.election_type = 'general'
                  AND ru.state_po = 'FL'
                  AND o.name IN ('U.S. Senate', 'Governor')
                """,
            ),
            "precincts": scalar(
                cursor,
                """
                SELECT COUNT(DISTINCT ru.id) AS value
                FROM results r
                JOIN contests c ON c.id = r.contest_id
                JOIN elections e ON e.id = c.election_id
                JOIN offices o ON o.id = c.office_id
                JOIN reporting_units ru ON ru.id = r.reporting_unit_id
                WHERE e.year = 2022
                  AND e.election_type = 'general'
                  AND ru.unit_type = 'precinct'
                  AND ru.state_po = 'FL'
                  AND o.name IN ('U.S. Senate', 'Governor')
                """,
            ),
            "result_rows": scalar(
                cursor,
                """
                SELECT COUNT(*) AS value
                FROM results r
                JOIN contests c ON c.id = r.contest_id
                JOIN elections e ON e.id = c.election_id
                JOIN offices o ON o.id = c.office_id
                JOIN reporting_units ru ON ru.id = r.reporting_unit_id
                WHERE e.year = 2022
                  AND e.election_type = 'general'
                  AND ru.state_po = 'FL'
                  AND o.name IN ('U.S. Senate', 'Governor')
                """,
            ),
            "missing_source_files": scalar(
                cursor,
                """
                SELECT COUNT(*) AS value
                FROM results r
                JOIN contests c ON c.id = r.contest_id
                JOIN elections e ON e.id = c.election_id
                JOIN offices o ON o.id = c.office_id
                JOIN reporting_units ru ON ru.id = r.reporting_unit_id
                LEFT JOIN source_files sf ON sf.id = r.source_file_id
                WHERE e.year = 2022
                  AND e.election_type = 'general'
                  AND ru.state_po = 'FL'
                  AND o.name IN ('U.S. Senate', 'Governor')
                  AND sf.id IS NULL
                """,
            ),
            "duplicate_result_keys": scalar(
                cursor,
                """
                SELECT COUNT(*) AS value
                FROM (
                  SELECT r.contest_id, r.contest_candidate_id, r.reporting_unit_id, r.vote_mode, r.source_file_id
                  FROM results r
                  JOIN contests c ON c.id = r.contest_id
                  JOIN elections e ON e.id = c.election_id
                  JOIN offices o ON o.id = c.office_id
                  JOIN reporting_units ru ON ru.id = r.reporting_unit_id
                  WHERE e.year = 2022
                    AND e.election_type = 'general'
                    AND ru.state_po = 'FL'
                    AND o.name IN ('U.S. Senate', 'Governor')
                  GROUP BY r.contest_id, r.contest_candidate_id, r.reporting_unit_id, r.vote_mode, r.source_file_id
                  HAVING COUNT(*) > 1
                ) duplicates
                """,
            ),
        }

        print("Florida 2022 general validation:")
        for key, value in checks.items():
            print(f"  {key}: {value}")

        failed = []
        if checks["contests"] != 2:
            failed.append("expected 2 contests: U.S. Senate and Governor")
        if checks["counties"] != 67:
            failed.append("expected all 67 Florida counties")
        if checks["precincts"] != 6013:
            failed.append("expected 6013 precinct-location reporting units")
        if checks["result_rows"] != 60120:
            failed.append("expected 60120 candidate/write-in precinct result rows")
        if checks["missing_source_files"] != 0:
            failed.append("expected every result to reference a source file")
        if checks["duplicate_result_keys"] != 0:
            failed.append("expected no duplicate result keys")

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
