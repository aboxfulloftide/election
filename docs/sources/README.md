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
- California Secretary of State official 2018, 2020, 2022, and 2024 Statement of Vote spreadsheet files for statewide and district contests.
- California Citizens Redistricting Commission official 2020 final map shapefiles for congressional, State Senate, and State Assembly district geometry.
- Pennsylvania Department of State official 2020, 2022, and 2024 general-election precinct return files.
- Ohio Secretary of State official 2020, 2022, and 2024 statewide results-by-county XLSX workbooks.
- Florida county Supervisor of Elections official municipal mayor summaries from Election Night Reporting pages for Miami-Dade cities, Tampa, Jacksonville, and Orlando.
- Texas Secretary of State official 2018 static historical race/county canvass pages.
- Texas Secretary of State official 2020, 2022, and 2024 County by County Canvass PDF district contests.
- City of Fort Worth City Secretary official election-history page for mayor contests.
- City of San Antonio and Bexar County official historical results for San Antonio mayor contests from 2005 through 2025.
- City of Houston City Secretary official combined canvass PDFs for Houston 1999, 2001, 2003, 2005, and 2007 mayor contests.
- Harris County Clerk official cumulative result PDFs for Houston 2009, 2011, 2013, 2015, 2019, and 2023 mayor contests.
- City of Austin City Clerk official canvass resolutions for Austin 2022 and 2024 mayor contests.
- City of Dallas City Secretary official master list and canvass resolutions for Dallas 1981 through 1999, 2002, 2007, 2011, 2015, 2019, and 2023 mayor contests.
- Texas Secretary of State current public HTML for statewide-only 2026 primary runoff contest totals.
- Tony McGovern's county-level presidential CSVs, used only as a non-authoritative supplement for missing MIT 2020/2024 county rows.
- Florida Division of Elections precinct-level general-election ZIPs, 2012-2024.
- Florida offices: President, U.S. Senate, U.S. House, Governor, State Senate, State House where on ballot.
- Florida Legislature EDR 2022 district geometry rows and generated GeoJSON for congressional, State Senate, and State House layers.

Recommended next import:

- Continue Texas major-city mayor archives beyond Austin/Dallas/Fort Worth/San Antonio/Houston, starting with remaining Houston years and older San Antonio years where official structured archives are available.
