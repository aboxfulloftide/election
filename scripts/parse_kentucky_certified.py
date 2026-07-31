#!/usr/bin/env python3
"""Extract a diagnostic U.S. Senate table from Kentucky's certified 2022 OCR."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/kentucky"
OCR_PATH = RAW_DIR / "2022_certified_general_election_results_ocr.txt"
OUTPUT_PATH = RAW_DIR / "2022_certified_senate_reconciliation.json"
NUMBER_RE = re.compile(r"(?<![A-Za-z])([0-9OoIl§][0-9,.OoIl§]*)(?![A-Za-z])")
ZERO_OCR_TOKENS = {"ie)", "ie}", "ie]", "it)", "is}", "i?)", "iC)", "te)", "i)", "(¢)", ")"}
OFFICE_RE = re.compile(r"^(United States Senator|United States Representative in Congress|State Senator|State Representative)$", re.I)
DISTRICT_RE = re.compile(r"(\d+)(?:st|nd|rd|th)\s+(Congressional|Senatorial|Representative)\s+District", re.I)


def number(value: str) -> int | None:
    normalized = value.replace(",", "").replace(".", "").translate(str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "§": "5"}))
    return int(normalized) if normalized.isdigit() else None


def senate_section(text: str) -> str:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.strip().lower() == "united states senator"]
    if not starts:
        raise RuntimeError("Certified OCR does not contain a U.S. Senate section")
    start = starts[-1]
    end = next((index for index in range(start + 1, len(lines)) if lines[index].strip().lower() == "for the office of"), len(lines))
    return "\n".join(lines[start + 1 : end])


def certified_sections(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.strip().lower() == "for the office of"]
    sections = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        body = [line.strip() for line in lines[start + 1 : end] if line.strip()]
        heading = next((line for line in body if OFFICE_RE.match(line)), "")
        if not heading:
            continue
        districts = []
        district_lines = []
        for line in body:
            match = DISTRICT_RE.search(line)
            if match:
                districts.append(f"{match.group(1)} {match.group(2).lower()} district")
                district_lines.append(line)
            elif "congressional district" in line.lower():
                district_lines.append(line)
        inferred = False
        if heading.lower().startswith("united states representative") and len(district_lines) == 6:
            districts = [f"{number} congressional district" for number in range(1, 7)]
            inferred = True
        sections.append(
            {
                "office": heading,
                "districts": list(dict.fromkeys(districts)),
                "districts_inferred": inferred,
                "line_count": len(body),
            }
        )
    return sections


def parse_senate(text: str) -> dict[str, Any]:
    rows = []
    official_totals = None
    county_names = {
        row["county_name"].casefold()
        for row in json.loads((ROOT_DIR / "public/results/county-presidential-summary.json").read_text())["counties"]
        if row["state_po"] == "KY"
    }
    for raw_line in senate_section(text).splitlines():
        line = re.sub(r"\s+", " ", raw_line.replace("\f", " ")).strip()
        line = " ".join("0" if token in ZERO_OCR_TOKENS else token for token in line.split())
        if not line or line.lower().startswith(("republican party", "democratic party", "rand ", "paul", "total votes", "november ")):
            if line.lower().startswith("total votes"):
                matches = NUMBER_RE.findall(line)
                values = [number(match) for match in matches]
                official_totals = [value for value in values if value is not None]
            continue
        matches = NUMBER_RE.findall(line)
        values = [number(match) for match in matches]
        values = [value for value in values if value is not None]
        if len(values) < 2:
            continue
        county = line[: matches[0] and line.find(matches[0])].strip(" _|:;-")
        if county.casefold() not in county_names:
            continue
        rows.append({"county": county, "values": values[:4], "raw": line})
    totals = [sum(row["values"][index] for row in rows if len(row["values"]) > index) for index in range(4)]
    return {
        "office": "U.S. Senate",
        "year": 2022,
        "rows": rows,
        "row_count": len(rows),
        "column_totals": totals,
        "official_total_votes": official_totals,
    }


def parse_us_house_totals(text: str) -> list[dict[str, Any]]:
    """Extract printed district totals as a second OCR checkpoint."""
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip().lower() == "united states representative in congress"), None)
    if start is None:
        return []
    end = next((index for index in range(start + 1, len(lines)) if lines[index].strip().lower() == "for the office of"), len(lines))
    districts: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in lines[start:end]:
        line = re.sub(r"\s+", " ", raw_line).strip()
        if "district" in line.lower() and ("congressional" in line.lower() or "representative" in line.lower()):
            match = DISTRICT_RE.search(line)
            current = {"district": int(match.group(1)) if match else len(districts) + 1, "official_total_votes": None}
            districts.append(current)
            continue
        if current and line.lower().startswith("total votes"):
            line = " ".join("0" if token in ZERO_OCR_TOKENS else token for token in line.split())
            current["official_total_votes"] = [value for value in (number(match) for match in NUMBER_RE.findall(line)) if value is not None]
    return districts


def parse_us_house_county_rows(text: str) -> list[dict[str, Any]]:
    """Extract county rows for each U.S. House district without publishing OCR values."""
    county_names = {
        row["county_name"].casefold()
        for row in json.loads((ROOT_DIR / "public/results/county-presidential-summary.json").read_text())["counties"]
        if row["state_po"] == "KY"
    }
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip().lower() == "united states representative in congress"), None)
    if start is None:
        return []
    end = next((index for index in range(start + 1, len(lines)) if lines[index].strip().lower() == "for the office of"), len(lines))
    districts: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in lines[start:end]:
        line = re.sub(r"\s+", " ", raw_line.replace("\f", " ")).strip()
        if "district" in line.lower() and ("congressional" in line.lower() or "representative" in line.lower()):
            match = DISTRICT_RE.search(line)
            current = {"district": int(match.group(1)) if match else len(districts) + 1, "rows": [], "official_total_votes": None}
            districts.append(current)
            continue
        if not current:
            continue
        line = " ".join("0" if token in ZERO_OCR_TOKENS else token for token in line.split())
        if line.lower().startswith("total votes"):
            current["official_total_votes"] = [value for value in (number(match) for match in NUMBER_RE.findall(line)) if value is not None]
            continue
        matches = NUMBER_RE.findall(line)
        values = [value for value in (number(match) for match in matches) if value is not None]
        if len(values) < 2:
            continue
        county = line[:line.find(matches[0])].strip(" _|:;-")
        if county.casefold() in county_names:
            current["rows"].append({"county": county, "values": values, "raw": line})
    for district in districts:
        district["row_count"] = len(district["rows"])
        district["summed_columns"] = [sum(row["values"][index] for row in district["rows"] if len(row["values"]) > index) for index in range(4)]
        district["party_columns_match"] = district["summed_columns"][:2] == (district["official_total_votes"] or [])[:2]
    return districts


def parse_certified_totals(text: str) -> list[dict[str, Any]]:
    """Collect every printed contest total across federal and state offices."""
    totals: list[dict[str, Any]] = []
    office = ""
    district: int | None = None
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        lowered = line.lower()
        if lowered == "for the office of":
            office, district = "", None
        elif lowered == "united states senator":
            office, district = "U.S. Senate", None
        elif lowered == "united states representative in congress":
            office, district = "U.S. House", None
        elif lowered == "state senator":
            office, district = "State Senate", None
        elif lowered == "state representative":
            office, district = "State House", None
        elif office and "district" in lowered:
            match = DISTRICT_RE.search(line)
            if match:
                district = int(match.group(1))
        if office and lowered.startswith("total votes"):
            line = " ".join("0" if token in ZERO_OCR_TOKENS else token for token in line.split())
            values = [value for value in (number(match) for match in NUMBER_RE.findall(line)) if value is not None]
            totals.append({"office": office, "district": district, "official_total_votes": values})
    return totals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=OCR_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT_DIR / args.input
    output_path = args.output if args.output.is_absolute() else ROOT_DIR / args.output
    text = input_path.read_text(encoding="utf-8")
    result = parse_senate(text)
    result["sections"] = certified_sections(text)
    result["us_house_totals"] = parse_us_house_totals(text)
    result["us_house_county_rows"] = parse_us_house_county_rows(text)
    result["contest_totals"] = parse_certified_totals(text)
    house = next((section for section in result["sections"] if section["office"].lower().startswith("united states representative")), None)
    state_senate = next((section for section in result["sections"] if section["office"].lower() == "state senator"), None)
    result["validation"] = {
        "expected_senate_counties": 120,
        "senate_counties_complete": result["row_count"] == 120,
        "printed_party_totals_match": result["column_totals"][:2] == (result["official_total_votes"] or [])[:2],
        "printed_write_in_totals_match": result["column_totals"][2:] == (result["official_total_votes"] or [])[2:],
        "expected_us_house_districts": 6,
        "us_house_districts_detected": len(house["districts"]) if house else 0,
        "us_house_districts_inferred": bool(house and house["districts_inferred"]),
        "us_house_county_rows_complete": len(result["us_house_county_rows"]) == 6 and all(item["row_count"] > 0 for item in result["us_house_county_rows"]),
        "us_house_party_totals_match": len(result["us_house_county_rows"]) == 6 and all(item["party_columns_match"] for item in result["us_house_county_rows"]),
        "expected_state_senate_districts": 19,
        "state_senate_districts_detected": len(state_senate["districts"]) if state_senate else 0,
        "state_house_districts_detected": sum(1 for item in result["contest_totals"] if item["office"] == "State House"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {result['row_count']} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
