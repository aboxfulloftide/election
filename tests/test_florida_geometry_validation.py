from __future__ import annotations

import struct
import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from shapefile_geojson import count_shp_records, read_dbf_fields


def shp_bytes(record_lengths: list[int]) -> bytes:
    data = bytearray(100)
    for index, content_length_bytes in enumerate(record_lengths, start=1):
        data.extend(struct.pack(">2i", index, content_length_bytes // 2))
        data.extend(b"\0" * content_length_bytes)
    return bytes(data)


def dbf_field(name: str) -> bytes:
    raw = bytearray(32)
    encoded_name = name.encode("ascii")
    raw[: len(encoded_name)] = encoded_name
    raw[11] = ord("C")
    raw[16] = 20
    return bytes(raw)


class FloridaGeometryValidationTests(TestCase):
    def test_count_shp_records_reads_record_headers(self) -> None:
        self.assertEqual(count_shp_records(shp_bytes([8, 16, 4])), 3)

    def test_count_shp_records_rejects_truncated_header(self) -> None:
        with self.assertRaises(ValueError):
            count_shp_records(b"\0" * 99)

    def test_read_dbf_fields_reads_field_descriptors(self) -> None:
        header_length = 32 + 32 + 32 + 1
        header = bytearray(32)
        header[8:10] = struct.pack("<H", header_length)
        data = bytes(header) + dbf_field("DISTRICT") + dbf_field("NAME") + b"\r"

        self.assertEqual(read_dbf_fields(data), [("DISTRICT", "C", 20), ("NAME", "C", 20)])
