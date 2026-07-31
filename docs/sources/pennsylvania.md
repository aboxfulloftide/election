# Pennsylvania Source Registry

## Statewide Source

Primary sources:

- Pennsylvania Department of State, Historical Elections Data: `https://www.pa.gov/agencies/dos/resources/voting-and-elections-resources/voting-and-election-statistics/election-data`
- Pennsylvania Election Returns: `https://www.electionreturns.pa.gov/`

Coverage notes:

- The Department of State provides public access to election data.
- The state describes both unofficial and official election returns submitted by county boards of elections.
- Recent summary data includes handbooks alongside files, starting with the 2024 General Election.

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
- District-level state legislative and congressional races.
- Precinct-level data likely requires county-level sources for many years.

First import target:

- Pennsylvania governor and U.S. Senate general-election official returns from state files, then congressional/state legislative district totals.

Current project status:

- Imported official 2020, 2022, and 2024 general-election precinct return files.
- Generated file: `public/results/pennsylvania-statewide-summary.json`.
- Current coverage: 741 contests across 2020, 2022, and 2024 for President, Governor, U.S. Senate, U.S. House, State Senate, and State House where on ballot.
- The parser aggregates official precinct rows to contest totals and county rows.

Importer difficulty:

- Medium. Recent general-election precinct return files are direct CSV-style text downloads; older years remain available but need batch expansion and validation.

## Mayor Sources

### Philadelphia

Primary source:

- Philadelphia City Commissioners, Archived Data Sets: `https://vote.phila.gov/resources-data/past-election-results/archived-data-sets/`

Coverage notes:

- Archived data sets include major-office results.
- Some years include city and ward summaries and division detail.
- Philadelphia's Ballot Box App has results from as far back as 2002, with spreadsheet download support.

Expected geography:

- Citywide mayor totals.
- Ward and division detail where available.

### Pittsburgh

Primary source:

- Allegheny County Election Results: `https://www.alleghenycounty.us/Government/Elections/Election-Results`

Coverage notes:

- Allegheny County provides primary, general, and special election results and election experience reports.
- Pittsburgh mayor data should be imported from Allegheny County official files where possible.

Expected geography:

- Citywide mayor totals.
- Precinct or ward-level detail depends on county report format and year.

## Open Questions

- How far back does the Pennsylvania state portal provide structured files by office?
- Which historical state legislative races are available as county-by-district returns rather than district totals only?
- Are Philadelphia division-level files stable enough for a reusable municipal importer?
