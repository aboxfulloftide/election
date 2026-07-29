#!/usr/bin/env python3
"""Generate Florida district GeoJSON files and normalized geometry rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR, connect, fetch_one_id
from florida_geometry_config import FloridaGeometryLayer, selected_layers
from shapefile_geojson import read_polygon_features


OUTPUT_DIR = ROOT_DIR / "public/results/geometry"


def output_path_for_layer(layer: FloridaGeometryLayer) -> Path:
    return OUTPUT_DIR / f"{layer.layer_key}.geojson"


def geometry_collection(layer: FloridaGeometryLayer, db_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "name": layer.layer_key,
        "features": [
            {
                "type": "Feature",
                "id": row["official_id"],
                "properties": {
                    "geometry_id": row["geometry_id"],
                    "layer_key": layer.layer_key,
                    "geo_type": layer.geo_type,
                    "official_plan_id": layer.official_plan_id,
                    "official_id": row["official_id"],
                    "district_label": row["district_label"],
                    "district_number": row["district_number"],
                    "name": row["name"],
                    "state_po": "FL",
                    "valid_from": layer.valid_from,
                    "valid_to": layer.valid_to,
                },
                "geometry": row["geometry"],
            }
            for row in db_rows
        ],
    }


def upsert_geometry(
    cursor: Any,
    layer: FloridaGeometryLayer,
    geometry_layer_id: int,
    source_file_id: int,
    record: dict[str, Any],
    geometry: dict[str, Any],
) -> dict[str, Any]:
    district_number = int(record[layer.id_field])
    district_label = f"{layer.district_label_prefix} {district_number}"
    name = str(record.get("LONGNAME") or district_label)
    official_id = f"FL:{layer.official_plan_id}:{district_number}"
    geometry_json = json.dumps(geometry, separators=(",", ":"))

    cursor.execute(
        """
        INSERT INTO geometries
          (geometry_layer_id, geo_type, name, state_po, official_id, district_label,
           valid_from, valid_to, source_file_id, simplified_geojson, notes)
        VALUES
          (%s, %s, %s, 'FL', %s, %s,
           %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          geo_type = VALUES(geo_type),
          name = VALUES(name),
          state_po = VALUES(state_po),
          district_label = VALUES(district_label),
          valid_from = VALUES(valid_from),
          valid_to = VALUES(valid_to),
          source_file_id = VALUES(source_file_id),
          simplified_geojson = VALUES(simplified_geojson),
          notes = VALUES(notes)
        """,
        (
            geometry_layer_id,
            layer.geo_type,
            name,
            official_id,
            district_label,
            layer.valid_from,
            layer.valid_to,
            source_file_id,
            geometry_json,
            f"Generated from official Florida EDR {layer.official_plan_id} shapefile.",
        ),
    )
    geometry_id = fetch_one_id(
        cursor,
        "SELECT id FROM geometries WHERE geometry_layer_id = %s AND official_id = %s",
        (geometry_layer_id, official_id),
    )
    if geometry_id is None:
        raise RuntimeError(f"Failed to upsert geometry {official_id}")

    return {
        "geometry_id": geometry_id,
        "official_id": official_id,
        "district_label": district_label,
        "district_number": district_number,
        "name": name,
        "geometry": geometry,
    }


def generate_layer(layer: FloridaGeometryLayer) -> int:
    features = read_polygon_features(layer.shapefile_path)
    if len(features) != layer.expected_features:
        raise RuntimeError(f"{layer.layer_key} has {len(features)} features; expected {layer.expected_features}")

    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id, source_file_id FROM geometry_layers WHERE layer_key = %s", (layer.layer_key,))
        layer_row = cursor.fetchone()
        if layer_row is None:
            raise RuntimeError(f"Missing geometry layer {layer.layer_key}. Run florida:geometry:register first.")
        geometry_layer_id, source_file_id = int(layer_row[0]), int(layer_row[1])

        cursor.execute("DELETE FROM geometries WHERE geometry_layer_id = %s", (geometry_layer_id,))
        db_rows = [
            upsert_geometry(cursor, layer, geometry_layer_id, source_file_id, record, geometry)
            for record, geometry in sorted(features, key=lambda item: int(item[0][layer.id_field]))
        ]
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    output_path = output_path_for_layer(layer)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(geometry_collection(layer, db_rows), separators=(",", ":")), encoding="utf-8")
    return len(db_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", help="Geometry layer key to generate. Defaults to congressional districts.")
    parser.add_argument("--all", action="store_true", help="Generate every configured Florida geometry layer.")
    args = parser.parse_args()

    for layer in selected_layers(args.layer, args.all):
        feature_count = generate_layer(layer)
        print(f"Wrote {output_path_for_layer(layer).relative_to(ROOT_DIR)} with {feature_count} features.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
