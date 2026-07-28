#!/usr/bin/env python3
"""Generate app-ready Florida statewide contest summaries from MySQL."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR, connect
from florida_precinct_config import FloridaGeneralElection, selected_elections


OUTPUT_DIR = ROOT_DIR / "public/results"


def build_summary(election: FloridaGeneralElection) -> dict[str, Any]:
    connection = connect()
    cursor = connection.cursor(dictionary=True)
    office_names = sorted(set(election.target_contests.values()))
    office_sql = ", ".join(["%s"] * len(office_names))

    try:
        cursor.execute(
            f"""
            SELECT
              c.id AS contest_id,
              o.name AS office_name,
              c.notes AS contest_name,
              county.name AS county_name,
              county.fips AS county_fips,
              cand.display_name AS candidate_name,
              p.canonical_code AS party,
              SUM(r.votes) AS votes,
              s.name AS source_name,
              s.homepage_url,
              sf.url AS source_file_url,
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
            JOIN jurisdictions county ON county.id = precinct.parent_jurisdiction_id
            WHERE sf.url = %s
              AND e.year = %s
              AND e.election_type = 'general'
              AND ru.state_po = 'FL'
              AND o.name IN ({office_sql})
            GROUP BY
              c.id, o.name, c.notes, county.name, county.fips,
              cand.display_name, p.canonical_code,
              s.name, s.homepage_url, sf.url, sf.quality_grade
            ORDER BY o.name, county.fips, votes DESC
            """,
            (election.url, election.year, *office_names),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    contests: dict[int, dict[str, Any]] = {}
    latest_source = rows[-1] if rows else {}

    for row in rows:
        contest = contests.setdefault(
            int(row["contest_id"]),
            {
                "contest_id": int(row["contest_id"]),
                "office": row["office_name"],
                "name": row["contest_name"],
                "state": "Florida",
                "state_po": "FL",
                "candidates": {},
                "counties": {},
            },
        )
        candidate_key = f"{row['candidate_name']}|{row['party']}"
        candidate = contest["candidates"].setdefault(
            candidate_key,
            {
                "candidate": row["candidate_name"],
                "party": row["party"],
                "votes": 0,
            },
        )
        votes = int(row["votes"] or 0)
        candidate["votes"] += votes

        county = contest["counties"].setdefault(
            row["county_fips"],
            {
                "fips": row["county_fips"],
                "county_name": row["county_name"],
                "candidates": {},
            },
        )
        county["candidates"][candidate_key] = {
            "candidate": row["candidate_name"],
            "party": row["party"],
            "votes": votes,
        }

    output_contests = []
    for contest in contests.values():
        candidates = sorted(contest["candidates"].values(), key=lambda item: item["votes"], reverse=True)
        total_votes = sum(candidate["votes"] for candidate in candidates)
        winner = candidates[0] if candidates else None
        runner_up = candidates[1] if len(candidates) > 1 else None
        counties = []

        for county in contest["counties"].values():
            county_candidates = sorted(county["candidates"].values(), key=lambda item: item["votes"], reverse=True)
            county_total = sum(candidate["votes"] for candidate in county_candidates)
            county_winner = county_candidates[0] if county_candidates else None
            county_runner_up = county_candidates[1] if len(county_candidates) > 1 else None
            counties.append(
                {
                    "fips": county["fips"],
                    "county_name": county["county_name"],
                    "total_votes": county_total,
                    "winner": county_winner,
                    "margin_votes": (
                        county_winner["votes"] - county_runner_up["votes"] if county_winner and county_runner_up else 0
                    ),
                    "candidates": county_candidates,
                }
            )

        output_contests.append(
            {
                "contest_id": contest["contest_id"],
                "office": contest["office"],
                "name": contest["name"],
                "state": contest["state"],
                "state_po": contest["state_po"],
                "total_votes": total_votes,
                "winner": winner,
                "margin_votes": winner["votes"] - runner_up["votes"] if winner and runner_up else 0,
                "candidates": candidates,
                "counties": sorted(counties, key=lambda item: item["fips"]),
            }
        )

    return {
        "source": {
            "name": latest_source.get("source_name") or "Florida Division of Elections",
            "url": latest_source.get("homepage_url")
            or "https://dos.fl.gov/elections/data-statistics/elections-data/precinct-level-election-results/",
            "source_file_url": latest_source.get("source_file_url") or election.url,
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "quality_grade": latest_source.get("quality_grade") or "A",
        },
        "election": {
            "year": election.year,
            "date": election.election_date.isoformat(),
            "type": "general",
            "state": "Florida",
        },
        "contests": sorted(output_contests, key=lambda item: item["office"]),
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, help="Florida general election year to generate. Defaults to 2022.")
    parser.add_argument("--all", action="store_true", help="Generate summaries for every configured Florida general election.")
    args = parser.parse_args()

    summaries = []
    for election in selected_elections(args.year, args.all):
        summary = build_summary(election)
        summaries.append(summary)
        output_path = OUTPUT_DIR / f"florida-{election.year}-statewide-summary.json"
        write_summary(output_path, summary)
        print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {len(summary['contests'])} contests.")

    if args.all:
        combined = {
            "source": {
                "name": "Florida Division of Elections",
                "url": "https://dos.fl.gov/elections/data-statistics/elections-data/precinct-level-election-results/",
                "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
                "quality_grade": "A",
            },
            "elections": summaries,
        }
        output_path = OUTPUT_DIR / "florida-statewide-summary.json"
        write_summary(output_path, combined)
        print(f"Wrote {output_path.relative_to(ROOT_DIR)} with {len(summaries)} elections.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
