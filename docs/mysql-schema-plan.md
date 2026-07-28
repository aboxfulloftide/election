# MySQL Schema Plan

## Database Role

The installed MySQL server is the system of record for normalized election data.

Raw source files are stored on disk and referenced from MySQL. The frontend consumes generated JSON or API responses created from MySQL.

High-level flow:

```text
source file -> importer -> MySQL normalized tables -> validation -> generated app data -> frontend
```

## Naming Conventions

- Use snake_case table and column names.
- Use surrogate integer primary keys for internal relationships.
- Preserve official identifiers where available.
- Use `created_at` and `updated_at` on durable records.
- Use `source_id` or `source_file_id` on imported factual records.

## Core Tables

### elections

Represents an election event.

Examples:

- `2024 general`
- `2022 general`
- `1970 general`

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
year SMALLINT NOT NULL,
election_date DATE NULL,
election_type ENUM('general', 'runoff') NOT NULL,
name VARCHAR(255) NOT NULL,
notes TEXT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

Unique key:

```sql
(year, election_type, election_date)
```

### jurisdictions

Represents political or administrative places.

Examples:

- United States
- Florida
- Miami-Dade County
- Los Angeles
- Ohio State Senate District 7

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
type ENUM('country', 'state', 'county', 'city', 'district', 'precinct') NOT NULL,
name VARCHAR(255) NOT NULL,
state_po CHAR(2) NULL,
fips VARCHAR(20) NULL,
official_id VARCHAR(100) NULL,
wikidata_id VARCHAR(40) NULL,
parent_jurisdiction_id BIGINT NULL,
valid_from YEAR NULL,
valid_to YEAR NULL,
notes TEXT NULL
```

Important notes:

- District and precinct boundaries change over time.
- `valid_from` and `valid_to` allow multiple historical versions.
- FIPS is useful for states/counties but not enough for districts or precincts.

### offices

Represents the office being elected.

Examples:

- President
- U.S. Senate
- U.S. House
- Governor
- State Senate
- State House
- Mayor

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
name VARCHAR(120) NOT NULL,
level ENUM('federal', 'state', 'local') NOT NULL,
body VARCHAR(120) NULL,
wikidata_id VARCHAR(40) NULL,
districted BOOLEAN NOT NULL DEFAULT FALSE,
executive BOOLEAN NOT NULL DEFAULT FALSE
```

### contests

Represents one race in one election.

Examples:

- `2024 President, United States`
- `2022 Governor, Pennsylvania`
- `2020 U.S. House, TX-07`
- `2018 Ohio State Senate District 7`
- `2025 Mayor, Pittsburgh`

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
election_id BIGINT NOT NULL,
office_id BIGINT NOT NULL,
contest_jurisdiction_id BIGINT NOT NULL,
district_label VARCHAR(100) NULL,
seat_label VARCHAR(100) NULL,
is_special BOOLEAN NOT NULL DEFAULT FALSE,
is_runoff BOOLEAN NOT NULL DEFAULT FALSE,
notes TEXT NULL
```

Important distinction:

- `contest_jurisdiction_id` is the office geography.
- Individual result rows use a separate reporting unit.

### parties

Normalized party names.

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
name VARCHAR(120) NOT NULL,
short_name VARCHAR(40) NOT NULL,
canonical_code VARCHAR(40) NOT NULL,
wikidata_id VARCHAR(40) NULL,
color_hex CHAR(7) NULL
```

Examples:

- `DEMOCRAT`
- `REPUBLICAN`
- `LIBERTARIAN`
- `GREEN`
- `OTHER`
- state-specific minor parties as needed

### candidates

Candidate identity table.

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
display_name VARCHAR(255) NOT NULL,
first_name VARCHAR(120) NULL,
last_name VARCHAR(120) NULL,
normalized_name VARCHAR(255) NOT NULL,
wikidata_id VARCHAR(40) NULL,
notes TEXT NULL
```

Do not assume name alone is globally unique.

### contest_candidates

Links candidates to contests.

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
contest_id BIGINT NOT NULL,
candidate_id BIGINT NOT NULL,
party_id BIGINT NULL,
ballot_label VARCHAR(255) NULL,
incumbent BOOLEAN NULL,
winner BOOLEAN NULL,
source_id BIGINT NULL
```

Unique key:

```sql
(contest_id, candidate_id, party_id)
```

### reporting_units

Represents the geography reporting the vote total.

Examples:

- State total
- County total
- County portion of congressional district
- Precinct
- Citywide total

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
jurisdiction_id BIGINT NOT NULL,
unit_type ENUM('state', 'county', 'county_district', 'district', 'city', 'precinct') NOT NULL,
name VARCHAR(255) NOT NULL,
state_po CHAR(2) NULL,
county_fips VARCHAR(10) NULL,
precinct_code VARCHAR(100) NULL,
district_label VARCHAR(100) NULL,
valid_from YEAR NULL,
valid_to YEAR NULL,
geometry_id BIGINT NULL,
notes TEXT NULL
```

### results

Stores candidate vote totals.

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
contest_id BIGINT NOT NULL,
contest_candidate_id BIGINT NOT NULL,
reporting_unit_id BIGINT NOT NULL,
votes INT NOT NULL,
total_votes INT NULL,
vote_mode VARCHAR(80) NULL,
source_file_id BIGINT NOT NULL,
quality_grade ENUM('A', 'B', 'C', 'D') NOT NULL,
notes TEXT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

Unique key:

```sql
(contest_id, contest_candidate_id, reporting_unit_id, vote_mode, source_file_id)
```

Vote mode examples:

- total
- election_day
- early
- absentee
- provisional

The first pipeline should store total returns. More detailed vote modes can be added later when sources support them cleanly.

## Source Tables

### sources

Represents an institution or compiled dataset.

Examples:

- Florida Department of State
- California Secretary of State
- MIT Election Data and Science Lab
- Harvard Dataverse
- Philadelphia City Commissioners

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
name VARCHAR(255) NOT NULL,
source_type ENUM('official_state', 'official_county', 'official_city', 'compiled_dataset', 'archive', 'other') NOT NULL,
homepage_url TEXT NULL,
discovery_reference_url TEXT NULL,
license_name VARCHAR(255) NULL,
license_url TEXT NULL,
notes TEXT NULL
```

### source_files

Represents an imported file, report, API response, or scanned document.

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
source_id BIGINT NOT NULL,
url TEXT NULL,
local_path TEXT NULL,
discovery_reference_url TEXT NULL,
retrieved_at DATETIME NOT NULL,
file_name VARCHAR(255) NULL,
file_type VARCHAR(80) NULL,
checksum_sha256 CHAR(64) NULL,
covers_year_start SMALLINT NULL,
covers_year_end SMALLINT NULL,
raw_license_text TEXT NULL,
transform_notes TEXT NULL,
quality_grade ENUM('A', 'B', 'C', 'D') NOT NULL
```

Every result row should trace back to a `source_file_id`.

## Geometry Tables

Geometry should be tracked separately from results because boundaries change.

### geometries

Suggested columns:

```sql
id BIGINT PRIMARY KEY AUTO_INCREMENT,
geo_type ENUM('state', 'county', 'district', 'city', 'precinct') NOT NULL,
name VARCHAR(255) NOT NULL,
state_po CHAR(2) NULL,
fips VARCHAR(20) NULL,
official_id VARCHAR(100) NULL,
valid_from YEAR NULL,
valid_to YEAR NULL,
source_file_id BIGINT NULL,
simplified_geojson MEDIUMTEXT NULL,
notes TEXT NULL
```

For large precinct data, do not store every geometry directly in the main results tables. Use separate geometry files or tiles if needed.

## Derived Tables or Views

These can be generated from raw results.

### contest_totals

Possible materialized summary:

```text
contest_id
reporting_unit_id
total_votes
winner_candidate_id
winner_party_id
margin_votes
margin_pct
dem_votes
rep_votes
two_party_margin
source_quality_floor
```

### comparison_metrics

Possible generated table:

```text
office_id
jurisdiction_id
reporting_unit_id
year
compare_year
party_margin
shift_margin
turnout_change
winner_changed
```

## Import Strategy

Imports should be idempotent.

Recommended pattern:

1. Register or update source.
2. Register source file with checksum.
3. Stage raw rows into an import table.
4. Normalize candidates, parties, contests, and reporting units.
5. Insert results.
6. Run validation checks.
7. Generate summaries.

Staging tables can be source-specific, but normalized tables should stay source-agnostic.

## First Migration Target

The first MySQL migration should include:

- `sources`
- `source_files`
- `elections`
- `jurisdictions`
- `offices`
- `contests`
- `parties`
- `candidates`
- `contest_candidates`
- `reporting_units`
- `results`
- `data_quality_notes`

Then convert the current MIT county presidential data importer to load MySQL instead of writing only frontend JSON.
