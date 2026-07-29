#!/usr/bin/env python3
"""Generate Florida district/county drilldown bundles from committed summaries."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR


RESULTS_DIR = ROOT_DIR / "public/results"
OUTPUT_DIR = RESULTS_DIR / "districts"
SUPPORTED_YEARS = (2022, 2024)
OFFICE_BY_LAYER = {
    "fl-2022-congressional-districts": "U.S. House",
    "fl-2022-state-house-districts": "State House",
    "fl-2022-state-senate-districts": "State Senate",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_geometry_layers() -> dict[str, dict[str, Any]]:
    manifest = load_json(RESULTS_DIR / "florida-geometry-layers.json")
    return {layer["layer_key"]: layer for layer in manifest["layers"]}


def compact_contest(contest: dict[str, Any]) -> dict[str, Any]:
    geometry = contest["geometry"]
    return {
        "contest_id": contest["contest_id"],
        "name": contest["name"],
        "office": contest["office"],
        "district_label": contest["district_label"],
        "district_number": geometry["district_number"],
        "geometry_id": geometry["geometry_id"],
        "geometry_official_id": geometry["official_id"],
        "total_votes": contest["total_votes"],
        "winner": contest["winner"],
        "margin_votes": contest["margin_votes"],
        "candidates": contest["candidates"],
        "counties": contest["counties"],
    }


def build_year_bundle(year: int, geometry_layers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary = load_json(RESULTS_DIR / f"florida-{year}-statewide-summary.json")
    contests = [contest for contest in summary["contests"] if "geometry" in contest]
    by_layer: dict[str, list[dict[str, Any]]] = {}
    for contest in contests:
        by_layer.setdefault(contest["geometry"]["layer_key"], []).append(compact_contest(contest))

    layers = []
    for layer_key in sorted(by_layer):
        source_layer = geometry_layers[layer_key]
        contests_for_layer = sorted(by_layer[layer_key], key=lambda contest: contest["district_number"])
        layers.append(
            {
                "layer_key": layer_key,
                "office": OFFICE_BY_LAYER[layer_key],
                "geo_type": source_layer["geo_type"],
                "geometry_url": source_layer["geometry_url"],
                "feature_count": source_layer["feature_count"],
                "contest_count": len(contests_for_layer),
                "contests": contests_for_layer,
            }
        )

    return {
        "source": {
            "name": summary["source"]["name"],
            "url": summary["source"]["url"],
            "source_file_url": summary["source"].get("source_file_url"),
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "quality_grade": summary["source"]["quality_grade"],
        },
        "election": summary["election"],
        "state": "Florida",
        "state_po": "FL",
        "layers": layers,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, choices=SUPPORTED_YEARS, help="Florida general election year to generate.")
    parser.add_argument("--all", action="store_true", help="Generate every supported Florida district drilldown bundle.")
    args = parser.parse_args()

    years = SUPPORTED_YEARS if args.all or args.year is None else (args.year,)
    geometry_layers = load_geometry_layers()
    year_bundles = []
    for year in years:
        bundle = build_year_bundle(year, geometry_layers)
        year_bundles.append(bundle)
        output_path = OUTPUT_DIR / f"florida-{year}-district-drilldown.json"
        write_json(output_path, bundle)
        contest_count = sum(layer["contest_count"] for layer in bundle["layers"])
        print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {contest_count} district contests.")

    if args.all or args.year is None:
        combined = {
            "source": {
                "name": "Florida Division of Elections",
                "url": "https://dos.fl.gov/elections/data-statistics/elections-data/precinct-level-election-results/",
                "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
                "quality_grade": "A",
            },
            "state": "Florida",
            "state_po": "FL",
            "elections": year_bundles,
        }
        output_path = OUTPUT_DIR / "florida-district-drilldown.json"
        write_json(output_path, combined)
        print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {len(year_bundles)} elections.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
