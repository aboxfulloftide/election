# Election Night Map

Interactive U.S. election-night map for comparing historical election results across election cycles.

## Current Scope

- County-level presidential general election results from 2000 through 2024.
- Florida official precinct-level general election results from 2012 through 2024 for President, U.S. Senate, U.S. House, Governor, State Senate, and State House where those offices were on the ballot.
- California official 2018, 2020, 2022, and 2024 Statement of Vote summaries for statewide and district contests.
- Florida official municipal mayor summaries from Election Night Reporting pages for Miami-Dade cities, Tampa, Jacksonville, and Orlando.
- Florida official 2022 redistricting-cycle district geometry for congressional, State Senate, and State House map layers.
- California official 2022 redistricting-cycle district geometry for congressional, State Senate, and State Assembly map layers.
- Florida 2022 and 2024 district/county drilldown bundles for geometry-linked district contests.
- California 2022 and 2024 district/county drilldown bundle for geometry-linked district contests. California 2020 contests are imported but are not geometry-linked until pre-2022 district maps are added.
- A React/Vite map UI with national totals, country/state/county comparison cards, year selection, election-to-election margin shift, scalable official-state selection, official county maps, and Florida/California district contest maps.
- Repeatable Python ingestion scripts that download raw files, import MySQL, validate normalized rows, and build app-ready JSON.
- Planning and handoff docs for continuing data collection before major interface expansion.

## Imported Data

Imported sources:

- MIT Election Data and Science Lab, "County Presidential Election Returns 2000-2024", Harvard Dataverse DOI `10.7910/DVN/VOQCHQ`.
- Georgia Secretary of State official 2020 general-election recount summary ZIP, aggregated to county presidential totals before supplemental data is applied.
- Kentucky State Board of Elections official 2020 certified general-election PDF, parsed to county presidential totals before supplemental data is applied.
- North Carolina State Board of Elections official precinct results ZIPs, aggregated to county presidential totals for 2020 and 2024 before supplemental data is applied.
- Virginia Department of Elections historical election CSV downloads, aggregated to locality presidential totals for 2020 and 2024 before supplemental data is applied.
- Wisconsin Elections Commission official 2024 county-by-county presidential canvass PDF, parsed to county presidential totals before supplemental data is applied.
- Tony McGovern's `US_County_Level_Election_Results_08-24` GitHub CSVs, used only as a non-authoritative supplement for missing MIT 2020/2024 county rows.
- Florida Division of Elections official precinct-level general-election ZIPs for 2012, 2014, 2016, 2018, 2020, 2022, and 2024.
- Florida Legislature Office of Economic and Demographic Research 2022 congressional, State Senate, and State House shapefile/block-equivalency files.
- California Secretary of State 2018, 2020, 2022, and 2024 Statement of Vote spreadsheet files for statewide and district contests.
- Pennsylvania Department of State official 2020, 2022, and 2024 general-election precinct return files.
- Ohio Secretary of State official 2020, 2022, and 2024 statewide results-by-county workbooks.
- Texas Secretary of State official 2018 general-election historical race/county canvass pages.
- National federal/state coverage matrix for all 50 states, 2000-2026, and six active office families.
- California Citizens Redistricting Commission 2020 final map shapefiles for congressional, State Senate, and State Assembly districts.
- Miami-Dade, Hillsborough, Duval, and Orange Supervisor of Elections official Election Night Reporting pages for configured municipal mayor contests.
- City of Fort Worth City Secretary official election-history page for mayor contests.
- City of San Antonio and Bexar County official historical results for San Antonio mayor contests from 2005 through 2025.
- City of Houston City Secretary combined canvass PDFs for Houston 1999, 2001, 2003, 2005, and 2007 mayor contests.
- Harris County Clerk official cumulative result PDFs for Houston 2009, 2011, 2013, 2015, 2019, and 2023 mayor contests.
- City of Austin City Clerk official canvass resolutions for Austin 2022 and 2024 mayor contests.
- City of Dallas City Secretary official master list and canvass resolutions for Dallas 1981 through 1999, 2002, 2007, 2011, 2015, 2019, and 2023 mayor contests.
- Texas Secretary of State current public HTML for statewide-only 2026 primary runoff contest totals.

The Dataverse download requires a guestbook response. The script defaults to a generic project contact; override it with:

```bash
export ELECTION_DATA_NAME="Your Name"
export ELECTION_DATA_EMAIL="you@example.com"
export ELECTION_DATA_INSTITUTION="Your Org"
export ELECTION_DATA_POSITION="Developer"
```

## Setup

```bash
npm install
python3 -m pip install -r requirements.txt
npm run data:fetch
npm run florida:fetch
npm run florida:geometry:fetch
npm run dev
```

The app can run after `npm install` because generated JSON summaries are committed. Run the data pipelines when rebuilding MySQL or refreshing generated results.

## Useful Commands

```bash
npm run data:fetch              # MIT presidential: download/import/validate/generate
npm run data:download           # MIT presidential: only download raw Dataverse files
npm run data:import             # MIT presidential: import downloaded file into MySQL
npm run data:validate           # MIT presidential: validate normalized import
npm run data:generate           # MIT presidential: rebuild frontend JSON from MySQL
npm run data:normalize          # merge known renamed/superseded county rows in generated JSON
npm run data:coverage           # rebuild national county coverage report from generated JSON
npm run data:official:ga        # replace GA 2020 county rows with official Georgia recount data
npm run data:official:ky        # replace KY 2020 county rows with official Kentucky certified PDF data
npm run data:official:nc        # replace NC 2020/2024 county rows with official NCSBE data
npm run data:official:va        # replace VA 2020/2024 locality rows with official Virginia data
npm run data:official:wi        # replace WI 2024 county rows with official Wisconsin canvass PDF data
npm run data:supplement         # fill missing 2020/2024 county rows from supplemental CSVs
npm run check:official          # compare official state source files against generated JSON rows
npm run virginia:check          # validate Virginia federal contest totals and coverage
npm run kentucky:check          # validate Kentucky contest totals and contributing report counts
npm run kentucky:recaps:ocr     # OCR selected image-only Kentucky recap PDFs (requires tesseract)
npm run kentucky:certified:download # stage Kentucky certified statewide reference PDFs
npm run sources:report          # validate source registry and write docs/source-registry-report.md
npm run coverage:national       # rebuild the 50-state federal/state coverage matrix
npm run florida:fetch           # Florida 2012-2024: download/import/validate/generate
npm run florida:import:year -- 2022
npm run florida:validate:year -- 2022
npm run florida:generate:year -- 2022
npm run florida:geometry:fetch    # Florida 2022 district geometry GeoJSON and metadata
npm run florida:districts:generate # Florida 2022/2024 district drilldown bundles
npm run florida:mayors:generate # Florida municipal mayor summaries
npm run california:fetch        # California 2020/2022/2024 statewide and district contest summaries
npm run california:geometry:fetch # California 2022 district geometry GeoJSON and metadata
npm run california:districts:generate # California 2022/2024 district drilldown bundle
npm run california:all          # California contests, geometry, and district drilldown
npm run pennsylvania:fetch      # Pennsylvania 2020/2022/2024 official precinct returns summary
npm run ohio:generate           # Ohio 2020/2022/2024 official statewide and district contest summaries
npm run texas:generate          # Texas 2018 plus 2020/2022/2024 county canvass summaries
npm run texas:current:generate  # Texas SOS current statewide-only summary
npm run texas:mayors:generate   # Texas official municipal mayor summaries
npm run db:apply                # apply MySQL schema and seed data
npm run lint                    # type-check the frontend
npm test                        # run DB-free Python unit tests
npm run check                   # type-check, unit-test, compile scripts, and validate generated JSON plus official state batches
npm run build                   # production build
```

## Documentation

- [Project plan](docs/project-plan.md)
- [Data collection plan](docs/data-collection-plan.md)
- [MySQL schema plan](docs/mysql-schema-plan.md)
- [Handoff and next steps](docs/handoff.md)
- [Pilot source registry](docs/sources/README.md)

## Repository Notes

This directory is its own GitHub repository. The remote is `https://github.com/aboxfulloftide/election.git`.

Do not commit `.env` or `data/raw/`. Both are ignored by git.
