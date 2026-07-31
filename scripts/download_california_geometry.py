#!/usr/bin/env python3
"""Download official California district geometry source files."""

from __future__ import annotations

import argparse
import sys
import urllib.request

from california_geometry_config import selected_layers


def download(url: str, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        path.write_bytes(response.read())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", help="Geometry layer key to download. Defaults to congressional districts.")
    parser.add_argument("--all", action="store_true", help="Download every configured California geometry layer.")
    args = parser.parse_args()

    for layer in selected_layers(args.layer, args.all):
        print(f"Downloading {layer.name}...")
        download(layer.source_url, layer.raw_path)
    print("Downloaded official California geometry source files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
