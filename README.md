# Election Night Map

Interactive U.S. election-night map for comparing historical election results across election cycles.

## Current Scope

- County-level presidential general election results from 2000 through 2024.
- Florida official precinct-level general election results from 2012 through 2024 for President, U.S. Senate, U.S. House, Governor, State Senate, and State House where those offices were on the ballot.
- California official 2024 Statement of Vote summaries for President, U.S. Senate, U.S. House, State Senate, and State Assembly.
- Florida official 2022 redistricting-cycle district geometry for congressional, State Senate, and State House map layers.
- Florida 2022 and 2024 district/county drilldown bundles for geometry-linked district contests.
- A React/Vite map UI with national totals, country/state/county comparison cards, year selection, election-to-election margin shift, Florida county maps for official statewide/non-presidential contests, and Florida 2022/2024 district contest maps with winner/shift modes.
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
- California Secretary of State 2024 Statement of Vote XLSX files for President, U.S. Senate, U.S. House, State Senate, and State Assembly.

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
npm run florida:fetch           # Florida 2012-2024: download/import/validate/generate
npm run florida:import:year -- 2022
npm run florida:validate:year -- 2022
npm run florida:generate:year -- 2022
npm run florida:geometry:fetch    # Florida 2022 district geometry GeoJSON and metadata
npm run florida:districts:generate # Florida 2022/2024 district drilldown bundles
npm run california:fetch        # California 2024 statewide and district contest summaries
npm run db:apply                # apply MySQL schema and seed data
npm run lint                    # type-check the frontend
npm test                        # run DB-free Python unit tests
npm run check                   # type-check, unit-test, compile scripts, and validate generated JSON
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
