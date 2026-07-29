# Data

`npm run data:fetch` downloads the current Harvard Dataverse files into `data/raw/`, imports normalized MIT presidential results into MySQL, validates them, applies configured official state overrides, fills remaining missing 2020/2024 county rows from the configured supplemental CSV source, and writes the frontend-ready files to:

```text
public/results/county-presidential-summary.json
public/results/county-presidential-coverage.json
```

Raw downloads are ignored by git. The generated summary is small enough to commit so the app can run immediately after `npm install`.

Use lower-level commands when debugging the pipeline:

```bash
npm run data:download
npm run data:import
npm run data:generate
npm run data:normalize
npm run data:geography-aliases
npm run data:coverage
npm run data:official:ga
npm run data:official:ky
npm run data:official:nc
npm run data:official:va
npm run data:official:wi
npm run data:supplement
```

Official state overrides run before the supplemental fallback. Georgia currently uses the official Secretary of State 2020 general-election recount summary ZIP, aggregated to county presidential totals and marked with `official: true`, `source_name`, `source_url`, and `quality_grade: "A"`. Georgia's site can block scripted downloads; place `november_3_2020_-_general_election_recount.zip` in the project root or `data/raw/official/georgia/` before running `npm run data:official:ga`. Kentucky currently uses the official State Board of Elections 2020 certified general-election PDF, parsed to county presidential totals and marked with quality grade `B` because the source is an official PDF rather than structured data. North Carolina currently uses official NCSBE precinct results ZIPs for 2020 and 2024, aggregated to county presidential totals and marked with quality grade `A`. Virginia currently uses official Department of Elections historical CSV downloads for 2020 and 2024, aggregated to locality presidential totals and marked with quality grade `A`. Wisconsin currently uses the official Elections Commission 2024 county-by-county canvass PDF, parsed to county presidential totals and marked with quality grade `B`.

The MIT source has incomplete state/year coverage for the current county presidential summary. `npm run data:supplement` downloads Tony McGovern's `US_County_Level_Election_Results_08-24` 2020/2024 CSVs and fills only missing county/year rows. Supplemental rows are marked with `supplemental: true`, `source_name`, `source_url`, and a lower `quality_grade`.

The geography normalizer merges known renamed/superseded rows after the MIT summary is generated. It currently merges Kansas City, Missouri's 2024 alias row into the existing Kansas City comparison row, merges historical Shannon County rows into Oglala Lakota County, and marks retired Bedford City, Virginia inactive after 2012. The coverage report is derived from the committed summary, excludes rows that are inactive for the report year, and records county coverage by year and missing counties by state. `npm run check:json` validates that this report is current.

Florida pilot data is rebuilt with:

```bash
npm run florida:fetch
```

It downloads official Florida Division of Elections precinct-level ZIPs into `data/raw/`, imports normalized results into MySQL, validates them, and writes:

```text
public/results/florida-2012-statewide-summary.json
public/results/florida-2014-statewide-summary.json
public/results/florida-2016-statewide-summary.json
public/results/florida-2018-statewide-summary.json
public/results/florida-2020-statewide-summary.json
public/results/florida-2022-statewide-summary.json
public/results/florida-2024-statewide-summary.json
public/results/florida-statewide-summary.json
```

Raw downloads are ignored by git. Generated summaries are committed.

Florida district geometry outputs are rebuilt with:

```bash
npm run florida:geometry:fetch
```

It downloads official Florida Legislature EDR 2022 congressional, State Senate, and State House shapefile ZIPs plus block-equivalency TXT files into `data/raw/`, registers source files and map layers in MySQL, validates the registrations, and writes:

```text
public/results/florida-geometry-layers.json
public/results/geometry/fl-2022-congressional-districts.geojson
public/results/geometry/fl-2022-state-senate-districts.geojson
public/results/geometry/fl-2022-state-house-districts.geojson
```

The raw geometry files are ignored by git. The generated layer manifest is committed.

Generated JSON contracts can be checked without rebuilding MySQL:

```bash
npm run check:json
npm run check:official
```

`npm run check:official` re-parses configured official county presidential source files and verifies that the generated JSON rows marked official still match those source totals.

Florida district/county drilldown bundles are generated from the committed Florida summaries and geometry manifest:

```bash
npm run florida:districts:generate
```

It writes:

```text
public/results/districts/florida-2022-district-drilldown.json
public/results/districts/florida-2024-district-drilldown.json
public/results/districts/florida-district-drilldown.json
```

California 2024 Statement of Vote summaries are rebuilt with:

```bash
npm run california:fetch
```

It downloads official California Secretary of State 2024 Statement of Vote XLSX files for President, U.S. Senate, U.S. House, State Senate, and State Assembly, then writes:

```text
public/results/california-statewide-summary.json
```

The statewide President and U.S. Senate contests include all 58 counties. The U.S. House, State Senate, and State Assembly contests are parsed from official district workbook blocks and include the counties reporting within each district.
