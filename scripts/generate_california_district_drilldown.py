#!/usr/bin/env python3
"""Generate California district contest bundles linked to district geometry."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR


RESULTS_DIR = ROOT_DIR / "public/results"
OUTPUT_DIR = RESULTS_DIR / "districts"
OUTPUT_PATH = OUTPUT_DIR / "california-district-drilldown.json"
GEOMETRY_LINKED_YEARS = {2022, 2024}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_contest(contest: dict[str, Any], geometry: dict[str, Any]) -> dict[str, Any]:
    return {
        "contest_id": contest["contest_id"],
        "name": contest["name"],
        "office": contest["office"],
        "district_label": contest["district_label"],
        "district_number": contest["district_number"],
        "geometry_id": geometry["geometry_id"],
        "geometry_official_id": geometry["official_id"],
        "total_votes": contest["total_votes"],
        "winner": contest["winner"],
        "margin_votes": contest["margin_votes"],
        "candidates": contest["candidates"],
        "counties": contest["counties"],
    }


def geometry_index(layer: dict[str, Any]) -> dict[int, dict[str, Any]]:
    collection = load_json(RESULTS_DIR / "geometry" / f"{layer['layer_key']}.geojson")
    return {
        int(feature["properties"]["district_number"]): feature["properties"]
        for feature in collection["features"]
        if isinstance(feature, dict)
    }


def build_election_bundle(election_summary: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    contests = [contest for contest in election_summary["contests"] if contest.get("district_number")]
    contests_by_office: dict[str, list[dict[str, Any]]] = {}
    for contest in contests:
        contests_by_office.setdefault(contest["office"], []).append(contest)

    layers = []
    for layer in manifest["layers"]:
        indexed_geometry = geometry_index(layer)
        office_contests = contests_by_office.get(layer["office"], [])
        compacted = []
        for contest in sorted(office_contests, key=lambda row: int(row["district_number"])):
            geometry = indexed_geometry.get(int(contest["district_number"]))
            if geometry is None:
                raise RuntimeError(f"Missing geometry for {contest['office']} district {contest['district_number']}")
            compacted.append(compact_contest(contest, geometry))
        layers.append(
            {
                "layer_key": layer["layer_key"],
                "office": layer["office"],
                "geo_type": layer["geo_type"],
                "geometry_url": layer["geometry_url"],
                "feature_count": layer["feature_count"],
                "contest_count": len(compacted),
                "contests": compacted,
            }
        )
    return {
        "source": election_summary["source"],
        "election": election_summary["election"],
        "state": "California",
        "state_po": "CA",
        "layers": layers,
    }


def build_bundle() -> dict[str, Any]:
    summary = load_json(RESULTS_DIR / "california-statewide-summary.json")
    manifest = load_json(RESULTS_DIR / "california-geometry-layers.json")
    geometry_linked_elections = [
        election_summary
        for election_summary in summary["elections"]
        if election_summary.get("election", {}).get("year") in GEOMETRY_LINKED_YEARS
    ]
    return {
        "source": summary["source"],
        "state": "California",
        "state_po": "CA",
        "elections": [build_election_bundle(election_summary, manifest) for election_summary in geometry_linked_elections],
    }


def main() -> int:
    bundle = build_bundle()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(bundle, separators=(",", ":")), encoding="utf-8")
    contest_count = sum(layer["contest_count"] for election in bundle["elections"] for layer in election["layers"])
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT_DIR)} with {len(bundle['elections'])} elections and {contest_count} contests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
