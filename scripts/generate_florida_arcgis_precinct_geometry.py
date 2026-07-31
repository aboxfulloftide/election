#!/usr/bin/env python3
"""Normalize official Florida county precinct GeoJSON exported from ArcGIS."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/florida/precinct-geometry"
OUTPUT_DIR = ROOT_DIR / "public/results/geometry"
MANIFEST_PATH = ROOT_DIR / "public/results/florida-precinct-geometry-layers.json"

LAYERS = (
    {
        "county_fips": "12011",
        "county_name": "Broward County",
        "state_po": "FL",
        "vintage": "2020",
        "raw_file": "broward/broward-2020.geojson",
        "source_url": "https://services.arcgis.com/JMAJrTsHNLrSsWf5/arcgis/rest/services/2026_SOE_GENERAL_USE_MAP___POST_CNG_WFL1/FeatureServer/199",
    },
    {
        "county_fips": "12011",
        "county_name": "Broward County",
        "state_po": "FL",
        "vintage": "2022",
        "raw_file": "broward/broward-2022.geojson",
        "source_url": "https://services.arcgis.com/JMAJrTsHNLrSsWf5/arcgis/rest/services/2026_SOE_GENERAL_USE_MAP___POST_CNG_WFL1/FeatureServer/200",
    },
    {
        "county_fips": "12011",
        "county_name": "Broward County",
        "state_po": "FL",
        "vintage": "2024",
        "raw_file": "broward/broward-2024.geojson",
        "source_url": "https://services.arcgis.com/JMAJrTsHNLrSsWf5/arcgis/rest/services/2026_SOE_GENERAL_USE_MAP___POST_CNG_WFL1/FeatureServer/203",
    },
)


def precinct_id(value: Any) -> str:
    text = str(value).strip().upper()
    return str(int(text)) if text.isdigit() else text


def polygons(geometry: dict[str, Any]) -> list[list[list[float]]]:
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    if geometry["type"] == "MultiPolygon":
        return geometry["coordinates"]
    raise ValueError(f"Unsupported geometry type: {geometry['type']}")


def build_layer(config: dict[str, str]) -> tuple[dict[str, Any], int]:
    raw = json.loads((RAW_DIR / config["raw_file"]).read_text(encoding="utf-8"))
    grouped: dict[str, list[list[list[float]]]] = defaultdict(list)
    for feature in raw["features"]:
        key = precinct_id(feature["properties"]["PRECINCT"])
        grouped[key].extend(polygons(feature["geometry"]))

    features = []
    for key in sorted(grouped):
        features.append(
            {
                "type": "Feature",
                "id": f"FL-{config['county_fips']}-{key}-{config['vintage']}",
                "properties": {
                    "state_po": config["state_po"],
                    "county_fips": config["county_fips"],
                    "county_name": config["county_name"],
                    "precinct_id": key,
                    "geometry_vintage": config["vintage"],
                },
                "geometry": {"type": "MultiPolygon", "coordinates": features_coordinates(grouped[key])},
            }
        )

    layer_key = f"fl-broward-{config['vintage']}-precincts"
    output_path = OUTPUT_DIR / f"{layer_key}.geojson"
    output_path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")), encoding="utf-8")
    return (
        {
            "layer_key": layer_key,
            "state": "Florida",
            "state_po": config["state_po"],
            "county_fips": config["county_fips"],
            "county_name": config["county_name"],
            "vintage": config["vintage"],
            "geometry_url": f"/results/geometry/{output_path.name}",
            "feature_count": len(features),
            "file_size_bytes": output_path.stat().st_size,
            "source_url": config["source_url"],
            "quality_grade": "A",
        },
        len(features),
    )


def features_coordinates(polygons_for_precinct: list[list[list[float]]]) -> list[list[list[list[float]]]]:
    return [[ring for ring in polygon] for polygon in polygons_for_precinct]


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    existing = [layer for layer in manifest["layers"] if not layer["layer_key"].startswith("fl-broward-")]
    generated = []
    for config in LAYERS:
        layer, count = build_layer(config)
        generated.append(layer)
        print(f"Wrote {layer['geometry_url']} with {count} precincts.")
    manifest["layers"] = existing + generated
    MANIFEST_PATH.write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf-8")
    print(f"Updated {MANIFEST_PATH.relative_to(ROOT_DIR)} with {len(manifest['layers'])} layers.")


if __name__ == "__main__":
    main()
