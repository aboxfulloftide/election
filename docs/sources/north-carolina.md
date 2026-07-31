# North Carolina Sources

## Statewide General Election Results

Source: North Carolina State Board of Elections historical election results data.

- Landing page: `https://www.ncsbe.gov/results-data/election-results/historical-election-results-data`
- 2020 general results ZIP: `https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2020_11_03/results_pct_20201103.zip`
- 2024 general results ZIP: `https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2024_11_05/results_pct_20241105.zip`

The NCSBE page states that election result files provide vote counts for each choice per contest, with vote counts broken down by county, precinct, and voting method. The project aggregates `US PRESIDENT` rows from the precinct-level results file to county presidential totals. The statewide importer also aggregates the six active federal/state office families into `public/results/north-carolina-statewide-summary.json`, excluding local, judicial, and referendum contests.

Implemented commands:

```bash
npm run data:official:nc:download
npm run data:official:nc:merge
npm run data:official:nc
```

Current coverage:

- 2020: all 100 North Carolina counties matched and replaced.
- 2024: all 100 North Carolina counties matched and replaced.
- 2020: 186 federal/state contests normalized.
- 2024: 186 federal/state contests normalized. The 2024 source has no U.S. Senate contest because that office was not on the ballot in that cycle.

Rows written to `public/results/county-presidential-summary.json` are marked with `official: true`, NCSBE source metadata, and quality grade `A`.
