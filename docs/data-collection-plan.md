# Data Collection Plan

## Scope

Pilot states:

- Florida
- California
- Pennsylvania
- Texas
- Ohio

Election type:

- General elections only.
- Normal scheduled mayor elections only.
- Runoffs only when they determine the winner.

Years:

- Target back to the 1950s where obtainable.

Offices:

- President
- U.S. Senate
- U.S. House
- Governor
- State Senate
- State House / Assembly
- Major city mayor

## Collection Principles

1. Prefer official sources.
2. Preserve every source citation.
3. Store the most detailed clean geography available.
4. Keep raw files separate from normalized data.
5. Make every import repeatable.
6. Record quality and completeness honestly.

## Source Priority

Use this priority order:

1. Official state election archive or Secretary of State.
2. Official county election office.
3. Official city election office.
4. Official legislative or state archive reports.
5. MIT Election Data and Science Lab, Harvard Dataverse, ICPSR, OpenElections, or other reputable compiled datasets.
6. Historical PDFs or scans when structured sources are unavailable.

Compiled datasets are useful, but should not erase original source attribution when that attribution is available.

## Source Discovery References

Reference guides and library indexes are useful for finding sources, but they are not enough by themselves for imported result rows. Use them to discover official archives, compiled datasets, GIS layers, and historical collections, then cite the actual source file or source institution used by the importer.

Pilot-state source discovery notes live in `docs/sources/`.

Initial discovery references:

- Princeton University Library, Elections and Voting Data Guide: `https://libguides.princeton.edu/elections`
- Wikipedia, List of United States official election results by state: `https://en.wikipedia.org/wiki/List_of_United_States_official_election_results_by_state`
- Wikidata election items for cross-links, identifiers, and alternate labels: `https://www.wikidata.org`
- MIT Election Data and Science Lab data catalog: `https://electionlab.mit.edu/data`
- Harvard Dataverse election-related datasets: `https://dataverse.harvard.edu`
- National Association of Secretaries of State state election office index: `https://www.nass.org`
- Duke Libraries election data guide: `https://blogs.library.duke.edu/data/2022/08/31/election-data/`

The source registry should record a discovery reference when it led to a dataset, but every imported file still needs its own source URL, retrieval date, checksum, license or terms note, and transformation notes.

Wikipedia and Wikidata usage rules:

- Use Wikipedia pages to discover official result archives, historical source names, and known data-format problems.
- Use Wikidata to help normalize public identifiers and aliases for elections, candidates, parties, offices, and jurisdictions.
- Do not treat Wikipedia table values as certified vote totals unless no better source exists and the row is explicitly quality-graded as compiled/reference data.
- When Wikipedia points to an official state, county, city, FEC, archive, or canvass source, cite and import from the linked source instead of citing Wikipedia as the vote source.

## Geography Priority

For each contest, collect the most detailed level that is clean and documented.

Priority:

1. Precinct.
2. County-by-district.
3. District total.
4. County total.
5. Statewide or citywide total.

Examples:

- President can often be county-level historically and precinct-level in newer years.
- U.S. House should ideally be county-by-district or precinct-level, because district totals alone cannot support county maps.
- State legislative races will often start as district totals, with precinct data added for newer years.
- Mayor races may be citywide totals historically and precinct/ward totals for newer elections.

## Pilot Collection Order

### Step 1: Existing Presidential Backbone

Status: complete for the current MIT 2000-2024 county presidential file, with official Georgia, Kentucky, North Carolina, Virginia, and Wisconsin state-source overrides, geography normalization for known renamed/re-coded rows, and a non-authoritative supplemental fill for remaining missing 2020/2024 county rows.

Current source:

- MIT Election Data and Science Lab, County Presidential Election Returns 2000-2024.
- Harvard Dataverse DOI: `10.7910/DVN/VOQCHQ`
- Georgia Secretary of State official 2020 general-election recount summary ZIP.
- Kentucky State Board of Elections official 2020 certified general-election PDF.
- North Carolina State Board of Elections official precinct results ZIPs for 2020 and 2024.
- Virginia Department of Elections official historical election CSV downloads for 2020 and 2024.
- Wisconsin Elections Commission official 2024 county-by-county presidential canvass PDF.
- Tony McGovern's `US_County_Level_Election_Results_08-24` GitHub CSVs for missing 2020/2024 rows only.

Implemented:

- `npm run data:fetch`
- MySQL import with source metadata and checksums.
- Validation for row counts, years, counties, missing source files, and duplicate keys.
- Official source comparison checks re-parse configured official county presidential source files and compare them against generated JSON rows.
- Generated `public/results/county-presidential-summary.json`.
- Generated `public/results/county-presidential-coverage.json`.
- Known geography aliases are normalized after generation: Kansas City, Missouri's 2024 alias code is merged into the existing Kansas City comparison row; historical Shannon County rows are merged into Oglala Lakota County; retired Bedford City is marked inactive after 2012 for coverage purposes.
- Georgia official rows are imported from the recount summary ZIP, replace fallback rows for 2020, and are marked in JSON with `official: true`, source metadata, and quality grade `A`.
- Kentucky official rows are parsed from the certified PDF, replace fallback rows for 2020, and are marked in JSON with `official: true`, source metadata, and quality grade `B`.
- North Carolina official rows are aggregated from precinct files, replace fallback rows, and are marked in JSON with `official: true`, source metadata, and quality grade `A`.
- Virginia official rows are imported from locality CSV downloads, replace fallback rows, and are marked in JSON with `official: true`, source metadata, and quality grade `A`.
- Wisconsin official rows are parsed from the county-by-county presidential canvass PDF, replace fallback rows for 2024, and are marked in JSON with `official: true`, source metadata, and quality grade `B`.
- Supplemental rows are marked in JSON with `supplemental: true`, source metadata, and lower quality grade.

Next work:

- Add older county presidential sources before 2000 where obtainable.
- Add source comparison checks against official state canvass totals when practical.
- Move one-off geography aliases into normalized MySQL jurisdiction history tables instead of applying them only in generated JSON.

### Step 2: Florida Official Precinct Baseline

Status: complete for configured 2012-2024 general-election files and scoped federal/state offices.

Current source:

- Florida Division of Elections precinct-level general-election ZIPs.
- Configured years: 2012, 2014, 2016, 2018, 2020, 2022, 2024.
- Configured offices where on ballot: President, U.S. Senate, U.S. House, Governor, State Senate, State House.

Current outputs:

- Normalized MySQL precinct/polling-location results with official source-file rows and checksums.
- `public/results/florida-{year}-statewide-summary.json`
- `public/results/florida-statewide-summary.json`
- Florida 2022 district geometry rows in MySQL, `public/results/florida-geometry-layers.json`, and district GeoJSON files under `public/results/geometry/`.
- Geometry links embedded in 2022 and 2024 Florida U.S. House, State Senate, and State House contest summaries.
- District/county drilldown bundles for 2022 and 2024 under `public/results/districts/`.
- Validation currently covers 672,309 normalized result rows, 922 contests, all 67 counties for every configured year, and zero duplicate result keys.

Next work:

- Add county/year official Florida precinct geometry sources.
- Add Florida mayor contests from county/city archives.
- Add frontend access for California Statement of Vote contests.
- Add California county or precinct geometry sources for district-aware maps.

### Step 3: Other Pilot-State Governor and U.S. Senate

Collect by pilot state.

Priority:

1. Official statewide returns.
2. County-level returns.
3. Historical official canvass PDFs.

Target outputs:

- Statewide contest total.
- County-level candidate totals where available.
- Source quality grade.

### Step 4: Other Pilot-State U.S. House

Collect district races.

Priority:

1. Precinct-level returns by district.
2. County-by-district results.
3. District totals.

Important issue:

Congressional district boundaries change after redistricting. Data must be tied to the district label and year, not a permanent district geometry assumption.

### Step 5: Other Pilot-State State Senate and State House

Collect district races.

Priority:

1. Official state legislative returns.
2. County-by-district breakdowns.
3. District totals.
4. Precinct files for newer years where practical.

Important issue:

State legislative district names, numbers, and boundaries vary by state and decade. Historical district records should be versioned by year range.

### Step 6: Major City Mayor

Pilot cities:

- Miami
- Jacksonville
- Tampa
- Orlando
- Los Angeles
- San Francisco
- San Diego
- San Jose
- Sacramento
- Philadelphia
- Pittsburgh
- Houston
- Dallas
- Austin
- San Antonio
- Fort Worth
- Columbus
- Cleveland
- Cincinnati
- Toledo

Priority:

1. Official city election office.
2. County election office if the county administers city elections.
3. City archive reports.
4. Historical PDFs or scans.

Mayor data should preserve city-specific election rules, including nonpartisan races and runoffs.

## Source Registry Fields

Each source should record:

- Source name.
- Source type.
- Discovery reference, if a guide or index led to the source.
- Homepage URL.
- Specific file/report/API URL.
- Retrieval date.
- License or terms if known.
- Coverage years.
- Covered offices.
- Covered geography.
- Local raw file path.
- File checksum.
- Transformation notes.
- Quality grade.

## Data Quality Grades

Use grades consistently:

- `A`: official structured data, validated.
- `B`: official PDF/report, extracted and reviewed.
- `C`: reputable compiled source, cited.
- `D`: incomplete, unresolved, or known issues.

Quality is per source file or import batch, not just per institution.

Example:

- A modern official CSV can be `A`.
- A scanned official canvass book may be `B`.
- A compiled historical dataset may be `C`.
- A partial file with missing counties may be `D`.

## Validation Checks

Required checks:

- Year is within expected range.
- Election type is general or qualifying runoff.
- Office is in scope.
- State is one of the pilot states unless importing national presidential context.
- Candidate names are present.
- Vote totals are numeric.
- Reporting unit is identified.
- Source file is attached.
- Duplicate result rows are detected.
- Winners and margins can be calculated where totals are complete.

Recommended checks:

- Candidate totals sum to official total where available.
- County totals sum to statewide totals where available.
- District totals sum from county/precinct pieces where available.
- Party labels normalize consistently.
- Uncontested races are marked explicitly.
- Nonpartisan mayor races do not force a party label.

## Known Hard Problems

Historical data back to the 1950s will not be uniform.

Expected issues:

- Scanned PDFs and canvass books.
- Missing precinct identifiers.
- Redistricting boundary changes.
- State legislative district renumbering.
- Uncontested races with no vote totals or write-in-only reporting.
- Fusion voting and minor party labels.
- Nonpartisan mayor races.
- City election rules that differ from state general-election calendars.

The database should store notes and quality flags instead of hiding these issues.

## Completed First Data Milestone

Status: complete.

Completed:

1. Registered MIT/Harvard Dataverse as a source.
2. Registered source files with local paths and checksums.
3. Imported 2000-2024 county presidential returns into MySQL.
4. Validated row counts, years, counties, source files, and duplicate keys.
5. Generated the current frontend JSON from MySQL.
6. Expanded Florida across President, U.S. Senate, U.S. House, Governor, State Senate, and State House at official precinct/polling-location level for 2012-2024.

Next milestone:

Expose the imported California Statement of Vote contests in the frontend, then continue with either Florida mayor contests or California geometry/back-year expansion.
