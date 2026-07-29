#!/usr/bin/env python3
"""Validate registered Florida district geometry layers."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR, connect
from florida_geometry_config import FloridaGeometryLayer, selected_layers
from generate_florida_geometry_geojson import output_path_for_layer
from shapefile_geojson import count_shp_records, read_dbf_fields, zip_member_with_suffix


REQUIRED_SHAPEFILE_EXTENSIONS = {".shp", ".shx", ".dbf", ".prj"}


def scalar(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> int:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return int(next(iter(row.values()))) if row else 0


def validate_zip(layer: FloridaGeometryLayer) -> list[str]:
    path = layer.shapefile_path
    failed: list[str] = []
    if not path.exists() or path.stat().st_size == 0:
        return [f"missing or empty {path.relative_to(ROOT_DIR)}"]
    with zipfile.ZipFile(path) as archive:
        extensions = {Path(name).suffix.lower() for name in archive.namelist()}
        missing = REQUIRED_SHAPEFILE_EXTENSIONS - extensions
        if missing:
            failed.append(f"{path.relative_to(ROOT_DIR)} missing shapefile parts: {', '.join(sorted(missing))}")
            return failed

        shp_name = zip_member_with_suffix(archive, ".shp")
        dbf_name = zip_member_with_suffix(archive, ".dbf")
        if shp_name is None or dbf_name is None:
            return failed

        feature_count = count_shp_records(archive.read(shp_name))
        if feature_count != layer.expected_features:
            failed.append(
                f"{path.relative_to(ROOT_DIR)} has {feature_count} features; expected {layer.expected_features}"
            )

        fields = {name.upper() for name, _, _ in read_dbf_fields(archive.read(dbf_name))}
        required_fields = {layer.id_field.upper(), layer.label_field.upper()}
        missing_fields = required_fields - fields
        if missing_fields:
            failed.append(f"{path.relative_to(ROOT_DIR)} missing DBF fields: {', '.join(sorted(missing_fields))}")
    return failed


def validate_layer(cursor: Any, layer: FloridaGeometryLayer) -> list[str]:
    failed = validate_zip(layer)
    if not layer.block_equivalency_path.exists() or layer.block_equivalency_path.stat().st_size == 0:
        failed.append(f"missing or empty {layer.block_equivalency_path.relative_to(ROOT_DIR)}")

    layer_count = scalar(
        cursor,
        "SELECT COUNT(*) AS value FROM geometry_layers WHERE layer_key = %s",
        (layer.layer_key,),
    )
    source_file_count = scalar(
        cursor,
        """
        SELECT COUNT(*) AS value
        FROM source_files
        WHERE url IN (%s, %s)
        """,
        (layer.shapefile_url, layer.block_equivalency_url),
    )
    geometry_count = scalar(
        cursor,
        """
        SELECT COUNT(*) AS value
        FROM geometries g
        JOIN geometry_layers gl ON gl.id = g.geometry_layer_id
        WHERE gl.layer_key = %s
        """,
        (layer.layer_key,),
    )
    geojson_path = output_path_for_layer(layer)

    print(f"Florida geometry validation: {layer.layer_key}")
    print(f"  geometry_layers: {layer_count}")
    print(f"  source_files: {source_file_count}")
    print(f"  geometries: {geometry_count}")
    print(f"  expected_features: {layer.expected_features}")

    if layer_count != 1:
        failed.append("expected one geometry_layers row")
    if source_file_count != 2:
        failed.append("expected shapefile and block-equivalency source_files")
    if geometry_count not in (0, layer.expected_features):
        failed.append(f"expected either no generated geometries or {layer.expected_features} generated geometries")
    if geometry_count == layer.expected_features and (not geojson_path.exists() or geojson_path.stat().st_size == 0):
        failed.append(f"missing generated GeoJSON {geojson_path.relative_to(ROOT_DIR)}")
    return failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", help="Geometry layer key to validate. Defaults to congressional districts.")
    parser.add_argument("--all", action="store_true", help="Validate every configured Florida geometry layer.")
    args = parser.parse_args()

    connection = connect()
    cursor = connection.cursor(dictionary=True)
    try:
        failed: list[str] = []
        for layer in selected_layers(args.layer, args.all):
            failed.extend(f"{layer.layer_key}: {message}" for message in validate_layer(cursor, layer))
        if failed:
            for message in failed:
                print(f"ERROR: {message}", file=sys.stderr)
            return 1
        return 0
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
