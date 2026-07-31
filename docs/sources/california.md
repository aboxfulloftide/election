# California Source Registry

## Statewide Source

Primary source:

- California Secretary of State, Prior Elections: `https://www.sos.ca.gov/elections/prior-elections`
- California Secretary of State, 2024 General Election Statement of Vote: `https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-5-2024/statement-vote`
- California Secretary of State, 2020 General Election Statement of Vote: `https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-3-2020/statement-vote`

Coverage notes:

- Statement of Vote pages provide PDF and XLSX files.
- The 2024 Statement of Vote includes statewide summary by county, political districts within counties, counties by congressional district, counties by Senate district, and other district/county breakdowns.
- California is likely one of the best pilot states for county-by-district and district-aware imports.

Initial offices:

- President
- U.S. Senate
- U.S. House
- Governor
- State Senate
- State Assembly

Expected geography:

- Statewide totals.
- County totals.
- Counties by congressional district.
- Counties by state Senate district.
- Political districts within counties.
- Precinct-level detail from county registrars for selected counties.

Current import target:

- Maintain 2018, 2020, 2022, and 2024 Statement of Vote spreadsheet imports, then add matching historical district geometry before adding older district maps.

Current project status:

- Imported for 2024 President, U.S. Senate, U.S. House, State Senate, and State Assembly.
- Imported for 2022 Governor, U.S. Senate, U.S. House, State Senate, and State Assembly.
- Imported for 2020 President, U.S. House, State Senate, and State Assembly.
- The generated summary uses official Secretary of State XLSX files and is written to `public/results/california-statewide-summary.json`.
- 2020-cycle congressional, State Senate, and State Assembly district geometry is generated from official California Citizens Redistricting Commission final map shapefiles.

Importer difficulty:

- Medium. Structured XLSX files are promising, but top-two election rules, nonpartisan offices, district/county splits, and write-ins require careful modeling.

## Mayor Sources

### Los Angeles

Primary sources:

- Los Angeles County Registrar-Recorder/County Clerk, Past Election Results: `https://www.lavote.gov/home/voting-elections/current-elections/election-results/past-election-results`
- City of Los Angeles Election Archives: `https://clerk.lacity.gov/clerk-services/elections/election-archives`

Coverage notes:

- Los Angeles County states that Official Election Returns indicate ballots cast and turnout.
- Statement of Votes Cast provides candidate/measure breakdowns.
- Precinct Bulletins provide precinct/polling-place results.
- Votes Cast by Community provides city/community turnout and vote totals, with limitations for smaller communities.

### San Francisco

Primary sources:

- San Francisco Department of Elections: `https://www.sf.gov/departments--department-elections`
- San Francisco Past Election Results: `https://www.sf.gov/past-election-results`

Coverage notes:

- Past results page provides certified results.
- Past election results are available by election.
- Historical turnout comparison goes back to 1899.

### San Diego

Primary sources:

- San Diego County Registrar of Voters, Past Election Information: `https://www.sdvote.com/content/rov/en/past-election-info.html`
- City of San Diego historical election results: `https://www.sandiego.gov/city-clerk/elections/city/past/results`

Coverage notes:

- City of San Diego provides candidate races/results by office.
- City materials include voter pamphlets and election results by election date from 1970 forward.
- Decade PDF files for propositions go back to 1900.

### San Jose

Primary source:

- Santa Clara County Registrar of Voters, Past Election Information and Results: `https://vote.santaclaracounty.gov/elections/past-election-information-and-results`

Coverage notes:

- Files are listed in PDF or Excel format.
- Summary Results provide overall contest results.
- Statement of Vote provides detailed precinct results.
- Write-in results by precinct should be added to Statement of Vote totals.

### Sacramento

Primary source:

- Sacramento County Voter Registration and Elections, Archived Elections: `https://elections.saccounty.gov/content/vre/us/en/election-information/archived-elections.html`

Coverage notes:

- Archived elections include Final Results and Statement of the Vote for many recent elections.
- Sacramento County notes past election information for General and Special Elections dating back to 1998.

## Open Questions

- Which Secretary of State XLSX layouts are stable across years?
- How should top-two primary/general history be represented for nonpartisan mayor races?
- Which county Statement of Vote formats can be parsed generically across California counties?
# California Sources

## 2024 Statement of Vote

Source: California Secretary of State, General Election Statement of Vote, November 5, 2024.

- Statement of Vote page: `https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-5-2024/statement-vote`
- President statewide summary by county XLSX: `https://elections.cdn.sos.ca.gov/sov/2024-general/ssov/pres-summary-by-county.xlsx`
- U.S. Senate full term statewide summary by county XLSX: `https://elections.cdn.sos.ca.gov/sov/2024-general/ssov/us-senate-summary-by-county-ft.xlsx`
- U.S. Senate partial/unexpired term statewide summary by county XLSX: `https://elections.cdn.sos.ca.gov/sov/2024-general/ssov/us-senate-summary-by-county-pt.xlsx`
- U.S. House district XLSX: `https://elections.cdn.sos.ca.gov/sov/2024-general/sov/25-us-rep-congress.xlsx`
- State Senate district XLSX: `https://elections.cdn.sos.ca.gov/sov/2024-general/sov/37-state-senator.xlsx`
- State Assembly district XLSX: `https://elections.cdn.sos.ca.gov/sov/2024-general/sov/42-state-assembly.xlsx`

Implemented commands:

```bash
npm run california:download
npm run california:generate
npm run california:fetch
npm run california:geometry:fetch
npm run california:districts:generate
npm run california:all
```

Current coverage:

- 2020 President: all 58 counties.
- 2020 U.S. House: 53 district contests, with county rows within each district.
- 2020 State Senate: 20 district contests for odd-numbered districts on the 2020 ballot, with county rows within each district.
- 2020 State Assembly: 80 district contests, with county rows within each district.
- 2024 President: all 58 counties.
- 2024 U.S. Senate full term: all 58 counties.
- 2024 U.S. Senate partial/unexpired term: all 58 counties.
- 2024 U.S. House: 52 district contests, with county rows within each district.
- 2024 State Senate: 20 district contests for odd-numbered districts on the 2024 ballot, with county rows within each district.
- 2024 State Assembly: 80 district contests, with county rows within each district.
- 2022 Governor: all 58 counties.
- 2022 U.S. Senate full term: all 58 counties.
- 2022 U.S. Senate partial/unexpired term: all 58 counties.
- 2022 U.S. House: 52 district contests, with county rows within each district.
- 2022 State Senate: 20 district contests for even-numbered districts on the 2022 ballot, with county rows within each district.
- 2022 State Assembly: 80 district contests, with county rows within each district.

Rows written to `public/results/california-statewide-summary.json` are sourced from official California Secretary of State XLSX files and marked quality grade `A`.

## 2020 Statement of Vote

Source: California Secretary of State, General Election Statement of Vote, November 3, 2020.

- Statement of Vote page: `https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-3-2020/statement-vote`
- President by County XLSX: `https://elections.cdn.sos.ca.gov/sov/2020-general/sov/18-presidential.xlsx`
- U.S. House district XLSX: `https://elections.cdn.sos.ca.gov/sov/2020-general/sov/24-us-reps.xlsx`
- State Senate district XLSX: `https://elections.cdn.sos.ca.gov/sov/2020-general/sov/36-state-senate.xlsx`
- State Assembly district XLSX: `https://elections.cdn.sos.ca.gov/sov/2020-general/sov/41-state-assembly.xlsx`

Note: 2020 U.S. House districts use the pre-2022 53-district map. The contests are imported into the statewide summary, but the district drilldown bundle does not link them to 2022-cycle geometry.

## 2018 Statement of Vote

Source: California Secretary of State, General Election Statement of Vote, November 6, 2018.

- Statement of Vote page: `https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-6-2018/statement-vote`
- Governor by County XLS: `https://elections.cdn.sos.ca.gov/sov/2018-general/sov/21-governor.xls`
- U.S. Senate by County XLS: `https://elections.cdn.sos.ca.gov/sov/2018-general/sov/45-us-senator.xls`
- U.S. House district XLS: `https://elections.cdn.sos.ca.gov/sov/2018-general/sov/48-congress.xls`
- State Senate district XLS: `https://elections.cdn.sos.ca.gov/sov/2018-general/sov/62-state-senator.xls`
- State Assembly district XLS: `https://elections.cdn.sos.ca.gov/sov/2018-general/sov/68-state-assemblymember.xls`

Note: 2018 district contests use pre-2022 district boundaries. The contests are imported into the statewide summary, but the district drilldown bundle does not link them to 2022-cycle geometry.

## 2022 Statement of Vote

Source: California Secretary of State, General Election Statement of Vote, November 8, 2022.

- Statement of Vote page: `https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-8-2022/statement-vote`
- Governor statewide summary by county XLSX: `https://elections.cdn.sos.ca.gov/sov/2022-general/ssov/governor-summary.xlsx`
- U.S. Senate full term statewide summary by county XLSX: `https://elections.cdn.sos.ca.gov/sov/2022-general/ssov/us-senate-summary-by-county-ft.xlsx`
- U.S. Senate partial/unexpired term statewide summary by county XLSX: `https://elections.cdn.sos.ca.gov/sov/2022-general/ssov/us-senate-summary-by-county.xlsx`
- U.S. House district XLSX: `https://elections.cdn.sos.ca.gov/sov/2022-general/sov/48-congress.xlsx`
- State Senate district XLSX: `https://elections.cdn.sos.ca.gov/sov/2022-general/sov/60-state-senator.xlsx`
- State Assembly district XLSX: `https://elections.cdn.sos.ca.gov/sov/2022-general/sov/65-state-assemblymember.xlsx`

## 2020 Final District Geometry

Source: California Citizens Redistricting Commission, Final Maps.

- Final Maps page: `https://wedrawthelines.ca.gov/final-maps/`
- Final CD shapefiles ZIP: `https://wedrawthelines.ca.gov/wp-content/uploads/sites/64/2023/01/OneDrive_2023-01-19-2.zip`
- Final SD shapefiles ZIP: `https://wedrawthelines.ca.gov/wp-content/uploads/sites/64/2023/01/OneDrive_2023-01-19-3.zip`
- Final AD shapefiles ZIP: `https://wedrawthelines.ca.gov/wp-content/uploads/sites/64/2023/01/OneDrive_2023-01-19-5.zip`

Generated files:

- `public/results/california-geometry-layers.json`
- `public/results/geometry/ca-2022-congressional-districts.geojson`
- `public/results/geometry/ca-2022-state-senate-districts.geojson`
- `public/results/geometry/ca-2022-state-assembly-districts.geojson`
- `public/results/districts/california-district-drilldown.json`

Geometry-linked coverage:

- 52 congressional district features linked to 52 U.S. House contests in 2022 and 2024.
- 40 State Senate district features linked to the 20 even-numbered 2022 State Senate contests and 20 odd-numbered 2024 State Senate contests on the ballot.
- 80 State Assembly district features linked to 80 State Assembly contests in 2022 and 2024.

Senate note: the CRC Final Maps page notes that Senate districts are implemented over a two-year period. The 2022 Statement of Vote includes even-numbered Senate contests, and the 2024 Statement of Vote includes odd-numbered Senate contests.
