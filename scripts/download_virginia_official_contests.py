#!/usr/bin/env python3
"""Download verified Virginia contest CSVs from the official contest inventory."""

from __future__ import annotations

import concurrent.futures
import json
import re
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT_DIR / "public/results/virginia-official-contest-inventory.json"
RAW_DIR = ROOT_DIR / "data/raw/official/virginia/contests"


def download(item: dict) -> str:
    year = item["year"]
    contest_id = item["contest_id"]
    path = RAW_DIR / f"va_{year}_{contest_id}_{re.sub(r'[^A-Za-z0-9]+', '_', item['office']).lower()}.csv"
    if path.exists() and path.stat().st_size > 100:
        return f"existing {path.name}"
    request = urllib.request.Request(item["csv_url"], headers={"User-Agent": "election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    if b"," not in data[:1000]:
        raise RuntimeError(f"Unexpected Virginia contest response for {contest_id}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return f"downloaded {path.name}"


def main() -> int:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for future in concurrent.futures.as_completed([executor.submit(download, item) for item in inventory["contests"]]):
            try:
                print(future.result())
            except Exception as exc:
                failures.append(str(exc))
    if failures:
        for failure in failures:
            print(f"failed: {failure}")
        raise SystemExit(f"{len(failures)} Virginia contest downloads failed")
    print(f"Downloaded {len(inventory['contests'])} verified Virginia contest CSVs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
