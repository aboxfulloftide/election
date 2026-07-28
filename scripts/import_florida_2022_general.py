#!/usr/bin/env python3
"""Compatibility wrapper for the Florida 2022 general precinct import."""

from __future__ import annotations

import sys

from florida_precinct_config import election_for_year
from import_florida_general import import_election


def main() -> int:
    election = election_for_year(2022)
    stats = import_election(election)
    print(
        "Imported Florida 2022 general precinct results: "
        f"{stats['rows']} rows, {stats['contests']} contests, {stats['counties']} counties, "
        f"{stats['precincts']} precincts (source_file_id={stats['source_file_id']})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
