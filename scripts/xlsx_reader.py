"""Small spreadsheet readers for simple one-sheet official election workbooks."""

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

    return rows_from_sheet_root(root, strings)


def rows_from_sheet_root(root: ET.Element, strings: list[str]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for row in root.findall(".//m:row", NS):
        values: list[Any] = []
        for cell in row.findall("m:c", NS):
            index = column_index(cell.attrib["r"])
            while len(values) <= index:
                values.append(None)
            values[index] = cell_value(cell, strings)
        while values and values[-1] is None:
            values.pop()
        rows.append(values)
    return rows


def read_xlsx_sheets(path: Path) -> dict[str, list[list[Any]]]:
    with zipfile.ZipFile(path) as archive:
        strings = shared_strings(archive)
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = workbook.findall("m:sheets/m:sheet", NS)
        return {
            str(sheet.attrib["name"]): rows_from_sheet_root(
                ET.fromstring(archive.read(f"xl/worksheets/sheet{index}.xml")),
                strings,
            )
            for index, sheet in enumerate(sheets, start=1)
        }


def read_first_sheet_xls(path: Path) -> list[list[Any]]:
    try:
        import xlrd
    except ImportError as exc:
        raise RuntimeError("Reading .xls files requires xlrd. Run python3 -m pip install -r requirements.txt") from exc

    workbook = xlrd.open_workbook(str(path))
    sheet = workbook.sheet_by_index(0)
    rows: list[list[Any]] = []
    for row_index in range(sheet.nrows):
        values: list[Any] = []
        for col_index in range(sheet.ncols):
            cell = sheet.cell(row_index, col_index)
            value: Any
            if cell.ctype == xlrd.XL_CELL_EMPTY:
                value = None
            elif cell.ctype == xlrd.XL_CELL_NUMBER:
                value = int(cell.value) if float(cell.value).is_integer() else cell.value
            else:
                value = cell.value
            values.append(value)
        while values and values[-1] is None:
            values.pop()
        rows.append(values)
    return rows


def read_first_spreadsheet_sheet(path: Path) -> list[list[Any]]:
    if path.suffix.lower() == ".xls":
        return read_first_sheet_xls(path)
    return read_first_sheet(path)
