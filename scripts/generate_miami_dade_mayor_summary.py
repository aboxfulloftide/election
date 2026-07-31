#!/usr/bin/env python3
"""Compatibility wrapper for the Florida municipal mayor summary generator."""

from __future__ import annotations

from generate_florida_mayor_summary import (  # noqa: F401
    EnrSummaryParser,
    build_contest,
    build_summary,
    clean_text,
    fetch_html,
    int_value,
    is_yes_no_question,
    main,
    parse_mayor_races,
    place_from_race_name,
)


if __name__ == "__main__":
    main()
