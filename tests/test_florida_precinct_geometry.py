from __future__ import annotations

import json
from pathlib import Path
from unittest import TestCase

ROOT_DIR = Path(__file__).resolve().parents[1]


class FloridaPrecinctGeometryTests(TestCase):
    def test_manifest_has_imported_vintages(self) -> None:
        manifest = json.loads((ROOT_DIR / "public/results/florida-precinct-geometry-layers.json").read_text())

        self.assertEqual(
            [(layer["county_fips"], layer["vintage"]) for layer in manifest["layers"]],
            [("12086", "2012"), ("12086", "2014"), ("12011", "2020"), ("12011", "2022"), ("12011", "2024")],
        )
        self.assertEqual([layer["feature_count"] for layer in manifest["layers"]], [829, 812, 577, 346, 358])

    def test_features_have_unique_precincts_and_wgs84_bounds(self) -> None:
        for filename, expected_count in (
            ("fl-miami-dade-2012-precincts.geojson", 829),
            ("fl-miami-dade-2014-precincts.geojson", 812),
            ("fl-broward-2020-precincts.geojson", 577),
            ("fl-broward-2022-precincts.geojson", 346),
            ("fl-broward-2024-precincts.geojson", 358),
        ):
            data = json.loads((ROOT_DIR / "public/results/geometry" / filename).read_text())
            self.assertEqual(len(data["features"]), expected_count)
            precincts = [feature["properties"]["precinct_id"] for feature in data["features"]]
            self.assertEqual(len(precincts), len(set(precincts)))

            coordinates = []

            def collect(value: object) -> None:
                if isinstance(value, list) and len(value) == 2 and all(isinstance(item, (int, float)) for item in value):
                    coordinates.append(value)
                elif isinstance(value, list):
                    for item in value:
                        collect(item)

            collect([feature["geometry"]["coordinates"] for feature in data["features"]])
            self.assertGreater(min(point[0] for point in coordinates), -81)
            self.assertLess(max(point[0] for point in coordinates), -79)
            self.assertGreater(min(point[1] for point in coordinates), 25)
            self.assertLess(max(point[1] for point in coordinates), 27)
