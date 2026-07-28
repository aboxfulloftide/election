#!/usr/bin/env python3
"""Validate the normalized MIT county presidential import."""

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
            "years": scalar(
                cursor,
                """
                SELECT COUNT(DISTINCT e.year) AS value
                FROM results r
                JOIN contests c ON c.id = r.contest_id
                JOIN elections e ON e.id = c.election_id
                JOIN offices o ON o.id = c.office_id
                WHERE o.name = 'President' AND o.level = 'federal'
                """,
            ),
            "counties": scalar(
                cursor,
                """
                SELECT COUNT(DISTINCT ru.county_fips) AS value
                FROM results r
                JOIN reporting_units ru ON ru.id = r.reporting_unit_id
                JOIN contests c ON c.id = r.contest_id
                JOIN offices o ON o.id = c.office_id
                WHERE o.name = 'President' AND o.level = 'federal' AND ru.unit_type = 'county'
                """,
            ),
            "result_rows": scalar(
                cursor,
                """
                SELECT COUNT(*) AS value
                FROM results r
                JOIN contests c ON c.id = r.contest_id
                JOIN offices o ON o.id = c.office_id
                WHERE o.name = 'President' AND o.level = 'federal'
                """,
            ),
            "missing_fips": scalar(
                cursor,
                """
                SELECT COUNT(*) AS value
                FROM reporting_units
                WHERE unit_type = 'county' AND (county_fips IS NULL OR county_fips = '')
                """,
            ),
            "missing_source_files": scalar(
                cursor,
                """
                SELECT COUNT(*) AS value
                FROM results r
                LEFT JOIN source_files sf ON sf.id = r.source_file_id
                WHERE sf.id IS NULL
                """,
            ),
            "duplicate_result_keys": scalar(
                cursor,
                """
                SELECT COUNT(*) AS value
                FROM (
                  SELECT r.contest_id, r.contest_candidate_id, r.reporting_unit_id, r.vote_mode, r.source_file_id
                  FROM results r
                  GROUP BY r.contest_id, r.contest_candidate_id, r.reporting_unit_id, r.vote_mode, r.source_file_id
                  HAVING COUNT(*) > 1
                ) duplicates
                """,
            ),
        }

        print("MIT county presidential validation:")
        for key, value in checks.items():
            print(f"  {key}: {value}")

        failed = []
        if checks["years"] != 7:
            failed.append("expected 7 presidential years from 2000-2024")
        if checks["counties"] < 3000:
            failed.append("expected at least 3000 county reporting units")
        if checks["result_rows"] == 0:
            failed.append("expected imported result rows")
        if checks["missing_fips"] != 0:
            failed.append("expected no missing county FIPS among county reporting units")
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

