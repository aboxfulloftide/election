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
HOUSE_CANDIDATES = {
    1: [("James R. Comer", "REPUBLICAN"), ("Jimmy C. Ausbrooks", "DEMOCRAT")],
    2: [("S. Brett Guthrie", "REPUBLICAN"), ("Hank Linderman", "DEMOCRAT")],
    3: [("Morgan McGarvey", "DEMOCRAT"), ("Stuart N. Ray", "REPUBLICAN"), ("Daniel Cobble", "OTHER")],
    4: [("Thomas Massie", "REPUBLICAN"), ("Matthew Lehman", "DEMOCRAT"), ("Ethan Keith Osborne", "INDEPENDENT")],
    5: [("Harold \"Hal\" Rogers", "REPUBLICAN"), ("Conor Halbleib", "DEMOCRAT"), ("Stephan William Mazur", "OTHER")],
    6: [("Andy Barr", "REPUBLICAN"), ("Geoffrey M. Young", "DEMOCRAT"), ("Maurice Randall Cravens II", "OTHER"), ("Maxwell Keith Froedge", "OTHER")],
}
HOUSE_OCR_CORRECTIONS = {
    (4, "Boone", 1): 13001,
    (5, "Carter", 1): 1587,
    (6, "Bath", 2): 1,
    (6, "Garrard", 3): 1,
}
COUNTY_OCR_ALIASES = {"lestie": "Leslie", "effiott": "Elliott"}
STATE_ROW_OCR_CORRECTIONS = {
    ("State Senate", 28, "Menifee", 0): 1551,
    ("State Senate", 28, "Menifee", 1): 0,
    ("State House", 72, "Nicholas", 0): 1811,
    ("State House", 73, "Fayette", 1): 1340,
    ("State House", 84, "Breathitt", 1): 1274,
    ("State House", 88, "Scott", 0): 1840,
}
STATE_TOTAL_OCR_CORRECTIONS = {
    ("State Senate", 16, 0): 31887,
}
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
        county = COUNTY_OCR_ALIASES.get(county.casefold(), county)
        if county.casefold() in county_names:
            corrected_values = list(values)
            corrections = []
            for index, value in enumerate(corrected_values):
                corrected = HOUSE_OCR_CORRECTIONS.get((current["district"], county, index))
                if corrected is not None and corrected != value:
                    corrections.append({"column": index, "ocr_value": value, "corrected_value": corrected})
                    corrected_values[index] = corrected
            current["rows"].append({"county": county, "values": corrected_values, "ocr_values": values, "corrections": corrections, "raw": line})
    for district in districts:
        district["row_count"] = len(district["rows"])
        district["summed_columns"] = [sum(row["values"][index] for row in district["rows"] if len(row["values"]) > index) for index in range(4)]
        district["party_columns_match"] = district["summed_columns"][:2] == (district["official_total_votes"] or [])[:2]
        district["all_columns_match"] = district["summed_columns"][:len(district["official_total_votes"] or [])] == (district["official_total_votes"] or [])
        district["corrections_applied"] = sum(len(row["corrections"]) for row in district["rows"])
    return districts


def build_us_house_contests(text: str) -> list[dict[str, Any]]:
    """Build import-shaped U.S. House diagnostics from corrected county rows."""
    contests = []
    for district in parse_us_house_county_rows(text):
        candidates = []
        for index, (name, party) in enumerate(HOUSE_CANDIDATES.get(district["district"], [])):
            votes = district["summed_columns"][index] if index < len(district["summed_columns"]) else 0
            candidates.append({"candidate": name, "party": party, "votes": votes})
        candidates.sort(key=lambda item: (-item["votes"], item["candidate"]))
        official_total = sum(district["official_total_votes"] or [])
        contests.append({
            "office": "U.S. House",
            "district_number": district["district"],
            "year": 2022,
            "state": "Kentucky",
            "state_po": "KY",
            "source_format": "ky-certified-pdf-ocr",
            "quality_grade": "B",
            "total_votes": official_total,
            "name": f"Kentucky 2022 {district['district']} U.S. House District",
            "source_url": "https://elect.ky.gov/results/2020-2029/Pages/2022.aspx",
            "source_files": 1,
            "district_label": f"{district['district']} Congressional District",
            "candidate_votes_total": sum(item["votes"] for item in candidates),
            "winner": candidates[0] if candidates else None,
            "candidates": candidates,
            "county_rows": district["row_count"],
            "validated": district["all_columns_match"],
            "corrections_applied": district["corrections_applied"],
        })
        contests[-1]["total_votes"] = sum(item["votes"] for item in candidates)
        contests[-1]["margin_votes"] = candidates[0]["votes"] - candidates[1]["votes"] if len(candidates) > 1 else 0
    return contests


def parse_state_legislative_rows(text: str, office: str) -> list[dict[str, Any]]:
    """Extract county rows and reconciliation status for a state legislative office."""
    if office not in {"State Senate", "State House"}:
        raise ValueError("office must be State Senate or State House")
    county_names = {
        row["county_name"].casefold()
        for row in json.loads((ROOT_DIR / "public/results/county-presidential-summary.json").read_text())["counties"]
        if row["state_po"] == "KY"
    }
    heading = "State Senator" if office == "State Senate" else "State Representative"
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip().lower() == heading.lower()), None)
    if start is None:
        return []
    end = next((index for index in range(start + 1, len(lines)) if lines[index].strip().lower() == "for the office of"), len(lines))
    districts: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in lines[start:end]:
        line = re.sub(r"\s+", " ", raw_line.replace("\f", " ")).strip()
        lowered = line.lower()
        if "district" in lowered and ("senatorial" in lowered or "representative" in lowered):
            match = DISTRICT_RE.search(line)
            current = {"district": int(match.group(1)) if match else len(districts) + 1, "rows": [], "official_total_votes": None}
            districts.append(current)
            continue
        if not current:
            continue
        line = " ".join("0" if token in ZERO_OCR_TOKENS else token for token in line.split())
        if lowered.startswith("total votes"):
            current["official_total_votes"] = [value for value in (number(match) for match in NUMBER_RE.findall(line)) if value is not None]
            for index, value in enumerate(current["official_total_votes"]):
                current["official_total_votes"][index] = STATE_TOTAL_OCR_CORRECTIONS.get((office, current["district"], index), value)
            continue
        matches = NUMBER_RE.findall(line)
        values = [value for value in (number(match) for match in matches) if value is not None]
        if len(values) < 1:
            continue
        county = line[:line.find(matches[0])].strip(" _|:;-")
        county = COUNTY_OCR_ALIASES.get(county.casefold(), county)
        if county.casefold() in county_names:
            corrected_values = list(values)
            for index, value in enumerate(corrected_values):
                corrected_values[index] = STATE_ROW_OCR_CORRECTIONS.get((office, current["district"], county, index), value)
            current["rows"].append({"county": county, "values": corrected_values, "ocr_values": values, "raw": line})
    for district in districts:
        district["row_count"] = len(district["rows"])
        width = len(district["official_total_votes"] or [])
        district["summed_columns"] = [sum(row["values"][index] for row in district["rows"] if len(row["values"]) > index) for index in range(max(width, 1))]
        district["all_columns_match"] = district["summed_columns"][:width] == (district["official_total_votes"] or [])
    return districts


def extract_state_candidate_headers(text: str, office: str) -> list[dict[str, Any]]:
    """Extract candidate names from certified table headers using party-column anchors."""
    if office not in {"State Senate", "State House"}:
        raise ValueError("office must be State Senate or State House")
    county_names = {
        row["county_name"].casefold()
        for row in json.loads((ROOT_DIR / "public/results/county-presidential-summary.json").read_text())["counties"]
        if row["state_po"] == "KY"
    }
    lines = text.splitlines()
    section_heading = "State Senator" if office == "State Senate" else "State Representative"
    start = next((index for index, line in enumerate(lines) if line.strip().lower() == section_heading.lower()), None)
    if start is None:
        return []
    end = next((index for index in range(start + 1, len(lines)) if lines[index].strip().lower() == "for the office of"), len(lines))
    district_matches = [
        (index, re.match(r"(\d+)(?:st|nd|rd|th) (Senatorial|Representative) District", lines[index].strip(), re.I))
        for index in range(start, end)
    ]
    district_matches = [(index, match) for index, match in district_matches if match]
    extracted: list[dict[str, Any]] = []
    for position, (district_start, district_match) in enumerate(district_matches):
        district_end = district_matches[position + 1][0] if position + 1 < len(district_matches) else end
        party_line_index = next((index for index in range(district_start + 1, district_end) if any(label in lines[index] for label in ("Republican Party", "Democratic Party", "Write-In"))), None)
        if party_line_index is None:
            continue
        party_labels = [(label, lines[party_line_index].find(label)) for label in ("Republican Party", "Democratic Party", "Write-In") if lines[party_line_index].find(label) >= 0]
        first_county = next(
            (
                index
                for index in range(party_line_index + 1, district_end)
                if lines[index].strip()
                and lines[index].strip().split()[0].casefold() in county_names
                and re.search(r"\d", lines[index])
            ),
            district_end,
        )
        candidates: list[dict[str, str]] = []
        for label, anchor in sorted(party_labels, key=lambda item: item[1]):
            fragments: list[str] = []
            for line in lines[party_line_index + 1:first_county]:
                for token in re.finditer(r"\S+", line):
                    value = token.group()
                    if any(character.isalpha() for character in value):
                        nearest = min(sorted(party_labels, key=lambda item: item[1]), key=lambda item: abs(token.start() - item[1]))
                        if nearest[0] == label:
                            fragments.append(value)
            if fragments:
                party = "REPUBLICAN" if label == "Republican Party" else "DEMOCRAT" if label == "Democratic Party" else "OTHER"
                candidates.append({"candidate": re.sub(r"\s+", " ", " ".join(fragments)).strip(), "party": party})
        extracted.append({"office": office, "district": int(district_match.group(1)), "candidates": candidates})
    return extracted


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
    result["us_house_contests"] = build_us_house_contests(text)
    result["state_senate_county_rows"] = parse_state_legislative_rows(text, "State Senate")
    result["state_house_county_rows"] = parse_state_legislative_rows(text, "State House")
    result["state_senate_candidate_headers"] = extract_state_candidate_headers(text, "State Senate")
    result["state_house_candidate_headers"] = extract_state_candidate_headers(text, "State House")
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
        "us_house_all_columns_match": len(result["us_house_county_rows"]) == 6 and all(item["all_columns_match"] for item in result["us_house_county_rows"]),
        "expected_state_senate_districts": 19,
        "state_senate_districts_detected": len(state_senate["districts"]) if state_senate else 0,
        "state_house_districts_detected": sum(1 for item in result["contest_totals"] if item["office"] == "State House"),
        "state_senate_county_rows_complete": len(result["state_senate_county_rows"]) == 19 and all(item["row_count"] > 0 for item in result["state_senate_county_rows"]),
        "state_house_county_rows_complete": len(result["state_house_county_rows"]) == 100 and all(item["row_count"] > 0 for item in result["state_house_county_rows"]),
        "state_senate_totals_match": all(item["all_columns_match"] for item in result["state_senate_county_rows"]),
        "state_house_totals_match": all(item["all_columns_match"] for item in result["state_house_county_rows"]),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {result['row_count']} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
