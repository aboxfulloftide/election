# Election Night Map Project Plan

## Goal

Build an election-night map and data system for comparing historical U.S. election results with a broadcast-style interface similar to CNN, Fox News, NBC, and other decision-desk products.

The project has two major tracks:

1. Data collection, normalization, validation, and storage.
2. Interface and visualization built from stable generated data products.

Data comes first. The interface should not depend on raw election files or one-off transformations.

## Initial Scope

### Pilot States

- Florida
- California
- Pennsylvania
- Texas
- Ohio

### Years

Active national target: even-year general elections from 2000 through 2026. Older elections are future archival work, not part of the current completion target.

The practical expectation is uneven coverage by office, state, and geography. The database should preserve that uncertainty instead of pretending all years are equally complete.

### Election Type

General elections only.

Runoffs are included only where the runoff determines the winner of a normally scheduled election.

### Offices

Federal:

- President
- U.S. Senate
- U.S. House

State:

- Governor
- State Senate
- State House / Assembly

Active scope excludes local offices. Existing mayor outputs are retained as archived artifacts only.

### Archived Mayor Pilot Cities

Florida:

- Miami
- Jacksonville
- Tampa
- Orlando

California:

- Los Angeles
- San Francisco
- San Diego
- San Jose
- Sacramento

Pennsylvania:

- Philadelphia
- Pittsburgh

Texas:

- Houston
- Dallas
- Austin
- San Antonio
- Fort Worth

Ohio:

- Columbus
- Cleveland
- Cincinnati
- Toledo

## Geography Rule

Store the most detailed clean reporting level available.

Priority order:

1. Precinct-level returns.
2. County-by-district returns.
3. District totals.
4. Statewide or citywide totals where appropriate.

The database must distinguish between contest geography and reporting geography.

Example:

- Contest geography: `OH State Senate District 7`
- Reporting geography: `Cuyahoga County precinct 14-B`

This lets the project store precinct results when available while still supporting complete district-level results when detailed data is unavailable.

## Phase 1: Data Foundation

Status: implemented for the initial normalized data model.

The current MySQL schema is applied by `npm run db:apply` and includes the normalized tables listed below. It is the system of record for imported results.

Core concepts:

- Election
- Contest
- Candidate
- Party
- Jurisdiction
- Reporting unit
- Result
- Source
- Source file
- Data quality note

The project uses the already installed MySQL server.

Completed outcomes:

- MySQL schema in `db/migrations/001_initial_schema.sql`.
- Geometry layer/source metadata schema in `db/migrations/002_geometry_tables.sql`.
- Seed data in `db/seeds/001_core_reference.sql`.
- Source-tracking rules in the schema and docs.
- Repeatable import conventions in the MIT and Florida pipelines.
- Validation scripts for imported datasets.
- Fast DB-free checks for parser helpers, geometry validation helpers, TypeScript type-checking, Python compilation, and generated JSON contracts.
- Generated frontend JSON files under `public/results/`.

## Phase 2: Pilot Data Collection

Status: partially implemented.

Completed:

- MIT county presidential general-election returns from 2000 through 2024.
- Florida official precinct-level general-election returns from 2012 through 2024 for President, U.S. Senate, U.S. House, Governor, State Senate, and State House where on ballot.
- Florida 2022 congressional, State Senate, and State House district geometry from official EDR shapefile/block-equivalency files.
- Florida official municipal mayor summaries from Election Night Reporting pages for Miami-Dade cities, Tampa, Jacksonville, and Orlando.
- California 2018, 2020, 2022, and 2024 Statement of Vote summaries for statewide and district contests.
- California 2022 congressional, State Senate, and State Assembly district geometry from official CRC final map shapefiles.
- Pennsylvania official 2020, 2022, and 2024 general-election precinct returns aggregated to statewide and county-by-district contest summaries.
- Ohio official 2020, 2022, and 2024 statewide results-by-county workbooks aggregated to statewide and county-by-district contest summaries.
- Texas 2018 official Secretary of State historical race/county canvass summaries.
- Texas Fort Worth official mayor summaries from the City Secretary election-history page.
- Texas San Antonio mayor summaries from 2005 through 2025 from City canvass PDFs and Bexar County official historical results.
- Texas Houston 1999, 2001, 2003, 2005, and 2007 mayor summaries from City Secretary combined canvass PDFs, plus 2009, 2011, 2013, 2015, 2019, and 2023 mayor summaries from Harris County official cumulative result PDFs.
- Texas Austin 2022 and 2024 mayor summaries from City Clerk official canvass resolution PDFs.
- Texas Dallas 1981 through 1999, 2002, 2007, 2011, 2015, 2019, and 2023 mayor summaries from the City Secretary official master list and canvass resolution PDFs.
- Texas 2026 primary runoff statewide-only summaries from SOS current public HTML.

Next collection targets:

- Backfill additional mayor years from structured official archives.
- Florida and California precinct geometry/results where county-by-district detail is not enough.
- Texas 2020/2022/2024 County by County Canvass PDF statewide and district contests are imported. Texas 2025-current public HTML is imported for statewide-only current totals.

Collect pilot-state data for the scoped offices and years.

Preferred source order:

1. Official state election archives.
2. Official county/city election offices.
3. State legislative archives and official canvass reports.
4. MIT Election Data and Science Lab, Harvard Dataverse, ICPSR, OpenElections, and similar compiled datasets.
5. Historical PDFs or scanned reports when structured data is unavailable.

Each imported batch must attach source metadata and quality notes.

Reference guides such as Princeton University Library's elections guide can be used for source discovery, but the database should cite the actual source file or institution used for each imported result batch.

Wikipedia and Wikidata can also be used for source discovery, aliases, and identifiers. Wikipedia is especially useful for finding official state result archive links and understanding format problems in historical election data. It should not be treated as the primary certified vote source when official or archival result files are available.

## Phase 3: Validation

Every import should be checked for:

- Required fields.
- Valid state, year, office, and election type.
- Valid geography identifiers where available.
- Duplicate result rows.
- Candidate and party normalization.
- Vote total reconciliation where possible.
- Winner and margin calculation.
- Source attached to every result.
- Data quality grade assigned.

Fast local checks:

- `npm run check` compiles Python scripts, type-checks the frontend, runs DB-free Python unit tests, validates committed generated JSON structure, compares official county sources, and checks Virginia and Kentucky statewide contest arithmetic and source coverage.
- MySQL-backed import validators remain separate because they require local database credentials and downloaded raw files.

Quality grades:

- `A`: official structured data, validated.
- `B`: official PDF/report, extracted and reviewed.
- `C`: reputable compiled source, cited.
- `D`: incomplete, unresolved, or known issues.

## Phase 4: Generated App Data

The frontend should consume generated files or API responses, not raw import files.

Implemented generated products:

- County presidential summary: `public/results/county-presidential-summary.json`.
- Florida year summaries: `public/results/florida-{year}-statewide-summary.json`.
- Florida combined summary: `public/results/florida-statewide-summary.json`.
- Florida geometry layer manifest: `public/results/florida-geometry-layers.json`.
- Florida district GeoJSON files: `public/results/geometry/fl-2022-*.geojson`.
- Florida 2022 and 2024 district contest summaries linked to geometry layer keys and geometry IDs.
- Florida district/county drilldown bundles: `public/results/districts/florida-*.json`.
- Florida precinct geometry pilot: `public/results/florida-precinct-geometry-layers.json` and Miami-Dade GeoJSON layers under `public/results/geometry/`.
- Florida Miami-Dade precinct result bundles: `public/results/precincts/florida-miami-dade-{year}-precincts.json` for 2012 and 2014.
- Florida Broward precinct result bundles: 2020 and 2024 join completely to official geometry; `florida-broward-2022-precincts.json` preserves a documented numeric/lettered namespace mismatch.
- Florida mayor summary: `public/results/florida-mayor-summary.json`.
- California combined summary: `public/results/california-statewide-summary.json`.
- Pennsylvania combined summary: `public/results/pennsylvania-statewide-summary.json`.
- Ohio combined summary: `public/results/ohio-statewide-summary.json`.
- Texas statewide summary: `public/results/texas-statewide-summary.json`.
- Texas mayor summary: `public/results/texas-mayor-summary.json`.
- California geometry layer manifest: `public/results/california-geometry-layers.json`.
- California district GeoJSON files: `public/results/geometry/ca-2022-*.geojson`.
- California district/county drilldown bundle: `public/results/districts/california-district-drilldown.json`.

Still needed:

- Source index.
- Data quality index.

Later generated products:

- Precinct tiles or partitioned precinct results.
- Historical swing rankings.
- Closest race rankings.
- State drilldown bundles.
- Timeline/playback bundles.

## Phase 5: Interface

The first serious interface should be a decision-desk map, not a landing page.

Status: national presidential interface exists with country, state, and county comparison cards. Official-state mode supports Florida and California. Florida 2022/2024 district map mode and California 2022/2024 district map mode exist for geometry-linked district contests. Florida 2012/2014 Miami-Dade precinct mode now renders official precinct geometry and candidate totals with contest selection and click/hover details.

Core views:

- National map.
- State drilldown.
- Office selector.
- Year selector.
- Contest selector.
- Winner coloring.
- Margin coloring.
- Swing coloring.
- County/district/precinct detail panel.
- Closest races panel.
- Source and data-quality indicator.

Supported map modes:

- County map.
- Congressional district map.
- State legislative district map.
- City mayor map.
- Precinct map where data is clean.

## Phase 6: Expansion

After the pilot is working:

- Add more states.
- Add more mayor cities.
- Add special elections.
- Add primaries if needed.
- Add live or simulated election-night reporting.
- Add scanned PDF extraction workflows.
- Add richer historical commentary and annotations.

## Current Next Steps

Use [handoff.md](handoff.md) as the current next-step script.

Current recommended order:

1. Process the first ten-state 2020-2024 federal/state cohort from `docs/national-backfill-plan.md`.
2. Process the remaining four state cohorts for 2020-2024 before starting older waves.
3. Regenerate `public/results/national-coverage-matrix.json` after every batch and require source, parser, tests, and quality status for each imported cell.
4. Backfill 2010-2018, then 2000-2008, with 2026 general results added after certification.
