#!/usr/bin/env python3
"""Generate app-ready California district GeoJSON files."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from california_geometry_config import CaliforniaGeometryLayer, selected_layers
from election_db import ROOT_DIR
from shapefile_geojson import read_polygon_features


OUTPUT_DIR = ROOT_DIR / "public/results/geometry"
MANIFEST_PATH = ROOT_DIR / "public/results/california-geometry-layers.json"


def ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def output_path_for_layer(layer: CaliforniaGeometryLayer):
    return OUTPUT_DIR / f"{layer.layer_key}.geojson"


def district_number(record: dict[str, Any]) -> int:
    value = record.get("DISTRICT_N", record.get("DISTRICT"))
    if value is None:
        raise RuntimeError(f"Missing district number in shapefile record: {record}")
    return int(value)


def geometry_id(layer: CaliforniaGeometryLayer, number: int) -> int:
    offset = {
        "congressional_district": 6000,
        "state_senate_district": 6100,
        "state_assembly_district": 6200,
    }[layer.geo_type]
    return offset + number


def district_label(layer: CaliforniaGeometryLayer, number: int) -> str:
    return f"{ordinal(number)} {layer.district_label_suffix}"


def geometry_collection(layer: CaliforniaGeometryLayer, features: list[tuple[dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "name": layer.layer_key,
        "features": [
            {
                "type": "Feature",
                "id": f"CA:CRC2020:{layer.geo_type}:{number}",
                "properties": {
                    "geometry_id": geometry_id(layer, number),
                    "layer_key": layer.layer_key,
                    "geo_type": layer.geo_type,
                    "official_plan_id": "CRC2020",
                    "official_id": f"CA:CRC2020:{layer.geo_type}:{number}",
                    "district_label": district_label(layer, number),
                    "district_number": number,
                    "name": district_label(layer, number),
                    "state_po": "CA",
                    "valid_from": layer.valid_from,
                    "valid_to": layer.valid_to,
                },
                "geometry": geometry,
            }
            for record, geometry in sorted(features, key=lambda item: district_number(item[0]))
            for number in [district_number(record)]
        ],
    }


def generate_layer(layer: CaliforniaGeometryLayer) -> int:
    if not layer.raw_path.exists():
        raise RuntimeError(f"Missing {layer.raw_path}. Run npm run california:geometry:download -- --all first.")
    features = read_polygon_features(layer.raw_path)
    if len(features) != layer.expected_features:
        raise RuntimeError(f"{layer.layer_key} has {len(features)} features; expected {layer.expected_features}")

    collection = geometry_collection(layer, features)
    output_path = output_path_for_layer(layer)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(collection, separators=(",", ":")), encoding="utf-8")
    return len(collection["features"])


def build_manifest() -> dict[str, Any]:
    return {
        "source": {
            "name": "California Citizens Redistricting Commission",
            "url": "https://wedrawthelines.ca.gov/final-maps/",
            "quality_grade": "A",
        },
        "layers": [
            {
                "layer_key": layer.layer_key,
                "geo_type": layer.geo_type,
                "office": layer.office,
                "name": layer.name,
                "state_po": "CA",
                "valid_from": layer.valid_from,
                "valid_to": layer.valid_to,
                "feature_count": layer.expected_features,
                "geometry_url": f"/results/geometry/{layer.layer_key}.geojson",
                "source_file_url": layer.source_url,
                "quality_grade": "A",
                "notes": layer.notes,
            }
            for layer in selected_layers(None, True)
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", help="Geometry layer key to generate. Defaults to congressional districts.")
    parser.add_argument("--all", action="store_true", help="Generate every configured California geometry layer.")
    args = parser.parse_args()

    for layer in selected_layers(args.layer, args.all):
        feature_count = generate_layer(layer)
        print(f"Wrote {output_path_for_layer(layer).relative_to(ROOT_DIR)} with {feature_count} features.")
    MANIFEST_PATH.write_text(json.dumps(build_manifest(), separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH.relative_to(ROOT_DIR)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
