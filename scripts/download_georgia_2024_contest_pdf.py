#!/usr/bin/env python3
"""Stage Georgia's official 2024 contest-comparison PDF."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from election_db import ROOT_DIR

URL = "https://sos.ga.gov/sites/default/files/2024-11/contest_results_comparison_with_jurisdiction_details_0.pdf"
DESTINATION = ROOT_DIR / "data/raw/official/georgia/contest_results_comparison_with_jurisdiction_details_0.pdf"


def main() -> int:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        content = response.read()
    if not content.startswith(b"%PDF"):
        raise RuntimeError("Georgia 2024 response was not a PDF")
    DESTINATION.write_bytes(content)
    print(f"Staged {DESTINATION.relative_to(ROOT_DIR)} ({len(content):,} bytes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
