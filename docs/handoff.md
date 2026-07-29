# Handoff

## Current State

Repository:

- Local path: `/home/matheau/code/election`
- Remote: `https://github.com/aboxfulloftide/election.git`
- Current branch: `main`

Data system:

- MySQL is the normalized source of truth.
- `.env` contains database credentials and must not be committed.
- `data/raw/` contains downloaded source files and must not be committed.
- Generated frontend JSON under `public/results/` is committed.

Implemented datasets:

- MIT county presidential returns, 2000-2024.
- Florida Division of Elections official precinct-level general-election returns, 2012-2024.
- Florida offices imported where on ballot: President, U.S. Senate, U.S. House, Governor, State Senate, State House.
- Current Florida validation: 672,309 normalized result rows, 922 contests, all 67 counties for every configured year, zero duplicate result keys.
- Florida 2022 redistricting-cycle district geometry rows and app-ready GeoJSON for congressional, State Senate, and State House layers.
- Florida 2022 and 2024 district contest summaries include geometry links for U.S. House, State Senate, and State House contests.
- Florida 2022 and 2024 district/county drilldown bundles are generated under `public/results/districts/`.
- Frontend supports national presidential mode with country/state/county comparison cards, plus Florida 2022/2024 district map mode with year, office, district, winner, and shift selectors.

## Standard Start Script

Run these before changing code or data:

```bash
git status --short
git pull --ff-only origin main
npm install
npm run db:apply
```

Do not print `.env` contents. If database connection fails, check that `.env` exists and that the local MySQL server is running.

## Rebuild Script

Use this when you need a fully refreshed local database and generated JSON:

```bash
npm run data:fetch
npm run florida:fetch
npm run florida:geometry:fetch
npm run build
```

Expected high-level results:

- MIT validation passes for county presidential data.
- Florida validation passes for 2012, 2014, 2016, 2018, 2020, 2022, and 2024.
- Florida geometry registration validates the three 2022 district shapefile/block-equivalency pairs and writes `public/results/florida-geometry-layers.json` plus district GeoJSON files under `public/results/geometry/`.
- Build passes. Vite may warn that the bundle is larger than 500 kB; that warning is currently expected.

## Before Commit Script

Run this before committing:

```bash
python3 -m py_compile scripts/*.py
npm run check
npm run build
git ls-files .env data/raw
git status --short --ignored
pgrep -af 'vite|npm run dev|election-night-map|import_florida|download_florida|validate_florida|generate_florida' || true
```

Expected:

- Fast checks pass, including Python compile, TypeScript type-checking, DB-free unit tests, and generated JSON contract checks.
- Build succeeds.
- `git ls-files .env data/raw` prints nothing.
- `.env`, `data/raw/`, `dist/`, `node_modules/`, and `scripts/__pycache__/` may appear only as ignored files.
- No dev server or import process is running. A match for the `pgrep` command itself is acceptable.

## Next Work Option A: Florida Geometry

Goal:

- Add map-ready geometry joins for Florida congressional districts, State Senate districts, State House districts, counties, and precincts.

Why next:

- Florida results now include district contests, but the interface cannot accurately draw district or precinct views until geometry is versioned by election year/redistricting cycle.

Likely tasks:

1. Identify official Florida precinct geometry sources by county and year.
2. Add richer Florida drilldown behavior, such as county highlighting, closest-race panels, and source/quality badges.
3. Identify official Florida precinct geometry sources by county and year.

Risks:

- Precinct boundaries change frequently.
- State legislative and congressional district boundaries change after redistricting.
- Official district labels must remain tied to election year.

## Next Work Option B: Florida Mayors

Goal:

- Import mayor contests for Miami, Jacksonville, Tampa, and Orlando.

Recommended first target:

- Miami, using Miami-Dade Supervisor of Elections archived results.

Likely tasks:

1. Inspect Miami-Dade archived result downloads for mayor contests.
2. Decide initial geography: citywide, precinct, or precinct-like.
3. Add city contest parsing without forcing partisan labels.
4. Validate citywide totals and source files.
5. Generate mayor summary JSON.

Risks:

- Municipal elections may be nonpartisan.
- Runoffs may determine the winner.
- City boundaries do not always align cleanly with county precinct files.

## Next Work Option C: California Statement of Vote

Goal:

- Add the second pilot-state structured import using California Secretary of State Statement of Vote XLSX files.

Recommended first target:

- 2024 general election, starting with U.S. Senate, U.S. House, State Senate, and State Assembly.

Likely tasks:

1. Download and inspect official California Statement of Vote XLSX files.
2. Add source-file registration and checksums.
3. Build a California importer that starts with county and county-by-district totals.
4. Validate contest counts and county coverage.
5. Generate California summary JSON.

Risks:

- XLSX sheet layouts may vary by office and year.
- California uses top-two general election behavior.
- District/county breakdowns need careful normalization.

## Current Recommended Order

1. Florida geometry, if the next priority is interface/map accuracy.
2. Florida mayors, if the next priority is completing Florida scope.
3. California Statement of Vote, if the next priority is proving a second state importer.
4. Frontend contest selector and Florida state drilldown are implemented for 2022/2024 district contests; expand from there.
