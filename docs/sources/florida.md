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
- Generated files: `public/results/florida-{year}-statewide-summary.json` and `public/results/florida-statewide-summary.json`.

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

- District and precinct geometry joins for U.S. House, State Senate, and State House maps.
- Major city mayor contests.

Importer difficulty:

- Medium. Official precinct files are scripted for 2012-2024 statewide and district offices; geometry joins and older archive formats still need inspection.

## Mayor Sources

### Miami

Primary source:

- Miami-Dade Supervisor of Elections, Past Election Results: `https://www.votemiamidade.gov/elections/data/results-archive.page`

Coverage notes:

- The Miami-Dade archive lists election results from 1996 to 2024.
- The office says results before 1996 require a public-records email request.

Expected geography:

- Citywide summaries for mayor.
- Precinct or precinct-like detail may be available in downloadable reports for some years.

### Jacksonville

Primary source:

- Duval County Supervisor of Elections, Election Results Archive: `https://www.duvalelections.gov/Archive.aspx?AMID=36`

Expected geography:

- Citywide mayor results.
- Precinct results available through Election Night Reporting pages for newer elections.

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

## Open Questions

- Which Florida archive formats are easiest for scripted import: CSV, XLS, HTML, PDF, or zipped reports?
- How far back can official county-level governor and U.S. Senate returns be collected without PDF extraction?
- Which counties provide clean precinct-level files for municipal and legislative races?
