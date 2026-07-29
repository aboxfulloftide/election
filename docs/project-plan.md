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

Target election data back to the 1950s where obtainable.

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

Local:

- Major city mayor

### Mayor Pilot Cities

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

Next collection targets:

- Florida mayor contests for Miami, Jacksonville, Tampa, and Orlando.
- Florida district and precinct geometry joins.
- California statewide/district Statement of Vote import.

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

- `npm run check` compiles Python scripts, type-checks the frontend, runs DB-free Python unit tests, and validates committed generated JSON structure.
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

Still needed:

- Mayor contest summary.
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

Status: national presidential interface exists with country, state, and county comparison cards. Florida 2022/2024 district map mode exists for U.S. House, State Senate, and State House contests using generated district drilldown bundles and GeoJSON, including winner and 2024-vs-2022 shift modes. The next interface work should deepen drilldown behavior and add precinct-aware views after precinct geometry is sourced.

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

1. Add richer frontend Florida drilldown behavior and identify county/year precinct geometry sources.
2. Add Florida mayor imports for Miami, Jacksonville, Tampa, and Orlando.
3. Add California Statement of Vote import as the second pilot-state structured import.
4. Update the interface to read Florida contest summaries and support contest/year selection beyond presidential county maps.
