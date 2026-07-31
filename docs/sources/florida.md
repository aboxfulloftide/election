# Florida Source Registry

## Statewide Source

Primary source:

- Florida Division of Elections, Election Results Archive: `https://dos.fl.gov/elections/data-statistics/elections-data/election-results-archive/`
- Current reporting system: `https://results.elections.myflorida.com/`

Coverage notes:

- The Division of Elections states that its archive goes back to 1978.
- It includes General, Primary, Presidential Preference Primary, and Special Elections.
- For local and municipal election results, the state directs users to the relevant County Supervisor of Elections Office.
- For results prior to 1978, the state directs users to the State Archives of Florida.

Initial offices:

- President
- U.S. Senate
- U.S. House
- Governor
- State Senate
- State House

Expected geography:

- Statewide totals.
- County-level results for statewide and federal offices.
- District/legislative contests may require district-aware parsing from state reports.
- Precinct-level data should be evaluated by county and year.

Implemented official precinct import:

- Division of Elections precinct-level general-election ZIPs from 2012, 2014, 2016, 2018, 2020, 2022, and 2024.
- Imported offices where they appear on the ballot: President, U.S. Senate, U.S. House, Governor, State Senate, and State House.
- Imported reporting geography: official precinct/polling-location rows, with county FIPS normalization.
- Current validated import: 672,309 normalized result rows, 922 contests, all 67 counties for every configured year, zero duplicate result keys.
- Generated files: `public/results/florida-{year}-statewide-summary.json` and `public/results/florida-statewide-summary.json`.

Implemented official district geometry:

- Florida Legislature Office of Economic and Demographic Research 2022 redistricting-cycle files.
- Registered layers: congressional districts `P000C0109`, State House districts `H000H8013`, State Senate districts `S027S8058`.
- Registered files: official shapefile ZIPs and census block-equivalency TXT files.
- Generated files: `public/results/florida-geometry-layers.json` and district GeoJSON files under `public/results/geometry/`.
- 2022 and 2024 U.S. House, State Senate, and State House contest summaries include geometry IDs, official IDs, layer keys, and GeoJSON URLs.

Implemented precinct geometry pilot:

- Miami-Dade County official 2012 and 2014/2015 precinct shapefile vintages are converted from NAD83 Florida East State Plane feet to WGS84 and merged by precinct identifier.
- Broward County official 2020, 2022, and 2024 precinct layers are imported from the Broward GIS ArcGIS service. Broward 2020 and 2024 join all result precinct IDs; the 2022 result file uses numeric IDs while the available boundary vintage uses lettered IDs, so its 355 unmatched IDs are retained without a map join.
- Generated files: `public/results/florida-precinct-geometry-layers.json`, `public/results/geometry/fl-miami-dade-2012-precincts.geojson`, and `public/results/geometry/fl-miami-dade-2014-precincts.geojson`.
- Source pages: `https://www.votemiamidade.gov/elections/data/precincts-districts-municipalities-2012.page` and `https://www.votemiamidade.gov/elections/data/precincts-districts-municipalities-2015.page`.
- 2022 and 2024 district/county drilldown bundles are generated under `public/results/districts/`.
- Frontend Florida district map mode reads these bundles for year, office, district, winner, and 2024-vs-2022 shift selection.
- Frontend precinct bundle discovery reads `public/results/florida-precinct-catalog.json`; bundles with zero validated geometry matches remain audit-only and are not exposed as map choices.

Configured official ZIP URLs:

- 2024 General Election: `https://fldoswebumbracoprod.blob.core.windows.net/media/708761/2024-gen-outputofficial1.zip`
- 2022 General Election: `https://fldoswebumbracoprod.blob.core.windows.net/media/706300/2022-gen-outputofficial.zip`
- 2020 General Election: `https://fldoswebumbracoprod.blob.core.windows.net/media/703763/2020-general-election-rev.zip`
- 2018 General Election: `https://fldoswebumbracoprod.blob.core.windows.net/media/700501/precinctlevelelectionresults2018gen.zip`
- 2016 General Election: `https://fldoswebumbracoprod.blob.core.windows.net/media/697454/precinctlevelelectionresults2016gen.zip`
- 2014 General Election: `https://fldoswebumbracoprod.blob.core.windows.net/media/697201/precinctlevelelectionresults2014gen.zip`
- 2012 General Election: `https://fldoswebumbracoprod.blob.core.windows.net/media/697204/precinctlevelelectionresults2012gen.zip`
- Data definitions: `https://fldoswebumbracoprod.blob.core.windows.net/media/709209/final-precinct-level-elections-data-definitions-and-field-codes_20250624.pdf`

Remaining Florida collection targets:

- Add richer frontend Florida drilldown behavior from generated district bundles.
- Backfill additional mayor years where official county/city archives expose structured results.
- Extend official county/year precinct geometry sources beyond the Miami-Dade pilot for precinct map views.

Importer difficulty:

- Medium. Official precinct files are scripted for 2012-2024 statewide and district offices; Miami-Dade geometry is piloted, while statewide geometry joins and older archive formats still need inspection.

## Mayor Sources

### Miami

Primary source:

- Miami-Dade Supervisor of Elections, Past Election Results: `https://www.votemiamidade.gov/elections/data/results-archive.page`

Coverage notes:

- The Miami-Dade archive lists election results from 1996 to 2024.
- The office says results before 1996 require a public-records email request.

Implemented import:

- `npm run florida:mayors:generate` parses official Election Night Reporting summary pages for configured municipal elections.
- Generated file: `public/results/florida-mayor-summary.json`.
- Current coverage: seventeen mayor contests across Miami, Hialeah, Miami Beach, Sunny Isles Beach, Tampa, Jacksonville, and Orlando, including runoffs where present.
- Referendum-style Yes/No questions that mention mayor terms are excluded from the mayor contest dataset.

Expected geography:

- Citywide summaries for mayor.
- Precinct or precinct-like detail may be available in downloadable reports for some years.

### Jacksonville

Primary source:

- Duval County Supervisor of Elections, Election Results Archive: `https://www.duvalelections.gov/Archive.aspx?AMID=36`

Expected geography:

- Citywide mayor results.
- Precinct results available through Election Night Reporting pages for newer elections.

Implemented import:

- 2015 first/general, 2019 first, and 2023 first/general mayor contests are parsed from official Duval Election Night Reporting summary pages.
- The configured 2019 general page has no mayor contest and is retained as an empty election in the generated summary.

### Tampa

Primary source:

- Hillsborough County Supervisor of Elections, Election Results: `https://www.votehillsborough.gov/183/Election-Results`

Expected geography:

- Citywide mayor results.
- Precinct detail depends on election-year reports.

### Orlando

Primary source:

- City of Orlando election information: `https://www.orlando.gov/Our-Government/Records-and-Documents/Election-Information`
- Orange County Supervisor of Elections: `https://voteorangefl.gov/`

Expected geography:

- Citywide mayor results.
- Orange County administers voter services; results archive needs direct inspection per election year.

Implemented import:

- The 2023 Orlando mayor contest is parsed from Orange County's official election-record page and ENR summary link.

## Open Questions

- Which Florida archive formats are easiest for extending official results before 2012: CSV, XLS, HTML, PDF, or zipped reports?
- How far back can official county-level governor, U.S. Senate, U.S. House, and state legislative returns be collected without PDF extraction?
- Which counties provide clean precinct-level files for municipal and legislative races?
- Which geometry sources best match Florida congressional and state legislative districts by redistricting cycle?
