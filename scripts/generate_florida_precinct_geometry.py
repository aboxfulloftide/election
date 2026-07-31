#!/usr/bin/env python3
"""Generate WGS84 precinct GeoJSON for the Miami-Dade pilot vintages."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from pyproj import Transformer

from shapefile_geojson import read_polygon_features


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/florida/precinct-geometry/miami-dade"
OUTPUT_DIR = ROOT_DIR / "public/results/geometry"
MANIFEST_PATH = ROOT_DIR / "public/results/florida-precinct-geometry-layers.json"
TRANSFORMER = Transformer.from_crs("EPSG:2236", "EPSG:4326", always_xy=True)

VINTAGES = {
    "2012": "miami-dade-2012-2014.zip",
    "2014": "miami-dade-2014-2015.zip",
}


def transform_ring(ring: list[list[float]]) -> list[list[float]]:
    return [[round(lon, 6), round(lat, 6)] for lon, lat in (TRANSFORMER.transform(x, y) for x, y in ring)]


def build_features(archive_path: Path, vintage: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[list[list[float]]]] = defaultdict(list)
    for record, geometry in read_polygon_features(archive_path):
        precinct_id = str(int(record["PRECINCT"]))
        for polygon in geometry["coordinates"]:
            for ring in polygon:
                grouped[precinct_id].append(transform_ring(ring))

    features = []
    for precinct_id in sorted(grouped):
        features.append(
            {
                "type": "Feature",
                "id": f"FL-086-{precinct_id}-{vintage}",
                "properties": {
                    "state_po": "FL",
                    "county_fips": "12086",
                    "county_name": "Miami-Dade County",
                    "precinct_id": precinct_id,
                    "geometry_vintage": vintage,
                },
                "geometry": {"type": "MultiPolygon", "coordinates": [[ring] for ring in grouped[precinct_id]]},
            }
        )
    return features


def main() -> None:
    layers = []
    for vintage, filename in VINTAGES.items():
        archive_path = RAW_DIR / filename
        if not archive_path.exists():
            raise FileNotFoundError(archive_path)
        features = build_features(archive_path, vintage)
        layer_key = f"fl-miami-dade-{vintage}-precincts"
        output_path = OUTPUT_DIR / f"{layer_key}.geojson"
        output_path.write_text(
            json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")),
            encoding="utf-8",
        )
        layers.append(
            {
                "layer_key": layer_key,
                "state": "Florida",
                "state_po": "FL",
                "county_fips": "12086",
                "county_name": "Miami-Dade County",
                "vintage": vintage,
                "geometry_url": f"/results/geometry/{output_path.name}",
                "feature_count": len(features),
                "file_size_bytes": output_path.stat().st_size,
                "source_url": (
                    "https://www.votemiamidade.gov/elections/data/precincts-districts-municipalities-2022.page"
                    if vintage == "2012"
                    else "https://www.votemiamidade.gov/elections/data/precincts-districts-municipalities-2015.page"
                ),
                "quality_grade": "A",
            }
        )
        print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {len(features)} precincts.")

    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "source": {
                    "name": "Miami-Dade County Supervisor of Elections",
                    "url": "https://www.votemiamidade.gov/elections/data/current-precincts-districts-municipalities.page",
                    "quality_grade": "A",
                },
                "layers": layers,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    print(f"Wrote {MANIFEST_PATH.relative_to(ROOT_DIR)} with {len(layers)} layers.")


if __name__ == "__main__":
    main()
