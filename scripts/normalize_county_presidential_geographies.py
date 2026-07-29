#!/usr/bin/env python3
"""Normalize known county-presidential geography aliases in generated JSON."""

from __future__ import annotations

import json
import sys
from typing import Any

from election_db import ROOT_DIR
from fetch_results import SUMMARY_PATH


def append_unique(target: dict[str, Any], key: str, value: str) -> None:
    values = target.setdefault(key, [])
    if value not in values:
        values.append(value)


def merge_geography(summary: dict[str, Any], *, source_fips: str, target_fips: str, note: str) -> bool:
    counties = summary.get("counties", [])
    by_fips = {str(county["fips"]): county for county in counties}
    source = by_fips.get(source_fips)
    target = by_fips.get(target_fips)
    if source is None:
        return False
    if target is None:
        source["fips"] = target_fips
        append_unique(source, "fips_aliases", source_fips)
        source["geography_note"] = note
        return True

    append_unique(target, "fips_aliases", source_fips)
    if source.get("county_name") and source.get("county_name") != target.get("county_name"):
        append_unique(target, "previous_names", str(source["county_name"]))
    target["geography_note"] = note

    target_results = target.setdefault("results", {})
    for year, source_result in source.get("results", {}).items():
        target_result = target_results.get(year)
        if target_result is None or (target_result.get("totalvotes") == 0 and source_result.get("totalvotes", 0) > 0):
            target_results[year] = source_result
            continue
        if source_result.get("totalvotes", 0) > 0 and target_result.get("totalvotes") != source_result.get("totalvotes"):
            raise RuntimeError(f"Conflicting results for geography alias {source_fips} -> {target_fips} in {year}")

    summary["counties"] = [county for county in counties if str(county["fips"]) != source_fips]
    return True


def mark_inactive(summary: dict[str, Any], *, fips: str, valid_to_year: int, reason: str) -> bool:
    for county in summary.get("counties", []):
        if str(county.get("fips")) == fips:
            county["valid_to_year"] = valid_to_year
            county["inactive_reason"] = reason
            return True
    return False


def normalize_summary(summary: dict[str, Any]) -> dict[str, int]:
    stats = {"merged": 0, "marked_inactive": 0}

    if merge_geography(
        summary,
        source_fips="36000",
        target_fips="2938000",
        note="MIT 2024 uses FIPS-like code 36000 for the Kansas City, Missouri split row; merged into the existing Kansas City comparison row.",
    ):
        stats["merged"] += 1

    if merge_geography(
        summary,
        source_fips="46113",
        target_fips="46102",
        note="Shannon County was renamed/re-coded as Oglala Lakota County; historical Shannon results are merged into the current Oglala Lakota comparison row.",
    ):
        stats["merged"] += 1

    if mark_inactive(
        summary,
        fips="51515",
        valid_to_year=2012,
        reason="Bedford City, Virginia reverted to town status after the 2012 presidential election cycle and is not a separate modern reporting geography.",
    ):
        stats["marked_inactive"] += 1

    summary["counties"].sort(key=lambda item: str(item["fips"]))
    return stats


def main() -> int:
    output_path = ROOT_DIR / SUMMARY_PATH
    summary = json.loads(output_path.read_text(encoding="utf-8"))
    stats = normalize_summary(summary)
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(
        "Normalized county presidential geographies: "
        f"{stats['merged']} alias rows merged, {stats['marked_inactive']} inactive rows marked."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
