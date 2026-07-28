#!/usr/bin/env python3
"""Import official Florida statewide general-election precinct results."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

from election_db import ROOT_DIR, connect, fetch_one_id
from fetch_results import parse_int
from florida_precinct_config import (
    DISCOVERY_URL,
    SOURCE_HOMEPAGE,
    SOURCE_NAME,
    FloridaGeneralElection,
    selected_elections,
)


SKIP_BALLOT_ACCOUNTING = {"OverVotes", "UnderVotes", "Times Over Voted", "Number of Under Votes"}
WRITE_IN_NAMES = {"WriteinVotes", "WriteInVotes", "Write-in Votes", "Write-In Votes", "WriteInsCast"}

FLORIDA_COUNTY_FIPS = {
    "ALA": "12001",
    "BAK": "12003",
    "BAY": "12005",
    "BRA": "12007",
    "BRE": "12009",
    "BRO": "12011",
    "CAL": "12013",
    "CHA": "12015",
    "CIT": "12017",
    "CLA": "12019",
    "CLL": "12021",
    "CLM": "12023",
    "DAD": "12086",
    "DES": "12027",
    "DIX": "12029",
    "DUV": "12031",
    "ESC": "12033",
    "FLA": "12035",
    "FRA": "12037",
    "GAD": "12039",
    "GIL": "12041",
    "GLA": "12043",
    "GUL": "12045",
    "HAM": "12047",
    "HAR": "12049",
    "HEN": "12051",
    "HER": "12053",
    "HIG": "12055",
    "HIL": "12057",
    "HOL": "12059",
    "IND": "12061",
    "JAC": "12063",
    "JEF": "12065",
    "LAF": "12067",
    "LAK": "12069",
    "LEE": "12071",
    "LEO": "12073",
    "LEV": "12075",
    "LIB": "12077",
    "MAD": "12079",
    "MAN": "12081",
    "MON": "12087",
    "MRN": "12083",
    "MRT": "12085",
    "NAS": "12089",
    "OKA": "12091",
    "OKE": "12093",
    "ORA": "12095",
    "OSC": "12097",
    "PAL": "12099",
    "PAS": "12101",
    "PIN": "12103",
    "POL": "12105",
    "PUT": "12107",
    "SAN": "12113",
    "SAR": "12115",
    "SEM": "12117",
    "STJ": "12109",
    "STL": "12111",
    "SUM": "12119",
    "SUW": "12121",
    "TAY": "12123",
    "UNI": "12125",
    "VOL": "12127",
    "WAK": "12129",
    "WAL": "12131",
    "WAS": "12133",
}

PARTY_MAP = {
    "DEM": "DEMOCRAT",
    "REP": "REPUBLICAN",
    "LPF": "LIBERTARIAN",
    "GRE": "GREEN",
    "NPA": "NONPARTISAN",
    "": "OTHER",
}


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).upper()


def clean_field(value: str) -> str:
    return value.replace("\x00", "").strip().lstrip("\ufeff")


def get_or_create_source(cursor: Any) -> int:
    source_id = fetch_one_id(cursor, "SELECT id FROM sources WHERE name = %s", (SOURCE_NAME,))
    notes = "Official Florida statewide compiled precinct-level election results."
    if source_id is not None:
        cursor.execute(
            """
            UPDATE sources
            SET source_type = 'official_state',
                homepage_url = %s,
                discovery_reference_url = %s,
                notes = %s
            WHERE id = %s
            """,
            (SOURCE_HOMEPAGE, DISCOVERY_URL, notes, source_id),
        )
        return source_id

    cursor.execute(
        """
        INSERT INTO sources (name, source_type, homepage_url, discovery_reference_url, notes)
        VALUES (%s, 'official_state', %s, %s, %s)
        """,
        (SOURCE_NAME, SOURCE_HOMEPAGE, DISCOVERY_URL, notes),
    )
    return int(cursor.lastrowid)


def get_or_create_source_file(cursor: Any, source_id: int, election: FloridaGeneralElection) -> int:
    file_checksum = checksum(election.zip_path)
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
           checksum_sha256, covers_year_start, covers_year_end, transform_notes, quality_grade)
        VALUES
          (%s, %s, %s, %s, %s, %s, 'application/zip',
           %s, %s, %s, %s, 'A')
        """,
        (
            source_id,
            election.url,
            str(election.zip_path.relative_to(ROOT_DIR)),
            DISCOVERY_URL,
            dt.datetime.now(dt.UTC).replace(tzinfo=None),
            election.zip_path.name,
            file_checksum,
            election.year,
            election.year,
            (
                "Imported configured statewide target contests from official Florida precinct-level "
                "general election ZIP; skipped overvote/undervote accounting rows."
            ),
        ),
    )
    return int(cursor.lastrowid)


def get_or_create_election(cursor: Any, election: FloridaGeneralElection) -> int:
    election_id = fetch_one_id(
        cursor,
        """
        SELECT id FROM elections
        WHERE year = %s AND election_type = 'general' AND election_date = %s
        ORDER BY id LIMIT 1
        """,
        (election.year, election.election_date),
    )
    if election_id is not None:
        return election_id

    cursor.execute(
        """
        INSERT INTO elections (year, election_date, election_type, name, notes)
        VALUES (%s, %s, 'general', %s, 'Official Florida precinct-level general election import.')
        """,
        (election.year, election.election_date, election.election_name),
    )
    return int(cursor.lastrowid)


def id_by_query(cursor: Any, query: str, params: tuple[Any, ...], missing_message: str) -> int:
    value = fetch_one_id(cursor, query, params)
    if value is None:
        raise RuntimeError(missing_message)
    return value


def get_or_create_county(cursor: Any, county_code: str, county_name: str, florida_id: int) -> int:
    fips = FLORIDA_COUNTY_FIPS[county_code]
    county_id = fetch_one_id(
        cursor,
        "SELECT id FROM jurisdictions WHERE type = 'county' AND official_id = %s",
        (fips,),
    )
    if county_id is not None:
        return county_id

    cursor.execute(
        """
        INSERT INTO jurisdictions
          (type, name, state_po, fips, official_id, parent_jurisdiction_id, notes)
        VALUES
          ('county', %s, 'FL', %s, %s, %s, 'Created by Florida precinct importer.')
        """,
        (county_name, fips, fips, florida_id),
    )
    return int(cursor.lastrowid)


def get_or_create_precinct(cursor: Any, row: dict[str, str], county_id: int, year: int) -> int:
    location_hash = hashlib.sha1(row["precinct_name"].encode("utf-8")).hexdigest()[:12]
    official_id = f"FL:{row['county_code']}:{row['election_number']}:{row['precinct_id']}:{location_hash}"
    jurisdiction_id = fetch_one_id(
        cursor,
        "SELECT id FROM jurisdictions WHERE type = 'precinct' AND official_id = %s",
        (official_id,),
    )
    if jurisdiction_id is None:
        cursor.execute(
            """
            INSERT INTO jurisdictions
              (type, name, state_po, official_id, parent_jurisdiction_id, valid_from, valid_to, notes)
            VALUES
              ('precinct', %s, 'FL', %s, %s, %s, %s, %s)
            """,
            (
                row["precinct_name"],
                official_id,
                county_id,
                year,
                year,
                f"Florida precinct {row['precinct_id']} from county code {row['county_code']}.",
            ),
        )
        jurisdiction_id = int(cursor.lastrowid)

    unit_id = fetch_one_id(
        cursor,
        """
        SELECT id FROM reporting_units
        WHERE jurisdiction_id = %s AND unit_type = 'precinct' AND precinct_code = %s
        ORDER BY id LIMIT 1
        """,
        (jurisdiction_id, row["precinct_id"]),
    )
    if unit_id is not None:
        return unit_id

    cursor.execute(
        """
        INSERT INTO reporting_units
          (jurisdiction_id, unit_type, name, state_po, county_fips, precinct_code, valid_from, valid_to, notes)
        VALUES
          (%s, 'precinct', %s, 'FL', %s, %s, %s, %s, 'Official Florida precinct reporting unit.')
        """,
        (jurisdiction_id, row["precinct_name"], FLORIDA_COUNTY_FIPS[row["county_code"]], row["precinct_id"], year, year),
    )
    return int(cursor.lastrowid)


def get_or_create_contest(
    cursor: Any,
    election_id: int,
    office_id: int,
    florida_id: int,
    election: FloridaGeneralElection,
    contest_name: str,
    district_label: str,
) -> int:
    contest_id = fetch_one_id(
        cursor,
        """
        SELECT id FROM contests
        WHERE election_id = %s AND office_id = %s AND contest_jurisdiction_id = %s
          AND district_label <=> %s AND seat_label IS NULL
          AND is_special = FALSE AND is_runoff = FALSE
        ORDER BY id LIMIT 1
        """,
        (election_id, office_id, florida_id, district_label or None),
    )
    if contest_id is not None:
        return contest_id

    cursor.execute(
        """
        INSERT INTO contests
          (election_id, office_id, contest_jurisdiction_id, district_label, notes)
        VALUES
          (%s, %s, %s, %s, %s)
        """,
        (election_id, office_id, florida_id, district_label or None, f"Florida {election.year} {contest_name}."),
    )
    return int(cursor.lastrowid)


def get_party_id(cursor: Any, party_code: str) -> int:
    canonical = PARTY_MAP.get(party_code.strip(), "OTHER")
    return id_by_query(
        cursor,
        "SELECT id FROM parties WHERE canonical_code = %s",
        (canonical,),
        f"Missing party seed {canonical}. Run npm run db:apply first.",
    )


def get_or_create_candidate(cursor: Any, candidate_name: str, party_code: str, official_id: str) -> int:
    display_name = "Write-in votes" if candidate_name in WRITE_IN_NAMES else candidate_name.strip()
    normalized = normalize_name(display_name)
    candidate_id = fetch_one_id(
        cursor,
        """
        SELECT id FROM candidates
        WHERE normalized_name = %s AND display_name = %s
        ORDER BY id LIMIT 1
        """,
        (normalized, display_name),
    )
    if candidate_id is not None:
        return candidate_id

    cursor.execute(
        """
        INSERT INTO candidates (display_name, normalized_name, notes)
        VALUES (%s, %s, %s)
        """,
        (display_name, normalized, f"Florida candidate/issue id {official_id}; party code {party_code}."),
    )
    return int(cursor.lastrowid)


def get_or_create_contest_candidate(cursor: Any, contest_id: int, candidate_id: int, party_id: int, source_id: int) -> int:
    contest_candidate_id = fetch_one_id(
        cursor,
        """
        SELECT id FROM contest_candidates
        WHERE contest_id = %s AND candidate_id = %s AND party_id = %s
        ORDER BY id LIMIT 1
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


def iter_target_rows(election: FloridaGeneralElection) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with zipfile.ZipFile(election.zip_path) as archive:
        for name in archive.namelist():
            if "_Recount" in name or name.endswith("/"):
                continue
            with archive.open(name) as raw_handle:
                text_handle = io.TextIOWrapper(raw_handle, encoding="utf-8", errors="replace", newline="")
                reader = csv.reader(text_handle, delimiter="\t")
                for fields in reader:
                    if len(fields) < 19:
                        continue
                    contest_name = clean_field(fields[11])
                    candidate_name = clean_field(fields[14])
                    if contest_name not in election.target_contests or candidate_name in SKIP_BALLOT_ACCOUNTING:
                        continue
                    county_code = clean_field(fields[0])
                    if county_code not in FLORIDA_COUNTY_FIPS:
                        raise RuntimeError(f"Unknown Florida county code {county_code!r}")
                    rows.append(
                        {
                            "county_code": county_code,
                            "county_name": clean_field(fields[1]),
                            "election_number": clean_field(fields[2]),
                            "election_date": clean_field(fields[3]),
                            "election_name": clean_field(fields[4]),
                            "precinct_id": clean_field(fields[5]),
                            "precinct_name": clean_field(fields[6]),
                            "registered_total": clean_field(fields[7]),
                            "contest_name": contest_name,
                            "district_label": clean_field(fields[12]),
                            "contest_code": clean_field(fields[13]),
                            "candidate_name": candidate_name,
                            "party_code": clean_field(fields[15]),
                            "candidate_fl_id": clean_field(fields[16]),
                            "candidate_number": clean_field(fields[17]),
                            "votes": clean_field(fields[18]),
                        }
                    )
    return aggregate_rows(election, rows)


def aggregate_rows(election: FloridaGeneralElection, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    aggregated: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        display_name = "Write-in votes" if row["candidate_name"] in WRITE_IN_NAMES else row["candidate_name"].strip()
        key = (
            election.target_contests[row["contest_name"]],
            row["district_label"],
            row["county_code"],
            row["county_name"],
            row["election_number"],
            row["election_date"],
            row["election_name"],
            row["precinct_id"],
            row["precinct_name"],
            display_name,
            row["party_code"],
        )
        existing = aggregated.get(key)
        if existing is None:
            aggregated[key] = dict(row)
            continue
        existing["votes"] = str(parse_int(existing["votes"]) + parse_int(row["votes"]))
    return list(aggregated.values())


def import_rows(election: FloridaGeneralElection, rows: list[dict[str, str]]) -> dict[str, int]:
    connection = connect()
    cursor = connection.cursor()

    try:
        source_id = get_or_create_source(cursor)
        source_file_id = get_or_create_source_file(cursor, source_id, election)
        election_id = get_or_create_election(cursor, election)
        florida_id = id_by_query(
            cursor,
            "SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'FL'",
            (),
            "Missing Florida jurisdiction seed. Run npm run db:apply first.",
        )

        cursor.execute(
            """
            DELETE r FROM results r
            JOIN contests c ON c.id = r.contest_id
            JOIN elections e ON e.id = c.election_id
            JOIN offices o ON o.id = c.office_id
            JOIN reporting_units ru ON ru.id = r.reporting_unit_id
            WHERE r.source_file_id = %s
              AND e.year = %s
              AND e.election_type = 'general'
              AND ru.state_po = 'FL'
              AND o.name IN ({})
            """.format(", ".join(["%s"] * len(set(election.target_contests.values())))),
            (source_file_id, election.year, *sorted(set(election.target_contests.values()))),
        )

        office_cache: dict[str, int] = {}
        contest_cache: dict[tuple[str, str], int] = {}
        county_cache: dict[str, int] = {}
        precinct_cache: dict[tuple[str, str, str], int] = {}
        party_cache: dict[str, int] = {}
        candidate_cache: dict[tuple[str, str, str], int] = {}
        contest_candidate_cache: dict[tuple[int, int, int], int] = {}

        imported = 0
        for row in rows:
            office_name = election.target_contests[row["contest_name"]]
            office_id = office_cache.get(office_name)
            if office_id is None:
                office_id = id_by_query(
                    cursor,
                    "SELECT id FROM offices WHERE name = %s",
                    (office_name,),
                    f"Missing office seed: {office_name}",
                )
                office_cache[office_name] = office_id

            contest_key = (office_name, row["district_label"])
            contest_id = contest_cache.get(contest_key)
            if contest_id is None:
                contest_id = get_or_create_contest(
                    cursor,
                    election_id,
                    office_id,
                    florida_id,
                    election,
                    row["contest_name"],
                    row["district_label"],
                )
                contest_cache[contest_key] = contest_id

            county_id = county_cache.get(row["county_code"])
            if county_id is None:
                county_id = get_or_create_county(cursor, row["county_code"], row["county_name"], florida_id)
                county_cache[row["county_code"]] = county_id

            precinct_key = (row["county_code"], row["precinct_id"], row["precinct_name"])
            reporting_unit_id = precinct_cache.get(precinct_key)
            if reporting_unit_id is None:
                reporting_unit_id = get_or_create_precinct(cursor, row, county_id, election.year)
                precinct_cache[precinct_key] = reporting_unit_id

            party_id = party_cache.get(row["party_code"])
            if party_id is None:
                party_id = get_party_id(cursor, row["party_code"])
                party_cache[row["party_code"]] = party_id

            candidate_key = (row["candidate_name"], row["party_code"], row["candidate_number"])
            candidate_id = candidate_cache.get(candidate_key)
            if candidate_id is None:
                candidate_id = get_or_create_candidate(cursor, row["candidate_name"], row["party_code"], row["candidate_number"])
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
                  (%s, %s, %s, %s, NULL, 'total', %s, 'A')
                ON DUPLICATE KEY UPDATE
                  votes = VALUES(votes),
                  quality_grade = VALUES(quality_grade)
                """,
                (
                    contest_id,
                    contest_candidate_id,
                    reporting_unit_id,
                    parse_int(row["votes"]),
                    source_file_id,
                ),
            )
            imported += 1

        connection.commit()
        return {
            "rows": imported,
            "contests": len(contest_cache),
            "counties": len(county_cache),
            "precincts": len(precinct_cache),
            "source_file_id": source_file_id,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def import_election(election: FloridaGeneralElection) -> dict[str, int]:
    if not election.zip_path.exists():
        raise RuntimeError(f"Missing {election.zip_path}. Run npm run florida:download first.")
    rows = iter_target_rows(election)
    return import_rows(election, rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, help="Florida general election year to import. Defaults to 2022.")
    parser.add_argument("--all", action="store_true", help="Import every configured Florida general election.")
    args = parser.parse_args()

    for election in selected_elections(args.year, args.all):
        stats = import_election(election)
        print(
            f"Imported Florida {election.year} general precinct results: "
            f"{stats['rows']} rows, {stats['contests']} contests, {stats['counties']} counties, "
            f"{stats['precincts']} precincts (source_file_id={stats['source_file_id']})."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
