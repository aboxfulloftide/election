# Georgia Sources

## Statewide General Election Results

Source: Georgia Secretary of State historical election results.

- Landing page: `https://sos.ga.gov/page/historical-elections-results`
- 2020 general election recount ZIP: `https://sos.ga.gov/sites/default/files/2026-04/november_3_2020_-_general_election_recount.zip`
- 2022 general/special election ZIP: `https://sos.ga.gov/sites/default/files/2026-05/November%208%2C%202022%20-%20General-Special%20Election.zip`
- 2020 general election full ZIP: `https://sos.ga.gov/sites/default/files/2026-04/november_3_2020_-_general_election.zip`
- 2024 official contest comparison PDF: `https://sos.ga.gov/sites/default/files/2024-11/contest_results_comparison_with_jurisdiction_details_0.pdf`

The Secretary of State historical results page lists precinct and summary-level results from 2012 to 2024. The project currently uses the 2020 general-election recount ZIP as the official presidential county source because its nested `summary.csv` files contain county-level presidential recount totals.

Georgia's site may block scripted downloads. If `npm run data:official:ga:download` cannot download the file directly, download the recount ZIP in a browser and place `november_3_2020_-_general_election_recount.zip` in the project root or `data/raw/official/georgia/`.

Implemented commands:

```bash
npm run data:official:ga:download
npm run data:official:ga:merge
npm run data:official:ga
```

Current coverage:

- 2020: all 159 Georgia counties matched and replaced from official recount summary files.
- 2022: 159 county summary ZIPs normalized into 252 official Governor, U.S. Senate, U.S. House, State Senate, and State House contests by `npm run georgia:2022:generate`.
- 2024: official contest-comparison PDF staged by `npm run georgia:2024:stage`; a separate PDF/table parser is still required before import.
- 2020 and 2024 remain source-identified lanes; the 2020-2024 cohort is not complete until all six target offices are normalized for both years.

The 2022 normalized artifact is `public/results/georgia-2022-official-contests.json`. It is kept separate from the county-presidential merger because the 2022 archive contains many non-presidential contest names.

Rows written to `public/results/county-presidential-summary.json` are marked with `official: true`, Georgia Secretary of State source metadata, and quality grade `A`.
