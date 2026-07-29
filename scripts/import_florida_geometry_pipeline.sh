#!/usr/bin/env bash
set -euo pipefail

python3 scripts/download_florida_geometry.py --all
python3 scripts/register_florida_geometry.py --all
python3 scripts/generate_florida_geometry_geojson.py --all
python3 scripts/validate_florida_geometry.py --all
python3 scripts/generate_florida_geometry_manifest.py
