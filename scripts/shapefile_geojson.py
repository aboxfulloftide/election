"""Small shapefile reader for WGS84 polygon layers used by this project."""

from __future__ import annotations

import io
import struct
import zipfile
from pathlib import Path
from typing import Any


SHAPE_TYPE_NULL = 0
SHAPE_TYPE_POLYGON = 5


def zip_member_with_suffix(archive: zipfile.ZipFile, suffix: str) -> str | None:
    matches = [name for name in archive.namelist() if Path(name).suffix.lower() == suffix]
    return matches[0] if matches else None


def count_shp_records(data: bytes) -> int:
    handle = io.BytesIO(data)
    if len(data) < 100:
        raise ValueError("SHP file is shorter than the 100-byte header")
    handle.seek(100)
    records = 0
    while handle.tell() < len(data):
        header = handle.read(8)
        if len(header) != 8:
            raise ValueError("SHP record header is truncated")
        _, content_length_words = struct.unpack(">2i", header)
        handle.seek(content_length_words * 2, io.SEEK_CUR)
        records += 1
    return records


def parse_shp_polygons(data: bytes) -> list[dict[str, Any] | None]:
    if len(data) < 100:
        raise ValueError("SHP file is shorter than the 100-byte header")
    shape_type = struct.unpack("<i", data[32:36])[0]
    if shape_type != SHAPE_TYPE_POLYGON:
        raise ValueError(f"Unsupported shapefile shape type {shape_type}; expected polygon type 5")

    handle = io.BytesIO(data)
    handle.seek(100)
    geometries: list[dict[str, Any] | None] = []
    while handle.tell() < len(data):
        header = handle.read(8)
        if len(header) != 8:
            raise ValueError("SHP record header is truncated")
        _, content_length_words = struct.unpack(">2i", header)
        content = handle.read(content_length_words * 2)
        if len(content) != content_length_words * 2:
            raise ValueError("SHP record content is truncated")
        record_shape_type = struct.unpack("<i", content[:4])[0]
        if record_shape_type == SHAPE_TYPE_NULL:
            geometries.append(None)
            continue
        if record_shape_type != SHAPE_TYPE_POLYGON:
            raise ValueError(f"Unsupported record shape type {record_shape_type}; expected polygon type 5")

        num_parts, num_points = struct.unpack("<2i", content[36:44])
        parts_offset = 44
        points_offset = parts_offset + (num_parts * 4)
        parts = list(struct.unpack(f"<{num_parts}i", content[parts_offset:points_offset]))
        points = [
            struct.unpack("<2d", content[points_offset + (index * 16) : points_offset + ((index + 1) * 16)])
            for index in range(num_points)
        ]
        rings = []
        for part_index, start in enumerate(parts):
            end = parts[part_index + 1] if part_index + 1 < len(parts) else num_points
            ring = [[round(x, 6), round(y, 6)] for x, y in points[start:end]]
            if ring and ring[0] != ring[-1]:
                ring.append(ring[0])
            if len(ring) >= 4:
                rings.append(ring)
        geometries.append({"type": "MultiPolygon", "coordinates": [[ring] for ring in rings]})
    return geometries


def parse_dbf_value(raw: bytes, field_type: str) -> Any:
    value = raw.decode("latin1", errors="replace").strip()
    if value == "":
        return None
    if field_type in {"N", "F"}:
        try:
            return int(value)
        except ValueError:
            return float(value)
    if field_type == "L":
        return value.upper() in {"Y", "T"}
    return value


def read_dbf_fields(data: bytes) -> list[tuple[str, str, int]]:
    if len(data) < 32:
        raise ValueError("DBF file is shorter than the header")
    header_length = struct.unpack("<H", data[8:10])[0]
    fields: list[tuple[str, str, int]] = []
    seen: dict[str, int] = {}
    offset = 32
    while offset + 32 <= min(header_length, len(data)):
        descriptor = data[offset : offset + 32]
        if descriptor[0] == 0x0D:
            break
        raw_name = descriptor[:11].split(b"\x00", 1)[0]
        name = raw_name.decode("ascii", errors="ignore").strip()
        seen[name] = seen.get(name, 0) + 1
        unique_name = name if seen[name] == 1 else f"{name}_{seen[name]}"
        fields.append((unique_name, chr(descriptor[11]), descriptor[16]))
        offset += 32
    return fields


def parse_dbf_records(data: bytes) -> list[dict[str, Any]]:
    fields = read_dbf_fields(data)
    record_count = struct.unpack("<I", data[4:8])[0]
    header_length = struct.unpack("<H", data[8:10])[0]
    record_length = struct.unpack("<H", data[10:12])[0]
    records: list[dict[str, Any]] = []
    for record_index in range(record_count):
        offset = header_length + (record_index * record_length)
        row = data[offset : offset + record_length]
        if len(row) != record_length:
            raise ValueError("DBF record is truncated")
        if row[:1] == b"*":
            records.append({})
            continue
        position = 1
        record: dict[str, Any] = {}
        for name, field_type, size in fields:
            record[name] = parse_dbf_value(row[position : position + size], field_type)
            position += size
        records.append(record)
    return records


def read_polygon_features(path: Path) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    with zipfile.ZipFile(path) as archive:
        shp_name = zip_member_with_suffix(archive, ".shp")
        dbf_name = zip_member_with_suffix(archive, ".dbf")
        if shp_name is None or dbf_name is None:
            raise ValueError(f"{path} must contain .shp and .dbf members")
        geometries = parse_shp_polygons(archive.read(shp_name))
        records = parse_dbf_records(archive.read(dbf_name))

    if len(geometries) != len(records):
        raise ValueError(f"{path} has {len(geometries)} geometries but {len(records)} DBF records")

    return [(record, geometry) for record, geometry in zip(records, geometries) if geometry is not None]
