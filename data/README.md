# Data

`npm run data:fetch` downloads the current Harvard Dataverse files into `data/raw/`, imports normalized MIT presidential results into MySQL, validates them, applies configured official state overrides, fills remaining missing 2020/2024 county rows from the configured supplemental CSV source, and writes the frontend-ready files to:

```text
public/results/county-presidential-summary.json
public/results/county-presidential-coverage.json
```

Raw downloads are ignored by git. The generated summary is small enough to commit so the app can run immediately after `npm install`.

National federal/state backfill planning is tracked in `public/results/national-coverage-matrix.json` and `docs/national-coverage-report.md`, generated with `npm run coverage:national`. The matrix covers all 50 states, 2000-2026 even-year general elections, and President, U.S. Senate, U.S. House, Governor, State Senate, and State House/Assembly. Municipal files are archived separately and are not part of this target.

Install Python parser dependencies before rebuilding legacy Excel sources:

```bash
python3 -m pip install -r requirements.txt
```

Texas mayor generation caches downloaded source files and extracted PDF/OCR text under ignored `data/raw/official/texas/mayors/`. The first run on a fresh machine may take a few minutes because scanned Dallas 2011 canvass resolutions require `ocrmypdf` and Tesseract; warm-cache runs should complete quickly. Delete that cache directory to force a clean source re-download and text extraction.

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

The first official precinct-geometry pilot is rebuilt with:

```bash
npm run florida:precinct:geometry
```

It converts Miami-Dade County's official 2012 and 2014/2015 precinct shapefile vintages from Florida State Plane feet to WGS84, merges split polygons by precinct, and writes `public/results/florida-precinct-geometry-layers.json` plus GeoJSON layers under `public/results/geometry/`. The pilot is ready for joining to the existing Florida precinct result identifiers; additional counties and vintages remain to be added.

Broward County's official ArcGIS precinct layers are rebuilt with:

```bash
npm run florida:precinct:geometry:arcgis
```

This imports the official Broward 2020, 2022, and 2024 precinct layers, normalizes them to WGS84 GeoJSON, and appends them to the shared geometry manifest. Broward 2020 and 2024 are joined to normalized results and are available in the official Florida UI. Broward 2022 results are also bundled, but all 355 result IDs remain unmatched because the result file uses numeric IDs while the available boundary layer uses lettered IDs.

The frontend bundle catalog is rebuilt with:

```bash
npm run florida:precinct:catalog
```

It discovers generated county/year bundles and marks only bundles with validated geometry matches as `map_ready`; audit-only bundles remain in the catalog but are not selectable on the map.

Join quality can be audited with:

```bash
npm run florida:precinct:preflight
```

Use `python3 scripts/check_florida_precinct_join.py --all --require-complete` when a pipeline requires every result precinct to have geometry. The geometry manifest also records GeoJSON payload sizes for future delivery decisions.

The complete state/federal precinct rebuild is:

```bash
npm run florida:precinct:all
```

It regenerates both geometry families, all current Miami-Dade/Broward bundles, the catalog, and `public/results/florida-precinct-join-report.json`.

Miami-Dade precinct result bundles are rebuilt with:

```bash
npm run florida:precinct:results -- 2012
npm run florida:precinct:results -- 2014
```

They write `public/results/precincts/florida-miami-dade-{year}-precincts.json` with contest, candidate, precinct, winner, and margin data. Legacy and split precinct identifiers are normalized, and unmatched historical geometry IDs remain represented for auditability. Each bundle records result precinct count, matched geometry count, and unmatched result-ID count. The official Florida UI loads these bundles for 2012 and 2014 and joins them to the generated GeoJSON layers for interactive Miami-Dade precinct maps.

Florida municipal mayor summaries are rebuilt with:

```bash
npm run florida:mayors:generate
```

It parses official county Supervisor of Elections Election Night Reporting summary pages for configured municipal elections, keeps mayor contests only, excludes referendum-style Yes/No questions that mention mayor terms, and writes:

```text
public/results/florida-mayor-summary.json
```

California Statement of Vote summaries are rebuilt with:

```bash
npm run california:fetch
```

It downloads official California Secretary of State 2018, 2020, 2022, and 2024 Statement of Vote spreadsheet files for statewide and district contests, then writes:

```text
public/results/california-statewide-summary.json
```

Statewide contests include all 58 counties. U.S. House, State Senate, and State Assembly contests are parsed from official district workbook blocks and include the counties reporting within each district. The 2020 district contests use pre-2022 district boundaries, so they are included in the statewide summary but not in the 2022-cycle geometry-linked district drilldown.

California district geometry and district/county drilldown outputs are rebuilt with:

```bash
npm run california:geometry:fetch
npm run california:districts:generate
```

`npm run california:geometry:fetch` downloads official 2020 California Citizens Redistricting Commission final map shapefiles and writes:

```text
public/results/california-geometry-layers.json
public/results/geometry/ca-2022-congressional-districts.geojson
public/results/geometry/ca-2022-state-senate-districts.geojson
public/results/geometry/ca-2022-state-assembly-districts.geojson
```

`npm run california:districts:generate` links 2022 and 2024 California U.S. House, State Senate, and State Assembly contests to those district geometry files and writes:

```text
public/results/districts/california-district-drilldown.json
```

Use `npm run california:all` to rebuild California Statement of Vote summaries, district geometry, and district drilldown in one pass.

Pennsylvania general-election summaries are rebuilt with:

```bash
npm run pennsylvania:fetch
```

It downloads official Pennsylvania Department of State precinct return files and readmes for 2020, 2022, and 2024 general elections, then writes:

```text
public/results/pennsylvania-statewide-summary.json
```

The generated summary aggregates precinct rows to contest-level candidate totals and county rows for President, Governor, U.S. Senate, U.S. House, State Senate, and State House where those offices appear on the ballot.

Ohio statewide and district summaries are rebuilt with:

```bash
npm run ohio:generate
```

It parses browser-supplied official Ohio Secretary of State statewide results-by-county XLSX workbooks and writes:

```text
public/results/ohio-statewide-summary.json
```

Current coverage is 397 contests across 2020, 2022, and 2024: 2020 President, U.S. House, State Senate, and State House; 2022 Governor, U.S. Senate, U.S. House, State Senate, and State House; and 2024 President, U.S. Senate, U.S. House, State Senate, and State House. The separate 2022 County Races Summary file is retained as a future local-office source, not imported into the statewide summary.

Texas historical general-election summaries are rebuilt with:

```bash
npm run texas:generate
```

It parses official Texas Secretary of State historical race/county canvass pages for configured static archive elections, plus browser-supplied Texas County by County Canvass PDF district contests, and writes:

```text
public/results/texas-statewide-summary.json
```

Current coverage is 764 contests: 2018 U.S. Senate, Governor, U.S. House, State Senate, and State House from static SOS pages; and 2020, 2022, and 2024 statewide and district contests from County by County Canvass PDFs. PDF-derived statewide coverage includes 2020 President and U.S. Senate, 2022 Governor, and 2024 President and U.S. Senate.

Texas municipal mayor summaries are rebuilt with:

```bash
npm run texas:mayors:generate
```

It parses the official City of Fort Worth City Secretary election-history page, City of San Antonio canvass PDFs and Bexar County historical results files for San Antonio, City of Houston City Secretary combined canvass PDFs, Harris County cumulative result PDFs for Houston, City of Austin canvass resolution PDFs, and City of Dallas canvass resolution PDFs, then writes:

```text
public/results/texas-mayor-summary.json
```

Current coverage is 65 Texas mayor contests: 10 Fort Worth contests from 2007, 2009, 2011 general/runoff, 2017, 2019, 2021 general/runoff, 2023, and 2025; San Antonio mayor contests from 1999 through 2025; Houston 1999, 2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2019, and 2023 mayor contests from City Secretary combined canvass PDFs and Harris County cumulative PDFs; Austin 2022 general/runoff plus 2024 general contests from City Clerk canvass resolutions; and Dallas 1981 through 1999, 2002, 2007, 2011, 2015, 2019, and 2023 mayor contests from the City Secretary master list and canvass resolutions. Fort Worth candidate totals use the official citywide `Vote Total` column; San Antonio 1999, 2003, 2005, and 2007 totals use official City canvass PDFs, most later San Antonio contests use official media-report HTML, San Antonio 2025 general totals aggregate the official Bexar County precinct CSV, Dallas 1981 through 1999 and 2002 use the official City Secretary master list, and PDF-backed San Antonio/Houston/Austin/Dallas contests use candidate-line totals from official summary/cumulative/canvass PDFs or OCR-backed Dallas resolution scans.

Texas current statewide-only summaries are rebuilt with:

```bash
npm run texas:current:generate
```

It parses the Texas Secretary of State public current-results HTML page and writes:

```text
public/results/texas-current-summary.json
```

Current coverage is 30 contests from the May 26, 2026 primary runoff: 17 U.S. House contests, 11 State House contests, one U.S. Senate contest, and one State Senate contest. The source page exposes statewide/district contest totals only, so county rows are intentionally empty.
