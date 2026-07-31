#!/usr/bin/env python3
"""Inventory Virginia official contest pages and CSV endpoints by election year."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "public/results/virginia-official-contest-inventory.json"
BASE_URL = "https://historical.elections.virginia.gov"
RANGES = {2020: range(144400, 145000), 2024: range(161200, 161800)}
OFFICE_MAP = {
    "President": "President",
    "U.S. Senate": "U.S. Senate",
    "U.S. House": "U.S. House",
    "Governor": "Governor",
    "State Senate": "State Senate",
    "State House": "State House",
    "House of Delegates": "State House",
}


def contest_from_page(contest_id: int) -> dict[str, Any] | None:
    url = f"{BASE_URL}/contest/{contest_id}"
    request = urllib.request.Request(url, headers={"User-Agent": "election-night-map/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError:
        return None
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))["props"]["pageProps"]["contest"]
    except (KeyError, json.JSONDecodeError):
        return None
    event = data.get("event") or {}
    year_match = re.match(r"(\d{4})-", str(event.get("startDate", "")))
    year = int(year_match.group(1)) if year_match else None
    office_name = (data.get("office") or {}).get("name")
    normalized_office = OFFICE_MAP.get(office_name or "")
    if year not in RANGES or normalized_office is None or event.get("type", {}).get("name") != "General Election":
        return None
    return {
        "contest_id": str(data["id"]),
        "year": year,
        "office": normalized_office,
        "source_office": office_name,
        "contest_url": url,
        "csv_url": f"https://va2.elstats3.civera.com/api/download_contest/{data['id']}_table.csv?split_party=false",
        "division": (data.get("division") or {}).get("displayName"),
        "district": data.get("officeModifier") or None,
        "verified_at": data.get("verifiedAt"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--year", type=int, choices=sorted(RANGES))
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()
    selected_years = [args.year] if args.year else sorted(RANGES)
    ids = []
    for year in selected_years:
        values = RANGES[year]
        start = args.start if args.start is not None else values.start
        end = args.end if args.end is not None else values.stop
        ids.extend(range(start, end))
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        for result in executor.map(contest_from_page, ids):
            if result:
                results.append(result)
    existing: list[dict[str, Any]] = []
    if OUTPUT_PATH.exists():
        try:
            existing = json.loads(OUTPUT_PATH.read_text(encoding="utf-8")).get("contests", [])
        except json.JSONDecodeError:
            existing = []
    by_id = {item["contest_id"]: item for item in existing}
    by_id.update({item["contest_id"]: item for item in results})
    results = sorted(by_id.values(), key=lambda item: (item["year"], item["office"], item["contest_id"]))
    output = {"source": BASE_URL, "years": sorted(RANGES), "contests": results}
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT_DIR)} with {len(results)} contests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
