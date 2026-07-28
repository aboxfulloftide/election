#!/usr/bin/env python3
"""Import MIT county presidential returns into normalized MySQL tables."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR, connect, fetch_one_id
from fetch_results import DOI, RESULTS_LABEL, RAW_DIR, parse_int


RESULTS_PATH = ROOT_DIR / RAW_DIR / RESULTS_LABEL
SOURCE_NAME = "MIT Election Data and Science Lab"
SOURCE_URL = "https://electionlab.mit.edu/data"
SOURCE_FILE_URL = "https://dataverse.harvard.edu/api/access/datafile/13573089"
DISCOVERY_URL = "https://libguides.princeton.edu/elections"

PARTY_MAP = {
    "DEMOCRAT": "DEMOCRAT",
    "REPUBLICAN": "REPUBLICAN",
    "LIBERTARIAN": "LIBERTARIAN",
    "GREEN": "GREEN",
}


def normalize_fips(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    return value.zfill(5)


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).upper()


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_or_create_source(cursor: Any) -> int:
    source_id = fetch_one_id(cursor, "SELECT id FROM sources WHERE name = %s", (SOURCE_NAME,))
    if source_id is not None:
        cursor.execute(
            """
            UPDATE sources
            SET source_type = 'compiled_dataset',
                homepage_url = %s,
                discovery_reference_url = %s,
                license_name = 'CC0 1.0',
                license_url = 'http://creativecommons.org/publicdomain/zero/1.0',
                notes = %s
            WHERE id = %s
            """,
            (
                SOURCE_URL,
                DISCOVERY_URL,
                "Compiled source for county-level presidential election returns.",
                source_id,
            ),
        )
        return source_id

    cursor.execute(
        """
        INSERT INTO sources
          (name, source_type, homepage_url, discovery_reference_url, license_name, license_url, notes)
        VALUES
          (%s, 'compiled_dataset', %s, %s, 'CC0 1.0', 'http://creativecommons.org/publicdomain/zero/1.0', %s)
        """,
        (
            SOURCE_NAME,
            SOURCE_URL,
            DISCOVERY_URL,
            "Compiled source for county-level presidential election returns.",
        ),
    )
    return int(cursor.lastrowid)


def get_or_create_source_file(cursor: Any, source_id: int, path: Path) -> int:
    file_checksum = checksum(path)
    source_file_id = fetch_one_id(
        cursor,
        "SELECT id FROM source_files WHERE source_id = %s AND checksum_sha256 = %s ORDER BY id LIMIT 1",
        (source_id, file_checksum),
    )
    if source_file_id is not None:
        return source_file_id

    cursor.execute(
        """
        INSERT INTO source_files
          (source_id, url, local_path, discovery_reference_url, retrieved_at, file_name, file_type,
           checksum_sha256, covers_year_start, covers_year_end, raw_license_text, transform_notes, quality_grade)
        VALUES
          (%s, %s, %s, %s, %s, %s, 'text/tab-separated-values',
           %s, 2000, 2024, 'CC0 1.0', %s, 'C')
        """,
        (
            source_id,
            SOURCE_FILE_URL,
            str(path.relative_to(ROOT_DIR)),
            DISCOVERY_URL,
            dt.datetime.now(dt.UTC).replace(tzinfo=None),
            path.name,
            file_checksum,
            f"Imported from Harvard Dataverse DOI {DOI}; filtered to mode=TOTAL rows.",
        ),
    )
    return int(cursor.lastrowid)


def get_or_create_election(cursor: Any, year: int) -> int:
    name = f"{year} general election"
    election_id = fetch_one_id(
        cursor,
        "SELECT id FROM elections WHERE year = %s AND election_type = 'general' AND name = %s",
        (year, name),
    )
    if election_id is not None:
        return election_id

    cursor.execute(
        """
        INSERT INTO elections (year, election_date, election_type, name, notes)
        VALUES (%s, NULL, 'general', %s, 'Election date omitted until source-specific calendar normalization is added.')
        """,
        (year, name),
    )
    return int(cursor.lastrowid)


def get_office_id(cursor: Any) -> int:
    office_id = fetch_one_id(cursor, "SELECT id FROM offices WHERE name = 'President' AND level = 'federal'", ())
    if office_id is None:
        raise RuntimeError("Missing President office seed. Run npm run db:apply first.")
    return office_id


def get_party_id(cursor: Any, party: str) -> int:
    canonical_code = PARTY_MAP.get((party or "").upper(), "OTHER")
    party_id = fetch_one_id(cursor, "SELECT id FROM parties WHERE canonical_code = %s", (canonical_code,))
    if party_id is None:
        raise RuntimeError(f"Missing party seed: {canonical_code}")
    return party_id


def get_or_create_candidate(cursor: Any, candidate: str) -> int:
    display_name = candidate.strip() or "Unknown"
    normalized = normalize_name(display_name)
    candidate_id = fetch_one_id(
        cursor,
        "SELECT id FROM candidates WHERE normalized_name = %s AND display_name = %s ORDER BY id LIMIT 1",
        (normalized, display_name),
    )
    if candidate_id is not None:
        return candidate_id

    cursor.execute(
        """
        INSERT INTO candidates (display_name, normalized_name)
        VALUES (%s, %s)
        """,
        (display_name, normalized),
    )
    return int(cursor.lastrowid)


def get_country_id(cursor: Any) -> int:
    country_id = fetch_one_id(
        cursor,
        "SELECT id FROM jurisdictions WHERE type = 'country' AND official_id = 'US'",
        (),
    )
    if country_id is None:
        raise RuntimeError("Missing United States jurisdiction seed. Run npm run db:apply first.")
    return country_id


def get_or_create_state(cursor: Any, state_name: str, state_po: str, state_fips: str, country_id: int) -> int:
    state_id = fetch_one_id(
        cursor,
        "SELECT id FROM jurisdictions WHERE type = 'state' AND official_id = %s",
        (state_po,),
    )
    if state_id is not None:
        return state_id

    cursor.execute(
        """
        INSERT INTO jurisdictions
          (type, name, state_po, fips, official_id, parent_jurisdiction_id, notes)
        VALUES
          ('state', %s, %s, %s, %s, %s, 'Created by MIT county presidential importer.')
        """,
        (state_name, state_po, state_fips, state_po, country_id),
    )
    return int(cursor.lastrowid)


def get_or_create_county(cursor: Any, county_name: str, state_po: str, county_fips: str, state_id: int) -> int:
    county_id = fetch_one_id(
        cursor,
        "SELECT id FROM jurisdictions WHERE type = 'county' AND official_id = %s",
        (county_fips,),
    )
    if county_id is not None:
        return county_id

    cursor.execute(
        """
        INSERT INTO jurisdictions
          (type, name, state_po, fips, official_id, parent_jurisdiction_id, notes)
        VALUES
          ('county', %s, %s, %s, %s, %s, 'Created by MIT county presidential importer.')
        """,
        (county_name, state_po, county_fips, county_fips, state_id),
    )
    return int(cursor.lastrowid)


def get_or_create_reporting_unit(cursor: Any, county_id: int, county_name: str, state_po: str, county_fips: str) -> int:
    unit_id = fetch_one_id(
        cursor,
        """
        SELECT id FROM reporting_units
        WHERE unit_type = 'county' AND county_fips = %s AND jurisdiction_id = %s
        ORDER BY id LIMIT 1
        """,
        (county_fips, county_id),
    )
    if unit_id is not None:
        return unit_id

    cursor.execute(
        """
        INSERT INTO reporting_units
          (jurisdiction_id, unit_type, name, state_po, county_fips, notes)
        VALUES
          (%s, 'county', %s, %s, %s, 'County-level total.')
        """,
        (county_id, county_name, state_po, county_fips),
    )
    return int(cursor.lastrowid)


def get_or_create_contest(cursor: Any, election_id: int, office_id: int, country_id: int, year: int) -> int:
    contest_id = fetch_one_id(
        cursor,
        """
        SELECT id FROM contests
        WHERE election_id = %s AND office_id = %s AND contest_jurisdiction_id = %s
          AND district_label IS NULL AND seat_label IS NULL
          AND is_special = FALSE AND is_runoff = FALSE
        ORDER BY id LIMIT 1
        """,
        (election_id, office_id, country_id),
    )
    if contest_id is not None:
        return contest_id

    cursor.execute(
        """
        INSERT INTO contests
          (election_id, office_id, contest_jurisdiction_id, notes)
        VALUES
          (%s, %s, %s, %s)
        """,
        (election_id, office_id, country_id, f"{year} U.S. presidential general election."),
    )
    return int(cursor.lastrowid)


def get_or_create_contest_candidate(cursor: Any, contest_id: int, candidate_id: int, party_id: int, source_id: int) -> int:
    contest_candidate_id = fetch_one_id(
        cursor,
        """
        SELECT id FROM contest_candidates
        WHERE contest_id = %s AND candidate_id = %s AND party_id = %s
        """,
        (contest_id, candidate_id, party_id),
    )
    if contest_candidate_id is not None:
        return contest_candidate_id

    cursor.execute(
        """
        INSERT INTO contest_candidates (contest_id, candidate_id, party_id, source_id)
        VALUES (%s, %s, %s, %s)
        """,
        (contest_id, candidate_id, party_id, source_id),
    )
    return int(cursor.lastrowid)


def read_rows(path: Path) -> list[dict[str, str]]:
    rows_by_key: dict[tuple[str, str, str, str], dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row.get("mode") != "TOTAL":
                continue
            row["county_fips"] = normalize_fips(row.get("county_fips", ""))
            if not row["county_fips"]:
                continue
            key = (
                row["year"],
                row["county_fips"],
                normalize_name(row.get("candidate") or "Unknown"),
                (row.get("party") or "OTHER").upper(),
            )
            existing = rows_by_key.get(key)
            if existing is None:
                rows_by_key[key] = row
                continue

            existing["candidatevotes"] = str(parse_int(existing.get("candidatevotes")) + parse_int(row.get("candidatevotes")))
            if parse_int(row.get("totalvotes")) > parse_int(existing.get("totalvotes")):
                existing["totalvotes"] = row.get("totalvotes", existing.get("totalvotes", "0"))

    return list(rows_by_key.values())


def import_rows(rows: list[dict[str, str]]) -> dict[str, int]:
    connection = connect()
    cursor = connection.cursor()

    try:
        source_id = get_or_create_source(cursor)
        source_file_id = get_or_create_source_file(cursor, source_id, RESULTS_PATH)
        office_id = get_office_id(cursor)
        country_id = get_country_id(cursor)

        election_cache: dict[int, int] = {}
        contest_cache: dict[int, int] = {}
        state_cache: dict[str, int] = {}
        county_cache: dict[str, int] = {}
        reporting_unit_cache: dict[str, int] = {}
        party_cache: dict[str, int] = {}
        candidate_cache: dict[str, int] = {}
        contest_candidate_cache: dict[tuple[int, int, int], int] = {}

        imported = 0
        for row in rows:
            year = int(row["year"])
            state_po = row["state_po"]
            county_fips = row["county_fips"]

            election_id = election_cache.get(year)
            if election_id is None:
                election_id = get_or_create_election(cursor, year)
                election_cache[year] = election_id
            contest_id = contest_cache.get(year)
            if contest_id is None:
                contest_id = get_or_create_contest(cursor, election_id, office_id, country_id, year)
                contest_cache[year] = contest_id
            state_id = state_cache.get(state_po)
            if state_id is None:
                state_id = get_or_create_state(cursor, row["state"], state_po, county_fips[:2], country_id)
                state_cache[state_po] = state_id
            county_id = county_cache.get(county_fips)
            if county_id is None:
                county_id = get_or_create_county(cursor, row["county_name"], state_po, county_fips, state_id)
                county_cache[county_fips] = county_id
            reporting_unit_id = reporting_unit_cache.get(county_fips)
            if reporting_unit_id is None:
                reporting_unit_id = get_or_create_reporting_unit(cursor, county_id, row["county_name"], state_po, county_fips)
                reporting_unit_cache[county_fips] = reporting_unit_id

            party_key = (row.get("party") or "OTHER").upper()
            party_id = party_cache.get(party_key)
            if party_id is None:
                party_id = get_party_id(cursor, party_key)
                party_cache[party_key] = party_id
            candidate_key = row.get("candidate") or "Unknown"
            candidate_id = candidate_cache.get(candidate_key)
            if candidate_id is None:
                candidate_id = get_or_create_candidate(cursor, candidate_key)
                candidate_cache[candidate_key] = candidate_id
            contest_candidate_key = (contest_id, candidate_id, party_id)
            contest_candidate_id = contest_candidate_cache.get(contest_candidate_key)
            if contest_candidate_id is None:
                contest_candidate_id = get_or_create_contest_candidate(cursor, contest_id, candidate_id, party_id, source_id)
                contest_candidate_cache[contest_candidate_key] = contest_candidate_id

            cursor.execute(
                """
                INSERT INTO results
                  (contest_id, contest_candidate_id, reporting_unit_id, votes, total_votes, vote_mode, source_file_id, quality_grade)
                VALUES
                  (%s, %s, %s, %s, %s, 'total', %s, 'C')
                ON DUPLICATE KEY UPDATE
                  votes = VALUES(votes),
                  total_votes = VALUES(total_votes),
                  quality_grade = VALUES(quality_grade)
                """,
                (
                    contest_id,
                    contest_candidate_id,
                    reporting_unit_id,
                    parse_int(row.get("candidatevotes")),
                    parse_int(row.get("totalvotes")),
                    source_file_id,
                ),
            )
            imported += 1

        connection.commit()
        return {
            "rows": imported,
            "years": len({int(row["year"]) for row in rows}),
            "counties": len({row["county_fips"] for row in rows}),
            "source_file_id": source_file_id,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def main() -> int:
    if not RESULTS_PATH.exists():
        raise RuntimeError(f"Missing raw results file: {RESULTS_PATH}. Run npm run data:fetch first.")

    rows = read_rows(RESULTS_PATH)
    stats = import_rows(rows)
    print(
        "Imported MIT county presidential results: "
        f"{stats['rows']} result rows, {stats['counties']} counties, {stats['years']} years "
        f"(source_file_id={stats['source_file_id']})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
