# Texas Source Registry

## Statewide Source

Primary sources:

- Texas Secretary of State, Election Results/Data: `https://www.sos.state.tx.us/elections/historical/index.shtml`
- Texas Secretary of State, Historical Elections Official Results: `https://elections.sos.state.tx.us/index.htm`
- Texas Secretary of State, Election Results Archive: `https://www.sos.state.tx.us/elections/historical/elections-results-archive.shtml`

Coverage notes:

- Texas Secretary of State provides official historical election results.
- Historical election results are listed for 1992-current.
- The state also provides turnout and voter-registration data, including voter registration and turnout figures from 1970-current.
- County and municipal results often need county election offices.

Initial offices:

- President
- U.S. Senate
- U.S. House
- Governor
- State Senate
- State House

Expected geography:

- Statewide totals.
- County-level official returns.
- District totals and county-by-district returns where available.
- Precinct-level data primarily from county sources, archives, or cast vote record systems in newer years.

First import target:

- Texas statewide official general-election results for governor and U.S. Senate, then U.S. House by district.

Current project status:

- Not imported yet.
- Likely better after one more structured state import because municipal and precinct detail is county-specific.

Importer difficulty:

- Medium to high. Official state results exist, but municipal and precinct detail is county-specific.

## Mayor Sources

### Houston

Primary source:

- Harris County Election Results Archives: `https://www.harrisvotes.com/Election-Results/Archives`

Expected geography:

- Citywide mayor totals.
- Precinct-level reports may be available in archived county files.

### Dallas

Primary sources:

- Dallas County Elections Department, Historical Results: `https://www.dallascountyvotes.org/election-results/historical/`
- Dallas County Elections Department, Election Results: `https://www.dallascountyvotes.org/election-results/`

Expected geography:

- Citywide mayor totals.
- Newer Election Night Reporting pages expose precinct-level details.

### Austin

Primary source:

- Travis County Clerk, Election Results and Reconciliation Forms: `https://votetravis.gov/current-election-information/election-results-and-reconciliation-forms/`

Coverage notes:

- Recent official results include cumulative and precinct-by-precinct reports.
- The page lists official results back at least to 2020 and reconciliation forms from 2022-present.

### San Antonio

Primary sources:

- Bexar County Historical Election Results: `https://www.bexar.org/2186/Historical-Election-Results`
- City of San Antonio Election Results 1856-Present PDF: `https://www.sa.gov/files/assets/main/v/1/occ/documents/municipal-archives-records/finding-aids/city-san-antonio-election-results-1856-2021.pdf`

Coverage notes:

- Bexar County says users can select the year and report to view historical results.
- Bexar County Elections Department covers voter registration and election operations across the county, including San Antonio.
- San Antonio city archive PDF is important for historical mayor/city-election context, but likely requires PDF extraction or manual review.

### Fort Worth

Primary sources:

- Tarrant County Past Election Information: `https://www.tarrantcountytx.gov/en/elections/past-election-information.html`
- City of Fort Worth Election History: `https://www.fortworthtexas.gov/departments/citysecretary/elections/election-history`

Coverage notes:

- Tarrant County notes a Ballot Verification system with ballot images and cast vote records starting with the complete March 2024 primary, with more elections coming.
- Fort Worth city election history includes mayoral election result tables by county portion.

## Open Questions

- Which Texas SOS historical pages can be scraped reliably versus requiring form navigation?
- How far back can county official precinct data be collected for Harris, Dallas, Travis, Bexar, and Tarrant?
- Should cast vote record sources be imported into a separate table before contest-result aggregation?
