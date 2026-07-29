# Georgia Sources

## Statewide General Election Results

Source: Georgia Secretary of State historical election results.

- Landing page: `https://sos.ga.gov/page/historical-elections-results`
- 2020 general election recount ZIP: `https://sos.ga.gov/sites/default/files/2026-04/november_3_2020_-_general_election_recount.zip`
- 2020 general election full ZIP: `https://sos.ga.gov/sites/default/files/2026-04/november_3_2020_-_general_election.zip`

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

Rows written to `public/results/county-presidential-summary.json` are marked with `official: true`, Georgia Secretary of State source metadata, and quality grade `A`.
