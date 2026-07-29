# Pilot Source Registry

This directory tracks source-discovery work for the five pilot states.

Files:

- [Florida](florida.md)
- [Georgia](georgia.md)
- [Geography normalization](geography-normalization.md)
- [Kentucky](kentucky.md)
- [North Carolina](north-carolina.md)
- [Virginia](virginia.md)
- [Wisconsin](wisconsin.md)
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
- County presidential geography normalization for known renamed, re-coded, or retired comparison rows.
- Georgia Secretary of State official 2020 general-election recount summary ZIP, aggregated to county presidential totals.
- Kentucky State Board of Elections official 2020 certified general-election PDF, parsed to county presidential totals.
- North Carolina State Board of Elections official precinct results ZIPs, aggregated to county presidential totals for 2020 and 2024.
- Virginia Department of Elections official historical CSV downloads, aggregated to locality presidential totals for 2020 and 2024.
- Wisconsin Elections Commission official 2024 county-by-county presidential canvass PDF, parsed to county presidential totals.
- California Secretary of State official 2024 Statement of Vote XLSX files for President, U.S. Senate, U.S. House, State Senate, and State Assembly.
- Tony McGovern's county-level presidential CSVs, used only as a non-authoritative supplement for missing MIT 2020/2024 county rows.
- Florida Division of Elections precinct-level general-election ZIPs, 2012-2024.
- Florida offices: President, U.S. Senate, U.S. House, Governor, State Senate, State House where on ballot.
- Florida Legislature EDR 2022 district geometry rows and generated GeoJSON for congressional, State Senate, and State House layers.

Recommended next import:

- Add frontend access for the California Statement of Vote contests, or import Florida mayor contests for Miami, Jacksonville, Tampa, and Orlando from county/city election archives.
