# Pilot Source Registry

This directory tracks source-discovery work for the five pilot states.

Files:

- [Florida](florida.md)
- [California](california.md)
- [Pennsylvania](pennsylvania.md)
- [Texas](texas.md)
- [Ohio](ohio.md)

## Rules

- Treat official state, county, and city election offices as primary sources.
- Treat Princeton, Wikipedia, Wikidata, Ballotpedia, news, and library guides as discovery or context unless no better source exists.
- Record the actual imported source file URL, retrieval date, checksum, format, coverage, and transformation notes in MySQL.
- Prefer precinct-level files when official and clean.
- Fall back to county-by-district, district totals, county totals, statewide totals, or citywide totals as needed.

## Current Import Status

Status: complete for the first Florida official precinct import.

Implemented imports:

- MIT county presidential returns, 2000-2024.
- Florida Division of Elections precinct-level general-election ZIPs, 2012-2024.
- Florida offices: President, U.S. Senate, U.S. House, Governor, State Senate, State House where on ballot.

Recommended next import:

- Florida mayor contests for Miami, Jacksonville, Tampa, and Orlando from county/city election archives, or California Statement of Vote files as the next state-level structured import.
