#!/usr/bin/env python3
"""Audit Florida precinct result/geometry joins before map publication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
BUNDLE_DIR = ROOT_DIR / "public/results/precincts"
ALLOWED_OFFICES = {"President", "U.S. Senate", "U.S. House", "Governor", "State Senate", "State House"}


def audit_bundle(path: Path) -> dict[str, Any]:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    geometry = bundle["geometry"]
    result_ids = {row["precinct_id"] for contest in bundle["contests"] for row in contest["precincts"]}
    geometry_path = ROOT_DIR / "public" / geometry["geometry_url"].lstrip("/")
    geometry_ids = {feature["properties"]["precinct_id"] for feature in json.loads(geometry_path.read_text())["features"]}
    offices = sorted({contest["office"] for contest in bundle["contests"]})
    return {
        "bundle": str(path.relative_to(ROOT_DIR)),
        "county": bundle["county"],
        "year": bundle["election"]["year"],
        "offices": offices,
        "result_precinct_count": len(result_ids),
        "geometry_precinct_count": len(geometry_ids),
        "matched_result_precinct_count": len(result_ids & geometry_ids),
        "unmatched_result_precinct_count": len(result_ids - geometry_ids),
        "extra_geometry_precinct_count": len(geometry_ids - result_ids),
        "state_federal_only": set(offices) <= ALLOWED_OFFICES,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--require-complete", action="store_true", help="fail when any result precinct lacks geometry")
    parser.add_argument("--report", type=Path, help="write the audit reports as JSON")
    args = parser.parse_args()
    paths = sorted(BUNDLE_DIR.glob("florida-*-precincts.json")) if args.all or not args.paths else args.paths
    reports = [audit_bundle(path if path.is_absolute() else ROOT_DIR / path) for path in paths]
    failed = False
    for report in reports:
        print(
            f"{report['bundle']}: {report['matched_result_precinct_count']}/{report['result_precinct_count']} matched; "
            f"{report['unmatched_result_precinct_count']} unmatched; offices={','.join(report['offices'])}"
        )
        failed |= not report["state_federal_only"]
        failed |= args.require_complete and report["unmatched_result_precinct_count"] > 0
    if args.report:
        report_path = args.report if args.report.is_absolute() else ROOT_DIR / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"bundles": reports}, separators=(",", ":")), encoding="utf-8")
        print(f"Wrote {report_path.relative_to(ROOT_DIR)}.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
