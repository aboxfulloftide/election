#!/usr/bin/env python3
"""Download official Florida district geometry source files."""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

from election_db import ROOT_DIR
from florida_geometry_config import FloridaGeometryLayer, selected_layers


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


def download_layer(layer: FloridaGeometryLayer, force: bool) -> None:
    for url, path in (
        (layer.shapefile_url, layer.shapefile_path),
        (layer.block_equivalency_url, layer.block_equivalency_path),
    ):
        wrote = download(url, path, force)
        action = "Downloaded" if wrote else "Already present"
        print(f"{action}: {path.relative_to(ROOT_DIR)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", help="Geometry layer key to download. Defaults to congressional districts.")
    parser.add_argument("--all", action="store_true", help="Download every configured Florida geometry layer.")
    parser.add_argument("--force", action="store_true", help="Redownload files even when they already exist.")
    args = parser.parse_args()

    for layer in selected_layers(args.layer, args.all):
        download_layer(layer, args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
