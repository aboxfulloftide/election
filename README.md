# Election Night Map

Interactive U.S. election-night map for comparing historical election results across election cycles.

## Current Scope

- County-level presidential general election results from 2000 through 2024.
- Florida official precinct-level general election results from 2012 through 2024 for President, U.S. Senate, U.S. House, Governor, State Senate, and State House where those offices were on the ballot.
- A React/Vite map UI with national totals, county hover/click details, year selection, and election-to-election margin shift.
- Repeatable Python ingestion scripts that download raw files, import MySQL, validate normalized rows, and build app-ready JSON.
- Planning and handoff docs for continuing data collection before major interface expansion.

## Imported Data

Imported sources:

- MIT Election Data and Science Lab, "County Presidential Election Returns 2000-2024", Harvard Dataverse DOI `10.7910/DVN/VOQCHQ`.
- Florida Division of Elections official precinct-level general-election ZIPs for 2012, 2014, 2016, 2018, 2020, 2022, and 2024.

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
npm run florida:fetch           # Florida 2012-2024: download/import/validate/generate
npm run florida:import:year -- 2022
npm run florida:validate:year -- 2022
npm run florida:generate:year -- 2022
npm run db:apply                # apply MySQL schema and seed data
npm run lint                    # type-check the frontend
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
