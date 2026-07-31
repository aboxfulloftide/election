#!/usr/bin/env python3
"""Stage Georgia's official 2020 full general-election archive."""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from election_db import ROOT_DIR
from georgia_official_config import GEORGIA_CONTEST_SOURCES, raw_path


def stage(optional: bool) -> bool:
    source = GEORGIA_CONTEST_SOURCES[2020]
    destination = ROOT_DIR / raw_path(source)
    if zipfile.is_zipfile(destination):
        print(f"Georgia 2020 full archive already staged: {destination.relative_to(ROOT_DIR)}")
        return True
    manual = ROOT_DIR / source.file_name
    try:
        if zipfile.is_zipfile(manual):
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(manual, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            request = urllib.request.Request(source.url, headers={"User-Agent": "Mozilla/5.0 election-night-map/0.1"})
            with urllib.request.urlopen(request, timeout=180) as response:
                destination.write_bytes(response.read())
        if not zipfile.is_zipfile(destination):
            destination.unlink(missing_ok=True)
            raise RuntimeError("response was not a ZIP file")
    except (OSError, RuntimeError, urllib.error.URLError) as exc:
        message = f"Could not stage Georgia 2020 full archive: {exc}. Download {source.url} in a browser and place {source.file_name} in the project root."
        if optional:
            print(message)
            return False
        raise RuntimeError(message) from exc
    print(f"Staged {destination.relative_to(ROOT_DIR)}.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--optional", action="store_true")
    args = parser.parse_args()
    available = stage(args.optional)
    return 0 if available or args.optional else 1


if __name__ == "__main__":
    sys.exit(main())
