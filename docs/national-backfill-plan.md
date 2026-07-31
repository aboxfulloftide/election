# National Federal/State Backfill Plan

## Target

Build a contest-level dataset for all 50 states, even-year general elections from 2000 through 2026, covering President, U.S. Senate, U.S. House, Governor, State Senate, and State House/Assembly.

2026 general-election cells remain `not_yet_available` until results are certified. Current 2026 primary/current data is tracked separately and does not count as a completed general-election cell.

Municipal and city elections remain archived project artifacts but are outside this active backfill.

## Matrix

The target matrix contains 4,200 cells: 50 states x 14 election cycles x 6 office families.

```bash
npm run coverage:national
```

Outputs:

- `public/results/national-coverage-matrix.json`
- `docs/national-coverage-report.md`

Statuses are `imported`, `source_identified`, `needs_discovery`, `blocked`, or `not_yet_available`.

## Batch Contract

Every state/year batch must deliver:

1. Raw source files under ignored `data/raw/`.
2. A source-registry entry with official URLs, years, offices, format, and quality grade.
3. A repeatable parser or importer.
4. Normalized MySQL rows with source-file references.
5. Generated app data under `public/results/`.
6. Candidate, party, total, winner, and margin reconciliation.
7. Geography and district-cycle notes.
8. Focused regression tests.
9. Updated source and handoff documentation.

## Waves

Process all states in each wave before starting the next:

1. 2020-2024: modern structured files, county/district detail, and current geometry.
2. 2010-2018: older structured files and official canvass reports.
3. 2000-2008: legacy formats, PDFs, scans, and validated compiled sources.
4. 2026: current primary/current data now; certified general results after the election.

## Parallel Cohorts

Use five cohorts of roughly ten states: Northeast, Southeast, Midwest, Mountain/Plains, and Pacific/Southwest. Each cohort processes multiple states and years per run. A cohort is complete only when its matrix cells, source entries, tests, and generated outputs are updated together.

## Quality Rules

- Official structured data receives grade A after reconciliation.
- Official PDFs or scans receive grade B after extraction review.
- Reputable compiled data receives grade C and retains its original citation.
- Unresolved or incomplete data receives grade D and remains out of map-ready publication.
- Precinct geometry is optional for historical years; contest totals are the completeness target.
- No city-level office enters the active six-office matrix.

## Execution Commands

```bash
npm run coverage:national
npm run sources:report
npm run check
npm run build
```

The first bulk cohort is ten states for 2020-2024, followed by the remaining four cohorts before 2010-2018 backfill begins.

The active first batch is tracked in [`data/national-cohorts/cohort-01-2020-2024.json`](../data/national-cohorts/cohort-01-2020-2024.json) with a human-readable status page at [`docs/national-cohort-01.md`](national-cohort-01.md). Five pilot states are imported; Georgia now has its 2022 federal/state contest lane normalized, while the remaining Georgia, Wisconsin, and Kentucky lanes continue through source discovery and reconciliation. Virginia's even-year federal lane is imported and its state legislative lanes are generally odd-year applicability cases.

The detailed execution backlog is maintained in [`docs/national-execution-backlog.md`](national-execution-backlog.md). Current work begins with Kentucky completion, the Georgia/North Carolina/Virginia/Wisconsin modern cohort, and the remaining 2020-2024 states.
