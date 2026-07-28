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

Define and document the data model before expanding collection.

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

The initial database will use the already installed MySQL server.

Primary outcomes:

- MySQL schema.
- Source-tracking rules.
- Import conventions.
- Validation rules.
- Generated frontend data contracts.

## Phase 2: Pilot Data Collection

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

Quality grades:

- `A`: official structured data, validated.
- `B`: official PDF/report, extracted and reviewed.
- `C`: reputable compiled source, cited.
- `D`: incomplete, unresolved, or known issues.

## Phase 4: Generated App Data

The frontend should consume generated files or API responses, not raw import files.

Initial generated products:

- County presidential summary.
- Statewide contest summary.
- District contest summary.
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

## Immediate Next Steps

1. Create MySQL schema migrations.
2. Create a source registry for the pilot states.
3. Convert the current MIT county presidential import into the new database pipeline.
4. Generate frontend JSON from MySQL instead of directly from raw files.
5. Expand one pilot state through governor, Senate, House, and state legislative results.
