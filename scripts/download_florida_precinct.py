#!/usr/bin/env python3
"""Download official Florida precinct-level election files."""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

from election_db import ROOT_DIR
from florida_precinct_config import DEFINITIONS_PATH, DEFINITIONS_URL, selected_elections


def download(url: str, path: Path, force: bool) -> bool:
    if path.exists() and path.stat().st_size > 0 and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        with path.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, help="Florida general election year to download. Defaults to 2022.")
    parser.add_argument("--all", action="store_true", help="Download every configured Florida general election ZIP.")
    parser.add_argument("--force", action="store_true", help="Redownload files even when they already exist.")
    args = parser.parse_args()

    elections = selected_elections(args.year, args.all)
    for election in elections:
        wrote = download(election.url, election.zip_path, args.force)
        action = "Downloaded" if wrote else "Already present"
        print(f"{action}: {election.zip_path.relative_to(ROOT_DIR)}")

    wrote_definitions = download(DEFINITIONS_URL, DEFINITIONS_PATH, args.force)
    action = "Downloaded" if wrote_definitions else "Already present"
    print(f"{action}: {DEFINITIONS_PATH.relative_to(ROOT_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
