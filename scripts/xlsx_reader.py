"""Small XLSX reader for simple one-sheet official election workbooks."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any


NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if match is None:
        raise ValueError(f"Invalid cell reference: {cell_ref}")
    index = 0
    for character in match.group(1):
        index = index * 26 + ord(character) - ord("A") + 1
    return index - 1


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    values: list[str] = []
    for item in root.findall("m:si", NS):
        values.append("".join(text.text or "" for text in item.findall(".//m:t", NS)))
    return values


def cell_value(cell: ET.Element, strings: list[str]) -> Any:
    value = cell.find("m:v", NS)
    if value is None or value.text is None:
        return None
    if cell.attrib.get("t") == "s":
        return strings[int(value.text)]
    number = float(value.text)
    return int(number) if number.is_integer() else number


def read_first_sheet(path: Path) -> list[list[Any]]:
    with zipfile.ZipFile(path) as archive:
        strings = shared_strings(archive)
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    rows: list[list[Any]] = []
    for row in root.findall(".//m:row", NS):
        values: list[Any] = []
        for cell in row.findall("m:c", NS):
            index = column_index(cell.attrib["r"])
            while len(values) <= index:
                values.append(None)
            values[index] = cell_value(cell, strings)
        rows.append(values)
    return rows
