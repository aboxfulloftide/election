#!/usr/bin/env python3
"""Normalize verified Virginia contest CSVs into statewide contest summaries."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/virginia/contests"
INVENTORY_PATH = ROOT_DIR / "public/results/virginia-official-contest-inventory.json"
OUTPUT_PATH = ROOT_DIR / "public/results/virginia-statewide-summary.json"

PARTY_MAP = {"DEMOCRATIC": "DEMOCRAT", "REPUBLICAN": "REPUBLICAN", "LIBERTARIAN": "LIBERTARIAN", "GREEN": "GREEN", "INDEPENDENT": "INDEPENDENT"}


def int_value(value: str) -> int:
    return int((value or "0").replace(",", "").strip() or 0)


def parse_file(path: Path, inventory_item: dict[str, Any]) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 3:
        raise RuntimeError(f"Virginia contest CSV is too short: {path.name}")
    header, party_row = rows[0], rows[1]
    total_column = next((index for index, value in enumerate(header) if value.strip() == "Total Votes Cast"), None)
    if total_column is None:
        raise RuntimeError(f"Virginia contest CSV has no total column: {path.name}")
    total_row = next((row for row in rows[2:] if row and row[0] in {"State", "Congressional District"}), None)
    if total_row is None:
        raise RuntimeError(f"Virginia contest CSV has no statewide or district total: {path.name}")
    candidates = []
    for index in range(2, total_column):
        name = header[index].strip() if index < len(header) else ""
        if not name or name == "Write-Ins":
            continue
        party = PARTY_MAP.get(party_row[index].strip().upper(), "OTHER") if index < len(party_row) else "OTHER"
        candidates.append({"candidate": name, "party": party, "votes": int_value(total_row[index] if index < len(total_row) else "0")})
    candidates.sort(key=lambda item: (-item["votes"], item["candidate"]))
    if not candidates:
        raise RuntimeError(f"Virginia contest has no candidates: {path.name}")
    district = None
    if total_row[0] == "Congressional District":
        district = int(re.sub(r"\D", "", total_row[1]))
    contest = {
        "contest_id": inventory_item["contest_id"],
        "office": inventory_item["office"],
        "name": f"Virginia {inventory_item['year']} {inventory_item['office']}" + (f" District {district}" if district else ""),
        "state": "Virginia",
        "state_po": "VA",
        "year": inventory_item["year"],
        "source_url": inventory_item["csv_url"],
        "source_format": "virginia-official-contest-csv",
        "quality_grade": "A",
        "total_votes": sum(candidate["votes"] for candidate in candidates),
        "winner": candidates[0],
        "margin_votes": candidates[0]["votes"] - candidates[1]["votes"] if len(candidates) > 1 else 0,
        "candidates": candidates,
    }
    if district is not None:
        contest["district_number"] = district
        contest["district_label"] = f"{district} Congressional District"
    return contest


def main() -> int:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    contests = []
    for item in inventory["contests"]:
        safe_office = re.sub(r"[^A-Za-z0-9]+", "_", item["office"]).lower()
        path = RAW_DIR / f"va_{item['year']}_{item['contest_id']}_{safe_office}.csv"
        contests.append(parse_file(path, item))
    output = {"source": {"name": "Virginia Department of Elections historical contest database", "url": "https://historical.elections.virginia.gov/", "official": True, "quality_grade": "A"}, "state_po": "VA", "elections": []}
    for year in sorted({contest["year"] for contest in contests}):
        output["elections"].append({"election": {"state": "Virginia", "state_po": "VA", "year": year}, "contests": [contest for contest in contests if contest["year"] == year]})
    OUTPUT_PATH.write_text(json.dumps(output, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT_DIR)} with {len(contests)} contests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
