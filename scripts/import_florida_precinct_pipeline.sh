#!/usr/bin/env bash
set -euo pipefail

python3 scripts/generate_florida_precinct_geometry.py
python3 scripts/generate_florida_arcgis_precinct_geometry.py
python3 scripts/generate_florida_precinct_drilldown.py --year 2012
python3 scripts/generate_florida_precinct_drilldown.py --year 2014
python3 scripts/generate_florida_precinct_drilldown.py --year 2020 --county-fips 12011 --county-name "Broward County" --output-slug broward
python3 scripts/generate_florida_precinct_drilldown.py --year 2022 --county-fips 12011 --county-name "Broward County" --output-slug broward
python3 scripts/generate_florida_precinct_drilldown.py --year 2024 --county-fips 12011 --county-name "Broward County" --output-slug broward
python3 scripts/generate_florida_precinct_catalog.py
python3 scripts/check_florida_precinct_join.py --all --report public/results/florida-precinct-join-report.json
