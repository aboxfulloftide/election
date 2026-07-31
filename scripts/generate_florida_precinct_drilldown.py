#!/usr/bin/env python3
"""Generate Miami-Dade precinct result bundles joined to official geometry vintages."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR, connect
from florida_precinct_config import election_for_year


OUTPUT_DIR = ROOT_DIR / "public/results/precincts"
GEOMETRY_MANIFEST = ROOT_DIR / "public/results/florida-precinct-geometry-layers.json"


def normalized_precinct(value: str, name: str | None) -> str:
    if name:
        cleaned_name = name.strip().upper()
        if re.fullmatch(r"[A-Z]\d{3}", cleaned_name):
            return cleaned_name
        match = re.search(r"(\d{4})$", cleaned_name)
        if match:
            return str(int(match.group(1)))
    cleaned_value = str(value).strip().upper().split(".", 1)[0]
    if re.fullmatch(r"[A-Z]\d{3}", cleaned_value):
        return cleaned_value
    return str(int(cleaned_value))


def precinct_sort_key(value: str) -> tuple[int, int | str]:
    return (0, int(value)) if value.isdigit() else (1, value)


def build_bundle(year: int, county_fips: str = "12086", county_name: str = "Miami-Dade County") -> dict[str, Any]:
    election = election_for_year(year)
    geometry_manifest = json.loads(GEOMETRY_MANIFEST.read_text(encoding="utf-8"))
    geometry_layer = next(
        layer for layer in geometry_manifest["layers"] if layer["vintage"] == str(year) and layer["county_fips"] == county_fips
    )
    geometry_path = ROOT_DIR / "public" / geometry_layer["geometry_url"].lstrip("/")
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    geometry_precinct_ids = {str(feature["properties"]["precinct_id"]) for feature in geometry["features"]}
    connection = connect()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT c.id AS contest_id, o.name AS office_name, c.district_label, c.notes AS contest_name,
                   ru.precinct_code, precinct.name AS precinct_name, cand.display_name AS candidate_name, p.canonical_code AS party,
                   SUM(r.votes) AS votes, s.name AS source_name, s.homepage_url, sf.url AS source_file_url,
                   sf.quality_grade
            FROM results r
            JOIN source_files sf ON sf.id = r.source_file_id
            JOIN sources s ON s.id = sf.source_id
            JOIN contests c ON c.id = r.contest_id
            JOIN elections e ON e.id = c.election_id
            JOIN offices o ON o.id = c.office_id
            JOIN contest_candidates cc ON cc.id = r.contest_candidate_id
            JOIN candidates cand ON cand.id = cc.candidate_id
            JOIN parties p ON p.id = cc.party_id
            JOIN reporting_units ru ON ru.id = r.reporting_unit_id
            JOIN jurisdictions precinct ON precinct.id = ru.jurisdiction_id
            WHERE sf.url = %s AND e.year = %s AND e.election_type = 'general'
              AND ru.county_fips = %s AND ru.unit_type = 'precinct'
            GROUP BY c.id, o.name, c.district_label, c.notes, ru.precinct_code, precinct.name,
                     cand.display_name, p.canonical_code, s.name, s.homepage_url,
                     sf.url, sf.quality_grade
            ORDER BY o.name, c.id, CAST(ru.precinct_code AS UNSIGNED), votes DESC
            """,
            (election.url, year, county_fips),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    contests: dict[int, dict[str, Any]] = {}
    for row in rows:
        contest = contests.setdefault(
            int(row["contest_id"]),
            {
                "contest_id": int(row["contest_id"]),
                "office": row["office_name"],
                "district_label": row["district_label"],
                "name": row["contest_name"],
                "precincts": {},
            },
        )
        precinct_id = normalized_precinct(row["precinct_code"], row["precinct_name"])
        precinct = contest["precincts"].setdefault(precinct_id, {"precinct_id": precinct_id, "candidates": {}})
        key = f"{row['candidate_name']}|{row['party']}"
        precinct["candidates"][key] = {
            "candidate": row["candidate_name"],
            "party": row["party"],
            "votes": int(row["votes"] or 0),
        }

    output_contests = []
    for contest in contests.values():
        precincts = []
        for precinct in contest["precincts"].values():
            candidates = sorted(precinct["candidates"].values(), key=lambda item: item["votes"], reverse=True)
            winner = candidates[0] if candidates else None
            runner_up = candidates[1] if len(candidates) > 1 else None
            precincts.append(
                {
                    "precinct_id": precinct["precinct_id"],
                    "total_votes": sum(candidate["votes"] for candidate in candidates),
                    "winner": winner,
                    "margin_votes": winner["votes"] - runner_up["votes"] if winner and runner_up else 0,
                    "candidates": candidates,
                }
            )
        output_contests.append(
            {
                "contest_id": contest["contest_id"],
                "office": contest["office"],
                "district_label": contest["district_label"],
                "name": contest["name"],
                "precincts": sorted(precincts, key=lambda item: precinct_sort_key(item["precinct_id"])),
            }
        )

    result_precinct_ids = {
        precinct["precinct_id"]
        for contest in output_contests
        for precinct in contest["precincts"]
    }
    matched_result_precinct_ids = result_precinct_ids & geometry_precinct_ids
    geometry_layer = {
        **geometry_layer,
        "result_precinct_count": len(result_precinct_ids),
        "matched_result_precinct_count": len(matched_result_precinct_ids),
        "unmatched_result_precinct_count": len(result_precinct_ids - geometry_precinct_ids),
    }

    return {
        "source": {
            "name": "Florida Division of Elections",
            "url": "https://dos.fl.gov/elections/data-statistics/elections-data/precinct-level-election-results/",
            "source_file_url": election.url,
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "quality_grade": "A",
        },
        "election": {"year": year, "date": election.election_date.isoformat(), "type": "general", "state": "Florida"},
        "county": {"fips": county_fips, "name": county_name},
        "geometry": geometry_layer,
        "contests": sorted(output_contests, key=lambda item: (item["office"], item["district_label"] or "")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--county-fips", default="12086")
    parser.add_argument("--county-name", default="Miami-Dade County")
    parser.add_argument("--output-slug", default="miami-dade")
    args = parser.parse_args()
    bundle = build_bundle(args.year, args.county_fips, args.county_name)
    output_path = OUTPUT_DIR / f"florida-{args.output_slug}-{args.year}-precincts.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {len(bundle['contests'])} contests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
