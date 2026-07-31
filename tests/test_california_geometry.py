from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from california_geometry_config import CALIFORNIA_GEOMETRY_LAYERS
from generate_california_geometry_geojson import geometry_collection, ordinal


class CaliforniaGeometryTests(TestCase):
    def test_ordinal_formats_district_numbers(self) -> None:
        self.assertEqual(ordinal(1), "1st")
        self.assertEqual(ordinal(2), "2nd")
        self.assertEqual(ordinal(3), "3rd")
        self.assertEqual(ordinal(11), "11th")
        self.assertEqual(ordinal(22), "22nd")

    def test_geometry_collection_uses_crc_properties(self) -> None:
        layer = CALIFORNIA_GEOMETRY_LAYERS["ca-2022-congressional-districts"]
        collection = geometry_collection(
            layer,
            [
                (
                    {"DISTRICT_N": 2},
                    {"type": "MultiPolygon", "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 0]]]]},
                )
            ],
        )

        feature = collection["features"][0]
        self.assertEqual(feature["id"], "CA:CRC2020:congressional_district:2")
        self.assertEqual(feature["properties"]["geometry_id"], 6002)
        self.assertEqual(feature["properties"]["district_label"], "2nd Congressional District")
        self.assertEqual(feature["properties"]["state_po"], "CA")
