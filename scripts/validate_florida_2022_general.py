#!/usr/bin/env python3
"""Compatibility wrapper for Florida 2022 general validation."""

from __future__ import annotations

import sys

from election_db import connect
from florida_precinct_config import election_for_year
from validate_florida_general import validate_election


def main() -> int:
    connection = connect()
    cursor = connection.cursor(dictionary=True)
    try:
        failures = validate_election(cursor, election_for_year(2022))
        if failures:
            for message in failures:
                print(f"ERROR: Florida 2022: {message}", file=sys.stderr)
            return 1
        return 0
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
