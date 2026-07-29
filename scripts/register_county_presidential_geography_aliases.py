#!/usr/bin/env python3
"""Register known county presidential geography aliases in MySQL."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from election_db import connect, fetch_one_id


@dataclass(frozen=True)
class GeographyAlias:
    state_po: str
    target_fips: str
    alias_type: str
    alias_value: str
    valid_from: int | None
    valid_to: int | None
    notes: str


ALIASES = [
    GeographyAlias(
        state_po="MO",
        target_fips="2938000",
        alias_type="fips",
        alias_value="36000",
        valid_from=2024,
        valid_to=2024,
        notes="MIT 2024 uses FIPS-like code 36000 for the Kansas City, Missouri split row.",
    ),
    GeographyAlias(
        state_po="SD",
        target_fips="46102",
        alias_type="fips",
        alias_value="46113",
        valid_from=2000,
        valid_to=2012,
        notes="Shannon County historical FIPS/name merged into Oglala Lakota County comparison row.",
    ),
    GeographyAlias(
        state_po="SD",
        target_fips="46102",
        alias_type="name",
        alias_value="SHANNON",
        valid_from=2000,
        valid_to=2012,
        notes="Shannon County historical name merged into Oglala Lakota County comparison row.",
    ),
]


def require_alias_table(cursor: Any) -> None:
    cursor.execute("SHOW TABLES LIKE 'jurisdiction_aliases'")
    if cursor.fetchone() is None:
        raise RuntimeError("Missing jurisdiction_aliases table. Run npm run db:apply first.")


def register_alias(cursor: Any, alias: GeographyAlias) -> bool:
    jurisdiction_id = fetch_one_id(
        cursor,
        "SELECT id FROM jurisdictions WHERE state_po = %s AND fips = %s ORDER BY id LIMIT 1",
        (alias.state_po, alias.target_fips),
    )
    if jurisdiction_id is None:
        print(f"Skipping alias {alias.alias_value}: target jurisdiction {alias.state_po} {alias.target_fips} is not imported yet.")
        return False

    cursor.execute(
        """
        INSERT INTO jurisdiction_aliases
          (jurisdiction_id, alias_type, alias_value, valid_from, valid_to, notes)
        VALUES
          (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          jurisdiction_id = VALUES(jurisdiction_id),
          notes = VALUES(notes)
        """,
        (jurisdiction_id, alias.alias_type, alias.alias_value, alias.valid_from, alias.valid_to, alias.notes),
    )
    return cursor.rowcount > 0


def main() -> int:
    connection = connect()
    cursor = connection.cursor()
    try:
        require_alias_table(cursor)
        changed = 0
        for alias in ALIASES:
            changed += int(register_alias(cursor, alias))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

    print(f"Registered {len(ALIASES)} county presidential geography aliases ({changed} inserted or updated).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
