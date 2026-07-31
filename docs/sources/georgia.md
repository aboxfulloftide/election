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
- 2024: 251 official contest totals normalized by `npm run georgia:2024:generate`: President, 14 U.S. House, 56 State Senate, and 180 State House contests. The PDF has no regular U.S. Senate contest for this year.
- 2020: 253 official contest totals are normalized by `npm run georgia:2020:generate`: President, regular and special U.S. Senate, 14 U.S. House, 56 State Senate, and 180 State House contests. Georgia had no regular Governor contest in 2020.
- The 2020-2024 cohort is not complete until the remaining 2020 Governor applicability/source lane is recorded and the state batch is reconciled.

The 2022 normalized artifact is `public/results/georgia-2022-official-contests.json`. It is kept separate from the county-presidential merger because the 2022 archive contains many non-presidential contest names.

The 2024 normalized artifact is `public/results/georgia-2024-official-contests.json`. It uses the PDF's audit count, preserves negative audit differences only as source parsing input, and retains the official candidate total for each contest.

Rows written to `public/results/county-presidential-summary.json` are marked with `official: true`, Georgia Secretary of State source metadata, and quality grade `A`.
