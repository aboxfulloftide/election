#!/usr/bin/env bash
set -euo pipefail

npm run db:apply
python3 scripts/download_florida_precinct.py --all
python3 scripts/import_florida_general.py --all
python3 scripts/validate_florida_general.py --all
python3 scripts/generate_florida_summary.py --all
