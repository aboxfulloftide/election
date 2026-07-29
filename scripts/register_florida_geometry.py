#!/usr/bin/env python3
"""Register official Florida district geometry source files in MySQL."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR, connect, fetch_one_id
from florida_geometry_config import (
    DISCOVERY_URL,
    SOURCE_HOMEPAGE,
    SOURCE_NAME,
    FloridaGeometryLayer,
    selected_layers,
)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_or_create_source(cursor: Any) -> int:
    source_id = fetch_one_id(cursor, "SELECT id FROM sources WHERE name = %s", (SOURCE_NAME,))
    notes = "Official Florida legislative redistricting plans and supporting GIS files."
    if source_id is not None:
        cursor.execute(
            """
            UPDATE sources
            SET source_type = 'official_state',
                homepage_url = %s,
                discovery_reference_url = %s,
                notes = %s
            WHERE id = %s
            """,
            (SOURCE_HOMEPAGE, DISCOVERY_URL, notes, source_id),
        )
        return source_id

    cursor.execute(
        """
        INSERT INTO sources (name, source_type, homepage_url, discovery_reference_url, notes)
        VALUES (%s, 'official_state', %s, %s, %s)
        """,
        (SOURCE_NAME, SOURCE_HOMEPAGE, DISCOVERY_URL, notes),
    )
    return int(cursor.lastrowid)


def get_or_create_source_file(
    cursor: Any,
    source_id: int,
    url: str,
    path: Path,
    file_type: str,
    layer: FloridaGeometryLayer,
    transform_notes: str,
) -> int:
    if not path.exists():
        raise RuntimeError(f"Missing {path}. Run npm run florida:geometry:download -- --all first.")

    file_checksum = checksum(path)
    source_file_id = fetch_one_id(
        cursor,
        "SELECT id FROM source_files WHERE source_id = %s AND checksum_sha256 = %s ORDER BY id LIMIT 1",
        (source_id, file_checksum),
    )
    if source_file_id is not None:
        return source_file_id

    cursor.execute(
        """
        INSERT INTO source_files
          (source_id, url, local_path, discovery_reference_url, retrieved_at, file_name, file_type,
           checksum_sha256, covers_year_start, covers_year_end, transform_notes, quality_grade)
        VALUES
          (%s, %s, %s, %s, %s, %s, %s,
           %s, %s, %s, %s, 'A')
        """,
        (
            source_id,
            url,
            str(path.relative_to(ROOT_DIR)),
            DISCOVERY_URL,
            dt.datetime.now(dt.UTC).replace(tzinfo=None),
            path.name,
            file_type,
            file_checksum,
            layer.valid_from,
            layer.valid_to or layer.valid_from,
            transform_notes,
        ),
    )
    return int(cursor.lastrowid)


def upsert_layer(cursor: Any, layer: FloridaGeometryLayer, shapefile_source_file_id: int) -> None:
    cursor.execute(
        """
        INSERT INTO geometry_layers
          (layer_key, geo_type, name, state_po, official_plan_id, valid_from, valid_to,
           source_file_id, local_path, file_type, id_field, label_field, district_label_prefix, notes)
        VALUES
          (%s, %s, %s, 'FL', %s, %s, %s,
           %s, %s, 'application/zip', %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          geo_type = VALUES(geo_type),
          name = VALUES(name),
          state_po = VALUES(state_po),
          official_plan_id = VALUES(official_plan_id),
          valid_from = VALUES(valid_from),
          valid_to = VALUES(valid_to),
          source_file_id = VALUES(source_file_id),
          local_path = VALUES(local_path),
          file_type = VALUES(file_type),
          id_field = VALUES(id_field),
          label_field = VALUES(label_field),
          district_label_prefix = VALUES(district_label_prefix),
          notes = VALUES(notes)
        """,
        (
            layer.layer_key,
            layer.geo_type,
            layer.name,
            layer.official_plan_id,
            layer.valid_from,
            layer.valid_to,
            shapefile_source_file_id,
            str(layer.shapefile_path.relative_to(ROOT_DIR)),
            layer.id_field,
            layer.label_field,
            layer.district_label_prefix,
            f"{layer.notes} Expected feature count: {layer.expected_features}.",
        ),
    )


def register_layer(cursor: Any, source_id: int, layer: FloridaGeometryLayer) -> None:
    shapefile_source_file_id = get_or_create_source_file(
        cursor,
        source_id,
        layer.shapefile_url,
        layer.shapefile_path,
        "application/zip",
        layer,
        f"Official shapefile ZIP for {layer.name}; geometry features are not simplified during registration.",
    )
    get_or_create_source_file(
        cursor,
        source_id,
        layer.block_equivalency_url,
        layer.block_equivalency_path,
        "text/plain",
        layer,
        f"Official census block equivalency file for {layer.name}; retained for future geometry joins.",
    )
    upsert_layer(cursor, layer, shapefile_source_file_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", help="Geometry layer key to register. Defaults to congressional districts.")
    parser.add_argument("--all", action="store_true", help="Register every configured Florida geometry layer.")
    args = parser.parse_args()

    connection = connect()
    cursor = connection.cursor()
    try:
        source_id = get_or_create_source(cursor)
        for layer in selected_layers(args.layer, args.all):
            register_layer(cursor, source_id, layer)
            print(f"Registered geometry layer: {layer.layer_key}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
