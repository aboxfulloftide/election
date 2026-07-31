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
- The 1992-2018 static historical result pages expose stable race-select and race/county canvass HTML pages.
- The 2019-2024 result portal is separate from the static historical pages. Direct non-browser requests to `https://results.texas-election.com/` currently return a Cloudflare challenge page with `cf-mitigated: challenge`.
- The 2025-current lane moved to Civix/Goelect. Its public results page at `https://electionresults.sos.state.tx.us/results.html` is accessible as plain HTML and imported for statewide-only totals, while the Civix app APIs return `401 Bearer` without an authenticated session.

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

- 2018 general election imported from official static historical race/county canvass pages.
- 2019-2024 official results are identified but blocked for unattended import from this environment because the public portal returns a Cloudflare challenge before any bundle or export endpoint can be inspected.
- Browser-supplied official County by County Canvass Report PDFs for 2020, 2022, and 2024 are staged under `data/raw/texas`. District contests are imported from those PDFs. The prior Excel exports were malformed turnout-report shells.
- 2025-current public HTML is imported for statewide/current totals, but it does not backfill the missing 2020/2022/2024 cycle.
- The 2020/2022/2024 county canvass PDFs are now imported for configured statewide and district contests. PDF-derived rows are quality grade `B`.

Importer difficulty:

- Medium to high. Official state results exist, but municipal and precinct detail is county-specific.

Implemented import:

- `npm run texas:generate` parses official 2018 Texas Secretary of State historical race/county canvass pages and PDF-derived 2020/2022/2024 statewide/district contests.
- Generated file: `public/results/texas-statewide-summary.json`.
- Current coverage: 764 contests. 2018 includes U.S. Senate, Governor, 36 U.S. House districts, 15 State Senate districts, and 150 State House districts. PDF-derived coverage adds 2020 President, U.S. Senate, U.S. House, State Senate, and State House; 2022 Governor, U.S. House, State Senate, and State House; and 2024 President, U.S. Senate, U.S. House, State Senate, and State House with validated county rows.
- County rows are included for each imported contest.
- `npm run texas:current:generate` parses the official Texas Secretary of State current public HTML page.
- Generated current file: `public/results/texas-current-summary.json`.
- Current statewide-only coverage: 30 contests from the May 26, 2026 primary runoff, including U.S. Senate, U.S. House, State Senate, and State House contests. County rows are not exposed by the public HTML and are intentionally empty in this file.
- `npm run texas:mayors:generate` parses the official City of Fort Worth City Secretary election-history page, City of San Antonio official canvass PDFs and Bexar County official historical result files for San Antonio, Harris County official cumulative result PDFs for Houston, City of Austin official canvass resolutions, and City of Dallas official canvass resolutions.
- Generated mayor file: `public/results/texas-mayor-summary.json`.
- Current mayor coverage: 10 Fort Worth mayor contests from 2007, 2009, 2011 general/runoff, 2017, 2019, 2021 general/runoff, 2023, and 2025, San Antonio mayor contests from 1999 through 2025, Houston 1999, 2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2019, and 2023 mayor contests, Austin 2022/2024 mayor contests, and Dallas 1981, 1983, 1985, 1987 general/runoff, 1989, 1991, 1995, 1999, 2002 special/runoff, 2007, 2011 general/runoff, 2015, 2019 general/runoff, and 2023 mayor contests.
- Austin mayor coverage: 2022 general, 2022 runoff, and 2024 general contests are imported from official City Clerk canvass resolution PDFs.

### Austin

Primary sources:

- City Clerk: `https://www.austintexas.gov/department/city-clerk`
- November 2024 Election: `https://www.austintexas.gov/clerk/november-2024-election`
- Travis County election results archive: `https://votetravis.gov/current-election-information/election-results-and-reconciliation-forms/`

Coverage notes:

- Austin 2022 general and runoff mayor contests are imported from adopted City Council canvass resolution PDFs.
- Austin 2024 general mayor contest is imported from a City Council backup PDF with redline vote values; the parser keeps the final post-bracket totals.
- Direct Travis Clarity ENR requests returned CloudFront 403 from the terminal, so the City Clerk canvass resolutions are the imported source for citywide Austin totals.
- Fort Worth candidate totals use the official citywide `Vote Total` column; county portion splits are preserved where present.
- San Antonio 1999, 2003, 2005, and 2007 totals use official City canvass PDFs, most later San Antonio contests use official media-report HTML, San Antonio 2025 general totals aggregate the official Bexar County precinct CSV, and San Antonio 2021, 2023, and 2025 runoff use candidate-line totals from official summary PDFs.

## Mayor Sources

### Houston

Primary source:

- City of Houston City Secretary election results: `https://www.houstontx.gov/citysec/elections/`
- Harris County Election Results Archives: `https://www.harrisvotes.com/Election-Results/Archives`

Expected geography:

- City Secretary combined citywide totals for older cycles that include Harris, Fort Bend, and Montgomery county portions.
- Harris County cumulative totals for the City of Houston mayor contest.
- Precinct-level reports may be available in archived county files.

Coverage notes:

- Houston 1999 general, 2001 general/runoff, 2003 general, 2005 general, and 2007 general mayor totals are imported from City Secretary official combined Harris/Fort Bend/Montgomery PDFs.
- Houston 2009 general/runoff, 2011 general, 2013 general, 2015 general/runoff, 2019 general/runoff, and 2023 general/runoff mayor totals are imported from Harris County official cumulative result PDFs.
- The 1999, 2005, 2011, and 2013 runoff archives did not contain mayor contests and are intentionally not imported.

### Dallas

Primary sources:

- City of Dallas City Secretary Historical Data: `https://dallascityhall.com/government/citysecretary/elections/Pages/historical-data.aspx`
- Dallas County Elections Department, Historical Results: `https://www.dallascountyvotes.org/election-results/historical/`
- Dallas County Elections Department, Election Results: `https://www.dallascountyvotes.org/election-results/`

Expected geography:

- Citywide mayor totals.
- Newer Election Night Reporting pages expose precinct-level details.

Coverage notes:

- Dallas 2007 general, 2011 general, 2011 runoff, 2015 general, 2019 general, 2019 runoff, and 2023 general mayor contests are imported from official City Secretary canvass resolution PDFs.
- Dallas 2011 general/runoff canvass PDFs are scanned files; the importer uses `ocrmypdf` before extracting the Place 15 mayor totals and caches OCR text under ignored `data/raw/official/texas/mayors/`.
- Dallas 2002 special and special runoff mayor totals are imported from the official City Secretary master list as quality `C`; original resolution numbers `02-0380` and `02-0711` are identified, and the February 20, 2002 City Council minutes confirm runoff action item `02-0711`, but direct original resolution PDF URLs were not found in this pass.
- Dallas 1981 through 1999 mayor totals are imported from the official City Secretary master list as quality `C`. Older records use Place 11/Mayor; Dallas changed to Place 15/Mayor for the 1991 cycle. The 1993 and 1997 master-list entries show no mayor contest (`N/A`) and are intentionally not imported.
- Direct Dallas County historical page requests can return an AWS WAF challenge from the terminal, so the imported source uses stable Dallas City Secretary resolution PDFs.

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
- San Antonio mayor results from 1999 through 2025 are imported from official City canvass PDFs and Bexar County historical results. The 1999 mayor totals come from Ordinance 89699 and the 2003 totals come from Ordinance 97603; older San Antonio mayor years remain useful but likely require PDF extraction or manual review.
- San Antonio city archive PDF is important for historical mayor/city-election context.

### Fort Worth

Primary sources:

- Tarrant County Past Election Information: `https://www.tarrantcountytx.gov/en/elections/past-election-information.html`
- City of Fort Worth Election History: `https://www.fortworthtexas.gov/departments/citysecretary/elections/election-history`

Coverage notes:

- Tarrant County notes a Ballot Verification system with ballot images and cast vote records starting with the complete March 2024 primary, with more elections coming.
- Fort Worth city election history includes mayoral election result tables by county portion and is imported for citywide mayor totals.

## Open Questions

- Can future Texas County by County Canvass PDFs keep using the same `pdftotext -tsv` parser, or will newer portal exports require another source format?
- How far back can county official precinct data be collected for Harris, Dallas, Travis, Bexar, and Tarrant?
- Should cast vote record sources be imported into a separate table before contest-result aggregation?
