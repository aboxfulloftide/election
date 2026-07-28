#!/usr/bin/env bash
set -euo pipefail

npm run db:apply
python3 scripts/fetch_results.py
python3 scripts/import_mit_county_presidential.py
python3 scripts/validate_mit_county_presidential.py
python3 scripts/generate_county_presidential_summary.py
