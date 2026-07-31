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
- Miami-Dade official 2012 and 2014/2015 precinct geometry pilot layers are generated under `public/results/geometry/` with `public/results/florida-precinct-geometry-layers.json`.
- Miami-Dade 2012 and 2014 precinct result bundles are generated under `public/results/precincts/` and normalize legacy/split precinct identifiers.
- California 2018, 2020, 2022, and 2024 Statement of Vote summaries include statewide and district contests.
- California 2022 redistricting-cycle district geometry and the 2022/2024 California district/county drilldown bundle are generated under `public/results/`.
- Florida municipal mayor summaries for configured Miami-Dade cities, Tampa, Jacksonville, and Orlando are generated under `public/results/`.
- Pennsylvania 2020, 2022, and 2024 official general-election precinct returns are generated under `public/results/`.
- Texas 2018 official Secretary of State historical race/county canvass summaries are generated under `public/results/`.
- Texas Fort Worth, San Antonio, Houston, Austin, and Dallas official municipal mayor summaries are generated under `public/results/`.
- Frontend supports national presidential mode with country/state/county comparison cards, scalable official-state selection, official county maps, and Florida/California district map modes.

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
npm run california:all
npm run florida:mayors:generate
npm run pennsylvania:fetch
npm run texas:generate
npm run texas:mayors:generate
npm run sources:report
npm run build
```

Expected high-level results:

- MIT validation passes for county presidential data.
- Florida validation passes for 2012, 2014, 2016, 2018, 2020, 2022, and 2024.
- Florida geometry registration validates the three 2022 district shapefile/block-equivalency pairs and writes `public/results/florida-geometry-layers.json` plus district GeoJSON files under `public/results/geometry/`.
- California Statement of Vote generation writes 619 contests across 2018, 2020, 2022, and 2024, California geometry generation writes 52 congressional, 40 State Senate, and 80 State Assembly features, and California district drilldown links 304 district contests for 2022/2024 only.
- Florida mayor generation writes seventeen municipal mayor contests across Miami-Dade cities, Tampa, Jacksonville, and Orlando.
- Pennsylvania generation writes 741 contests across 2020, 2022, and 2024.
- Ohio generation writes 397 contests across 2020, 2022, and 2024 from browser-supplied official SOS workbooks.
- Texas generation writes 764 contests: 2018 statewide/district contests plus 2020/2022/2024 PDF-derived statewide and district contests.
- Texas current generation writes 30 statewide-only May 26, 2026 primary runoff contests from SOS public HTML.
- Texas mayor generation writes 65 contests: 10 Fort Worth mayor contests from 2007 through 2025, San Antonio mayor contests from 1999 through 2025, Houston 1999, 2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2019, and 2023 mayor contests, Austin 2022/2024 mayor contests, and Dallas 1981 through 1999, 2002, 2007, 2011, 2015, 2019, and 2023 mayor contests.
- Texas mayor source downloads, PDF text, and OCR text are cached under ignored `data/raw/official/texas/mayors/`; delete that directory when a clean re-download/re-OCR is required.
- Source registry report writes `docs/source-registry-report.md`.
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

## Next Work Option A: National Federal/State Backfill

The active target is now the 4,200-cell matrix in `public/results/national-coverage-matrix.json`: 50 states, even-year general elections from 2000 through 2026, and President, U.S. Senate, U.S. House, Governor, State Senate, and State House/Assembly. Municipal datasets remain archived and are not part of this work.

The execution backlog for the national work is documented in `docs/national-execution-backlog.md`. The active batch is Kentucky completion plus the Georgia, North Carolina, Virginia, and Wisconsin 2020-2024 cohort. Georgia 2020, 2022, and 2024 are normalized into separate generated contest artifacts. Kentucky's 119 certified 2022 legislative contests are promoted and audited; Virginia's 2020/2024 federal contests are imported with odd-year state-office applicability recorded; Wisconsin remains source-identified because direct WEC archive access is challenged. Run `npm run national:cohort:preflight` to see raw-source and generated-artifact availability for every state/year batch.

The legacy waves are now operationally partitioned into five ten-state cohorts each. `npm run legacy:status` reports explicit source-backed coverage, while `npm run legacy:cohorts` regenerates the cohort plans.

The first legacy cohort (`AL, AK, AZ, AR, CO, CT, DE, HI, ID, IL`) now has year-level official source records for 2000–2008 and 2010–2018. Run `npm run legacy:sources` to regenerate them and review `docs/sources/legacy-cohort-01.md`; these records are source-identified only until files are staged and reconciled.

Acquisition has started for the structured lanes. `npm run legacy:acquisition:audit` reports the staged-file boundary: Delaware 2018, Idaho 2014/2016/2018, and Illinois 2018 currently pass the format audit. Idaho portal shells for 2000–2012 and a rejected Delaware 2010 response are retained as invalid audit evidence and must not be parsed.

Use [national-backfill-plan.md](national-backfill-plan.md) for the batch contract and wave order. The first execution batch is ten states for 2020-2024, followed by the remaining four cohorts before older years.

## Next Work Option B: Expand Florida Precinct Geometry

Goal:

- Expand map-ready county/year precinct geometry joins beyond the Miami-Dade pilot.

Why next:

- Florida district maps now draw for 2022-cycle congressional, State Senate, and State House contests. Precinct-aware views still need official county/year precinct geometry.
- Miami-Dade is the first precinct-geometry pilot: official 2012 and 2014/2015 shapefiles are converted to WGS84 and merged by precinct.
- Miami-Dade 2012 and 2014 precinct result bundles now join the normalized Florida database results to those geometry vintages; some historical result IDs remain unmatched and are retained in the bundles.
- The Florida official UI now loads those bundles for 2012 and 2014, renders the WGS84 precinct map, supports contest selection and precinct hover/click details, and links the official source.
- Broward County official ArcGIS precinct layers for 2020, 2022, and 2024 are now normalized and appended to the shared geometry manifest. Broward 2020 and 2024 join all result precinct IDs and are available in the UI. Broward 2022 is bundled for auditability, but all 355 result IDs remain unmatched because the result namespace is numeric and the available boundary namespace is lettered.
- Precinct bundle discovery is now manifest-driven through `public/results/florida-precinct-catalog.json`; map readiness is derived from validated join counts instead of hardcoded frontend URLs.
- `npm run florida:precinct:preflight` audits match rates and enforces the federal/state-only office scope; `--require-complete` is available for strict publication checks. Geometry payload sizes are recorded in the manifest and shown in precinct details.
- `npm run florida:precinct:all` rebuilds the state/federal precinct geometry, result bundles, catalog, and downloadable join report in one pass.

Likely tasks:

1. Reconcile Broward 2022 numeric result IDs with a compatible historical boundary vintage or official crosswalk.
2. Measure the generated GeoJSON size as coverage grows and move to county-partitioned or vector-tile delivery if needed.
3. Extend the same result/geometry join and UI path beyond Miami-Dade, preserving unmatched identifiers for auditability.
4. Add richer precinct analytics, such as closest-race sorting and a visible unmatched-join count.

Risks:

- Precinct boundaries change frequently.
- State legislative and congressional district boundaries change after redistricting.
- Official district labels must remain tied to election year.

## Next Work Option B: Florida Mayors

Goal:

- Backfill additional mayor years where official county/city archives expose structured results.

Completed first target:

- Miami-Dade Supervisor of Elections archived ENR pages for configured 2021 and 2023 mayor contests.
- Hillsborough Supervisor of Elections archived ENR pages for Tampa 2015, 2019, and 2023 mayor contests.
- Duval Supervisor of Elections archived ENR pages for Jacksonville 2015, 2019, and 2023 mayor contests.
- Orange County Supervisor of Elections ENR page for the 2023 Orlando mayor contest.

Likely tasks:

1. Inspect older Orange/Orlando result archives and other major-city archives for structured mayor contest pages or reports.
2. Decide initial geography: citywide, precinct, or precinct-like.
3. Add city contest parsing without forcing partisan labels.
4. Validate citywide totals and source files.
5. Generate mayor summary JSON.

Risks:

- Municipal elections may be nonpartisan.
- Runoffs may determine the winner.
- City boundaries do not always align cleanly with county precinct files.

## Next Work Option C: Texas Mayor Backfill

Goal:

- Continue official Texas mayor imports from reachable county and city archives.

Recommended first target:

- Remaining Houston years, then older San Antonio years.

Likely tasks:

1. Identify official city or county election-result archives with stable files.
2. Add source entries under `data/source-registry/texas.json`.
3. Extend `scripts/generate_texas_mayor_summary.py` and tests for each source format.
4. Connect imported Texas years to generated JSON validation.
5. Update the source registry, docs, and generated JSON validation for each imported batch.

Risks:

- XLSX sheet layouts may vary by office and year.
- California uses top-two general election behavior.
- District/county breakdowns need careful normalization.
- State Senate districts phase in over two election cycles.
- Texas 2019-2024 official results are on a modern portal that returns a Cloudflare challenge to direct non-browser requests.
- Texas 2025-current Civix app APIs return `401 Bearer`; only the public `electionresults.sos.state.tx.us/results.html` page is currently reachable without authentication.
- Ohio data portal, direct XLSX guesses, and sampled county ENR URLs currently return the Ohio Secretary of State maintenance page with HTTP 403. Browser-supplied 2020, 2022, and 2024 statewide workbooks are imported.

## Current Recommended Order

1. Continue structured mayor archives for remaining Houston years and older San Antonio years, starting with whichever archive exposes HTML/CSV/XLSX before PDF-only reports.
2. Continue official Texas mayor backfill with remaining Houston years.
3. County/year precinct geometry and precinct results, if the next priority is precinct-aware state drilldown.
4. Richer frontend drilldown behavior once the underlying precinct geography exists.
