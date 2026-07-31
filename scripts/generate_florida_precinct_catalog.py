#!/usr/bin/env python3
"""Build the frontend catalog of generated Florida precinct bundles."""

from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BUNDLE_DIR = ROOT_DIR / "public/results/precincts"
OUTPUT_PATH = ROOT_DIR / "public/results/florida-precinct-catalog.json"


def main() -> None:
    bundles = []
    for path in sorted(BUNDLE_DIR.glob("florida-*-precincts.json")):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        bundles.append(
            {
                "year": bundle["election"]["year"],
                "county_fips": bundle["county"]["fips"],
                "county_name": bundle["county"]["name"],
                "bundle_url": f"/results/precincts/{path.name}",
                "geometry_layer_key": bundle["geometry"]["layer_key"],
                "quality_grade": bundle["source"]["quality_grade"],
                "map_ready": bundle["geometry"].get("matched_result_precinct_count", 0) > 0,
            }
        )
    OUTPUT_PATH.write_text(json.dumps({"bundles": bundles}, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT_DIR)} with {len(bundles)} bundles.")


if __name__ == "__main__":
    main()
