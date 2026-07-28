#!/usr/bin/env bash
set -euo pipefail

npm run db:apply
python3 scripts/download_florida_precinct.py
python3 scripts/import_florida_2022_general.py
python3 scripts/validate_florida_2022_general.py
python3 scripts/generate_florida_2022_summary.py
