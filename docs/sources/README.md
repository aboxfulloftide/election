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

## First Import Recommendation

After the MIT presidential backbone, the next import should be **Florida statewide general-election returns from the Florida Division of Elections archive**, starting with governor and U.S. Senate. Florida has an official archive back to 1978, and its state office explicitly points local/municipal results to county supervisors, which matches our source model.

