#!/usr/bin/env python3
"""Compatibility wrapper for Florida 2022 summary generation."""

from __future__ import annotations

import sys

from election_db import ROOT_DIR
from florida_precinct_config import election_for_year
from generate_florida_summary import OUTPUT_DIR, build_summary, write_summary


def main() -> int:
    election = election_for_year(2022)
    summary = build_summary(election)
    output_path = OUTPUT_DIR / "florida-2022-statewide-summary.json"
    write_summary(output_path, summary)
    print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {len(summary['contests'])} contests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
