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
OCR_PATH = RAW_DIR / "ocr/2022_certified_general_election_results.txt"
OUTPUT_PATH = RAW_DIR / "2022_certified_senate_reconciliation.json"
NUMBER_RE = re.compile(r"(?<![A-Za-z])([0-9OoIl][0-9,.OoIl]*)")


def number(value: str) -> int | None:
    normalized = value.replace(",", "").replace(".", "").translate(str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1"}))
    return int(normalized) if normalized.isdigit() else None


def senate_section(text: str) -> str:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.strip().lower() == "united states senator"]
    if not starts:
        raise RuntimeError("Certified OCR does not contain a U.S. Senate section")
    start = starts[-1]
    end = next((index for index in range(start + 1, len(lines)) if lines[index].strip().lower() == "for the office of"), len(lines))
    return "\n".join(lines[start + 1 : end])


def parse_senate(text: str) -> dict[str, Any]:
    rows = []
    for raw_line in senate_section(text).splitlines():
        line = re.sub(r"\s+", " ", raw_line.replace("\f", " ")).strip()
        if not line or line.lower().startswith(("republican party", "democratic party", "rand ", "paul", "total votes")):
            continue
        matches = NUMBER_RE.findall(line)
        values = [number(match) for match in matches]
        values = [value for value in values if value is not None]
        if len(values) < 2:
            continue
        county = line[: matches[0] and line.find(matches[0])].strip(" _|:;-")
        if not county or county.lower() in {"for the office of", "united states senator"}:
            continue
        rows.append({"county": county, "values": values[:4], "raw": line})
    totals = [sum(row["values"][index] for row in rows if len(row["values"]) > index) for index in range(4)]
    return {"office": "U.S. Senate", "year": 2022, "rows": rows, "row_count": len(rows), "column_totals": totals}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=OCR_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT_DIR / args.input
    output_path = args.output if args.output.is_absolute() else ROOT_DIR / args.output
    result = parse_senate(input_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {result['row_count']} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
