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
| Georgia | Source identified | Download and normalize official files |
| North Carolina | Source identified | Download and normalize official files |
| Virginia | Federal contests imported; state-office lane open | Extend official inventory to applicable state-office election years |
| Wisconsin | Source identified | Download and normalize official files |
| Kentucky | Source identified | Download and normalize official files |

## Completion Rule

A state moves to `imported` only after all 18 state/year/office cells have generated normalized output, source references, reconciliation checks, and regression coverage. Source discovery alone does not count as imported.

## Commands

```bash
npm run coverage:national
npm run national:cohort:preflight
npm run national:cohort:check
npm run sources:check
npm run check
npm run build
```
