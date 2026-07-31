# National Cohort 01

## Scope

The first bulk backfill window covers 2020, 2022, and 2024 for ten states and the six active federal/state office families:

- President
- U.S. Senate
- U.S. House
- Governor
- State Senate
- State House/Assembly

The cohort excludes city and municipal offices.

Machine-readable tracking lives in `data/national-cohorts/cohort-01-2020-2024.json`.
Raw-file availability is reported by `npm run national:cohort:preflight` in [`docs/national-cohort-01-preflight.md`](national-cohort-01-preflight.md).

## State Status

| State | Status | Next action |
| --- | --- | --- |
| Florida | Imported | Maintain regression coverage |
| California | Imported | Resolve remaining 2020-2024 gaps |
| Pennsylvania | Imported | Maintain regression coverage |
| Texas | Imported | Maintain regression coverage |
| Ohio | Imported | Maintain regression coverage |
| Georgia | In progress | Extend beyond the staged 2020 presidential source into full 2020-2024 federal/state imports |
| North Carolina | Imported | Maintain 557 normalized 2020-2024 federal/state contests and resolve remaining applicability metadata |
| Virginia | Federal contests imported; state-office lane open | State-office elections are generally odd-year; record applicability and complete any applicable cohort cells |
| Wisconsin | In progress | Extend beyond the staged 2024 presidential canvass into full 2020-2024 federal/state imports |
| Kentucky | In progress | Promote validated state legislative contests and complete applicable 2020-2024 cells |

## Completion Rule

A state moves to `imported` only after all applicable 2020-2024 state/year/office cells have generated normalized output, source references, reconciliation checks, and regression coverage. Offices not scheduled for a state/year must be recorded as not on the ballot; source discovery alone does not count as imported.

## Commands

```bash
npm run coverage:national
npm run national:cohort:preflight
npm run national:cohort:check
npm run sources:check
npm run check
npm run build
```
