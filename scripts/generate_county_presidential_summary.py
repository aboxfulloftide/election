#!/usr/bin/env python3
"""Generate the frontend county presidential summary from MySQL."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR, connect
from fetch_results import DOI, PUBLIC_RESULTS_DIR, SUMMARY_PATH


def build_summary() -> dict[str, Any]:
    connection = connect()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
              e.year,
              j.name AS county_name,
              j.state_po,
              j.fips AS county_fips,
              sj.name AS state_name,
              p.canonical_code AS party,
              r.votes,
              r.total_votes,
              sf.retrieved_at,
              sf.quality_grade,
              s.name AS source_name,
              s.license_name,
              s.homepage_url
            FROM results r
            JOIN contests c ON c.id = r.contest_id
            JOIN elections e ON e.id = c.election_id
            JOIN offices o ON o.id = c.office_id
            JOIN contest_candidates cc ON cc.id = r.contest_candidate_id
            JOIN parties p ON p.id = cc.party_id
            JOIN reporting_units ru ON ru.id = r.reporting_unit_id
            JOIN jurisdictions j ON j.id = ru.jurisdiction_id
            LEFT JOIN jurisdictions sj ON sj.id = j.parent_jurisdiction_id
            JOIN source_files sf ON sf.id = r.source_file_id
            JOIN sources s ON s.id = sf.source_id
            WHERE o.name = 'President'
              AND o.level = 'federal'
              AND e.election_type = 'general'
              AND ru.unit_type = 'county'
              AND r.vote_mode = 'total'
            ORDER BY e.year, j.fips, p.canonical_code
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    county_rows: dict[str, dict[str, Any]] = {}
    years: set[int] = set()
    source_rows = [row for row in rows if row.get("source_name")]
    latest_source = source_rows[-1] if source_rows else {}

    for row in rows:
        year = int(row["year"])
        years.add(year)
        fips = str(row["county_fips"]).zfill(5)
        county = county_rows.setdefault(
            fips,
            {
                "fips": fips,
                "state": row["state_name"] or row["state_po"],
                "state_po": row["state_po"],
                "county_name": row["county_name"],
                "results": {},
            },
        )
        result = county["results"].setdefault(
            str(year),
            {
                "totalvotes": int(row["total_votes"] or 0),
                "parties": {},
            },
        )
        party = row["party"] or "OTHER"
        result["parties"][party] = result["parties"].get(party, 0) + int(row["votes"] or 0)

    for county in county_rows.values():
        for result in county["results"].values():
            parties = result["parties"]
            total = result["totalvotes"] or sum(parties.values())
            ordered = sorted(parties.items(), key=lambda item: item[1], reverse=True)
            winner_party, winner_votes = ordered[0] if ordered else ("OTHER", 0)
            runner_up_votes = ordered[1][1] if len(ordered) > 1 else 0
            dem_votes = parties.get("DEMOCRAT", 0)
            rep_votes = parties.get("REPUBLICAN", 0)
            margin_votes = winner_votes - runner_up_votes

            result["totalvotes"] = total
            result["winner_party"] = winner_party
            result["winner_votes"] = winner_votes
            result["margin_votes"] = margin_votes
            result["margin_pct"] = round((margin_votes / total) * 100, 2) if total else 0
            result["dem_share"] = round((dem_votes / total) * 100, 2) if total else 0
            result["rep_share"] = round((rep_votes / total) * 100, 2) if total else 0
            result["two_party_margin"] = round(((dem_votes - rep_votes) / total) * 100, 2) if total else 0

    return {
        "source": {
            "name": latest_source.get("source_name") or "MIT Election Data and Science Lab",
            "doi": DOI,
            "url": "https://doi.org/10.7910/DVN/VOQCHQ",
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "dataverse_version": "20.0",
            "dataverse_release_time": None,
            "license": latest_source.get("license_name") or "CC0 1.0",
            "quality_grade": latest_source.get("quality_grade") or "C",
        },
        "years": sorted(years),
        "counties": sorted(county_rows.values(), key=lambda item: item["fips"]),
    }


def main() -> int:
    output_path = ROOT_DIR / SUMMARY_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = build_summary()
    output_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {Path(SUMMARY_PATH)} with {len(summary['counties'])} counties and {len(summary['years'])} years.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

