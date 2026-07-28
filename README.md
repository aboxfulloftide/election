# Election Night Map

Interactive U.S. election-night map for comparing historical election results across election cycles.

## Current Scope

- County-level presidential general election results from 2000 through 2024.
- Florida official precinct-level statewide general election results from 2012 through 2024 for President, U.S. Senate, and Governor where those offices were on the ballot.
- A React/Vite map UI with national totals, county hover/click details, year selection, and election-to-election margin shift.
- Repeatable Python ingestion scripts that download raw files, import MySQL, validate normalized rows, and build app-ready JSON.

## Data Source

The first dataset is MIT Election Data and Science Lab, "County Presidential Election Returns 2000-2024", Harvard Dataverse DOI `10.7910/DVN/VOQCHQ`.

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
npm run dev
```

## Useful Commands

```bash
npm run data:fetch   # download Dataverse files, import MySQL, and rebuild public/results/county-presidential-summary.json
npm run data:download # only download raw Dataverse files
npm run data:import  # import the downloaded MIT county presidential file into MySQL
npm run data:validate # validate the normalized MIT presidential import
npm run data:generate # rebuild frontend JSON from MySQL
npm run florida:fetch # download/import/validate/generate configured Florida 2012-2024 statewide precinct data
npm run florida:import:year -- 2022 # import one configured Florida year
npm run db:apply     # apply MySQL schema and seed data
npm run lint         # type-check the frontend
npm run build        # production build
```

## Repository Notes

This directory is intended to be its own GitHub repository. The local git repo can be initialized with:

```bash
git init
git add .
git commit -m "Initial election night map scaffold"
```
