#!/usr/bin/env python3
"""Generate app-ready Florida geometry layer metadata from MySQL."""

from __future__ import annotations

import datetime as dt
import json
import sys
from typing import Any

from election_db import ROOT_DIR, connect


OUTPUT_PATH = ROOT_DIR / "public/results/florida-geometry-layers.json"


def build_manifest() -> dict[str, Any]:
    connection = connect()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
              gl.layer_key,
              gl.geo_type,
              gl.name,
              gl.state_po,
              gl.official_plan_id,
              gl.valid_from,
              gl.valid_to,
              gl.local_path,
              gl.file_type,
              gl.id_field,
              gl.label_field,
              gl.district_label_prefix,
              gl.notes,
              COUNT(g.id) AS feature_count,
              s.name AS source_name,
              s.homepage_url AS source_url,
              sf.url AS source_file_url,
              sf.checksum_sha256,
              sf.quality_grade
            FROM geometry_layers gl
            LEFT JOIN geometries g ON g.geometry_layer_id = gl.id
            LEFT JOIN source_files sf ON sf.id = gl.source_file_id
            LEFT JOIN sources s ON s.id = sf.source_id
            WHERE gl.state_po = 'FL'
            GROUP BY
              gl.id, gl.layer_key, gl.geo_type, gl.name, gl.state_po, gl.official_plan_id,
              gl.valid_from, gl.valid_to, gl.local_path, gl.file_type, gl.id_field,
              gl.label_field, gl.district_label_prefix, gl.notes,
              s.name, s.homepage_url, sf.url, sf.checksum_sha256, sf.quality_grade
            ORDER BY gl.valid_from, gl.geo_type, gl.layer_key
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return {
        "source": {
            "name": rows[0]["source_name"] if rows else "Florida Legislature Office of Economic and Demographic Research",
            "url": rows[0]["source_url"] if rows else "https://edr.state.fl.us/content/redistricting/2020redistricting/index.cfm",
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "quality_grade": min((row["quality_grade"] for row in rows if row["quality_grade"]), default="A"),
        },
        "layers": [
            {
                "layer_key": row["layer_key"],
                "geo_type": row["geo_type"],
                "name": row["name"],
                "state_po": row["state_po"],
                "official_plan_id": row["official_plan_id"],
                "valid_from": row["valid_from"],
                "valid_to": row["valid_to"],
                "local_path": row["local_path"],
                "file_type": row["file_type"],
                "id_field": row["id_field"],
                "label_field": row["label_field"],
                "district_label_prefix": row["district_label_prefix"],
                "feature_count": int(row["feature_count"] or 0),
                "geometry_url": f"/results/geometry/{row['layer_key']}.geojson",
                "source_file_url": row["source_file_url"],
                "checksum_sha256": row["checksum_sha256"],
                "quality_grade": row["quality_grade"],
                "notes": row["notes"],
            }
            for row in rows
        ],
    }


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    OUTPUT_PATH.write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT_DIR)} with {len(manifest['layers'])} layers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
