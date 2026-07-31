# Ohio Source Registry

## Statewide Source

Primary sources:

- Ohio Secretary of State Data Portal: `https://www.ohiosos.gov/data`
- Ohio Secretary of State Past Election Results: `https://data.ohiosos.gov/portal/past-election-results`
- Ohio Secretary of State Local Election Results Directory: `https://www.ohiosos.gov/directories/local-election-results`

Coverage notes:

- The Ohio Secretary of State Data Portal is the official data portal.
- Ohio's DATA Act created a state emphasis on collecting, preserving, and publishing electronic election data.
- The Local Election Results Directory points to county result sources.
- Direct requests to `https://data.ohiosos.gov/portal/past-election-results`, `https://www.ohiosos.gov/directories/local-election-results`, and sampled county ENR pages currently return an Ohio Secretary of State website maintenance page with HTTP 403.
- Browser-supplied official XLSX workbooks for 2020, 2022, and 2024 are imported. The separate browser-supplied 2022 County Races Summary file is retained as a future local-office source.

Initial offices:

- President
- U.S. Senate
- U.S. House
- Governor
- State Senate
- State House

Expected geography:

- Statewide totals.
- County totals.
- Local county result pages for municipal races and precinct detail.
- Older historical data may exist in PDF or county archive pages.

First import target:

- County and municipal sources for local-office and mayor coverage.

Current project status:

- `npm run ohio:generate` parses official Ohio Secretary of State statewide results-by-county XLSX workbooks supplied under `data/raw/ohio`.
- Generated file: `public/results/ohio-statewide-summary.json`.
- Current coverage: 397 contests across 2020, 2022, and 2024. The 2020 workbook covers President, U.S. House, State Senate, and State House. The 2022 workbook covers Governor, U.S. Senate, U.S. House, State Senate, and State House. The 2024 workbook covers President, U.S. Senate, U.S. House, State Senate, and State House.
- `data/raw/ohio/ohio_2022_general_county_races_summary_partial.xlsx` covers county-office races only and is intentionally not imported into the statewide summary.

Importer difficulty:

- Medium. Ohio has strong official sources, but portal-backed pages and county-specific archives need inspection for stable download endpoints.

## Mayor Sources

### Columbus

Primary source:

- Franklin County Board of Elections live/results viewer: `https://vote.franklincountyohio.gov/elections`

Coverage notes:

- Franklin County has election info pages reaching back at least into the 1960s.
- The 1965 election info page includes election results/downloads as PDFs.

Expected geography:

- Citywide mayor totals.
- PDFs for older elections.
- Newer live/results viewer data needs endpoint inspection.

### Cleveland

Primary source:

- Cuyahoga County Board of Elections, Elections page: `https://boe.cuyahogacounty.gov/elections`

Coverage notes:

- The county page says past election details date back to 2010.
- It points to an Election Results Archive for results dating back to 1983.

Expected geography:

- Citywide mayor totals.
- Official archive and newer interactive results.

### Cincinnati

Primary source:

- Hamilton County Board of Elections, Election Results: `https://votehamiltoncountyohio.gov/results/`

Coverage notes:

- Hamilton County provides archived official election results in interactive, PDF, and Excel spreadsheet forms.

Expected geography:

- Citywide mayor totals.
- Precinct detail likely available in interactive or spreadsheet outputs for many recent years.

### Toledo

Primary source:

- Lucas County Board of Elections: `https://co.lucas.oh.us/74/Board-of-Elections/`

Expected geography:

- Citywide mayor totals.
- Newer Ohio Election Night Reporting pages need endpoint inspection.
- Older official files may require county site navigation or archive requests.

## Open Questions

- Should the 2022 County Races Summary workbook be imported into a separate local-office dataset later?
- What downloadable endpoint backs the Ohio Secretary of State Data Portal when the portal is not returning the maintenance page?
- Which county boards expose Excel/CSV versus only interactive reports?
- How far back can Columbus mayor results be collected from Franklin County without manual PDF extraction?
