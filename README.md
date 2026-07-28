# Election Night Map

Interactive U.S. election-night map for comparing county presidential results across election cycles.

## Current Scope

- County-level presidential general election results from 2000 through 2024.
- A React/Vite map UI with national totals, county hover/click details, year selection, and election-to-election margin shift.
- A repeatable Python ingestion script that downloads MIT Election Data and Science Lab data from Harvard Dataverse and builds the app-ready JSON.

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
