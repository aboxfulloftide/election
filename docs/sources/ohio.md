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

- Statewide governor and U.S. Senate general-election results from the Ohio Secretary of State portal, then county detail.

Current project status:

- Not imported yet.
- Useful candidate for a later pilot because the official data portal and county result directory may help with both state and mayor data.

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

- What downloadable endpoint backs the Ohio Secretary of State Data Portal?
- Which county boards expose Excel/CSV versus only interactive reports?
- How far back can Columbus mayor results be collected from Franklin County without manual PDF extraction?
