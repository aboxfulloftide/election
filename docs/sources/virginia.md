# Virginia Sources

## Statewide General Election Results

Source: Virginia Department of Elections historical election results.

- Landing page: `https://historical.elections.virginia.gov/`
- 2020 presidential contest page: `https://historical.elections.virginia.gov/contest/144567`
- 2020 results CSV: `https://va2.elstats3.civera.com/api/download_contest/144567_table.csv?split_party=false`
- 2024 presidential contest page: `https://historical.elections.virginia.gov/contest/161256`
- 2024 results CSV: `https://va2.elstats3.civera.com/api/download_contest/161256_table.csv?split_party=false`

The historical election pages expose contest-specific CSV downloads. The project imports `Locality` rows from those CSVs, maps party labels to the normalized presidential party buckets, and preserves independent and write-in votes as `OTHER`.

The official contest inventory now records verified 2020 and 2024 President, U.S. Senate, and all 11 U.S. House district pages in `public/results/virginia-official-contest-inventory.json`. Download those CSVs with:

```bash
npm run virginia:inventory -- --year 2020 --start 144560 --end 144580
npm run virginia:inventory -- --year 2024 --start 161250 --end 161400
npm run virginia:download
npm run virginia:generate
npm run virginia:check
```

The generated federal summary is `public/results/virginia-statewide-summary.json` with 26 contests. State legislative offices require separate odd-year election coverage and are not represented by the current even-year federal inventory; the 2020, 2022, and 2024 even-year lanes are therefore recorded as not applicable for this cohort rather than treated as missing downloads.

`npm run virginia:check` verifies that every contest's candidate totals reconcile to total votes, the recorded winner and margin are mathematically correct, contest IDs are unique, and both years contain all 11 U.S. House districts.

Implemented commands:

```bash
npm run data:official:va:download
npm run data:official:va:merge
npm run data:official:va
```

Current coverage:

- 2020: all 133 current Virginia presidential localities matched and replaced.
- 2024: all 133 current Virginia presidential localities matched and replaced.

The historical Bedford City FIPS row remains present for older years only. The official `Bedford County` row maps to county FIPS `51019`, not retired independent-city FIPS `51515`.

Rows written to `public/results/county-presidential-summary.json` are marked with `official: true`, Virginia Department of Elections source metadata, and quality grade `A`.
