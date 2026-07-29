#!/usr/bin/env python3
"""Stage official Georgia presidential source ZIPs.

Georgia's site can block scripted downloads. If the direct download fails, place
the ZIP from the SOS historical results page in the project root or raw source
directory and run this command again.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from election_db import ROOT_DIR
from georgia_presidential_config import GEORGIA_PRESIDENTIAL_SOURCES, raw_path


def is_valid_zip(path: Path) -> bool:
    return path.exists() and zipfile.is_zipfile(path)


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())
    if not is_valid_zip(path):
        path.unlink(missing_ok=True)
        raise RuntimeError("Downloaded response was not a ZIP file")


def stage_source(source, *, optional: bool) -> bool:
    destination = ROOT_DIR / raw_path(source)
    if is_valid_zip(destination):
        print(f"Georgia {source.year} official results already staged: {destination.relative_to(ROOT_DIR)}")
        return True

    manual_path = ROOT_DIR / source.file_name
    if is_valid_zip(manual_path):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(manual_path, destination)
        print(f"Staged Georgia {source.year} official results from {manual_path.name}.")
        return True

    try:
        print(f"Downloading Georgia {source.year} official results...")
        download(source.url, destination)
        return True
    except (OSError, RuntimeError, urllib.error.URLError) as exc:
        message = (
            f"Could not stage Georgia {source.year} official results: {exc}. "
            f"Download {source.url} manually and place {source.file_name} in the project root."
        )
        if optional:
            print(message)
            return False
        raise RuntimeError(message) from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--optional", action="store_true", help="Return success when Georgia files are unavailable.")
    args = parser.parse_args()

    staged = [stage_source(source, optional=args.optional) for source in GEORGIA_PRESIDENTIAL_SOURCES.values()]
    if all(staged):
        print("Staged official Georgia presidential source files.")
    elif args.optional:
        print("Skipped unavailable Georgia official presidential source files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
