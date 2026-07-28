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

First import target:

- Governor and U.S. Senate general-election results from the Division of Elections archive.

Importer difficulty:

- Medium. Official source is clear, but older formats and district contests need inspection.

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

