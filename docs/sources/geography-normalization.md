# County Presidential Geography Normalization

The MIT county presidential file can contain separate rows for geographies that were renamed, re-coded, or retired across the 2000-2024 range. The generated app summary normalizes known cases so year-to-year comparison cards do not show avoidable missing rows.

Implemented command:

```bash
npm run data:normalize
```

`npm run data:fetch` runs this command immediately after generating `public/results/county-presidential-summary.json`.

## Current Rules

- Missouri `36000` Kansas City is merged into the existing `2938000` Kansas City comparison row. MIT uses `2938000` through 2020 and `36000` in 2024.
- South Dakota `46113` Shannon is merged into `46102` Oglala Lakota. This preserves historical Shannon results and current Oglala Lakota results in one comparison row.
- Virginia `51515` Bedford City is marked inactive after 2012. It remains in the summary for historical results but is excluded from modern coverage denominators.

## Source Notes

- Missouri Secretary of State election results page: `https://www.sos.mo.gov/elections/s_default`
- South Dakota 2020 election history page: `https://sdsos.gov/elections-voting/election-resources/election-history/2020_Election_History.aspx`
- South Dakota 2020 official state canvass PDF: `https://sdsos.gov/elections-voting/assets/Archive/2020%20Assests/2020GeneralStateCanvassFinal%26Certificate.pdf`
- South Dakota 2024 election history page: `https://sdsos.gov/elections-voting/election-resources/election-history/2024_Election_History.aspx`
- South Dakota 2024 official state canvass PDF: `https://sdsos.gov/elections-voting/assets/Archive/2024%20Assets/Recount-Canvass-and-Canvass-Docs-General/2024GeneralElectionCanvassWithCert.pdf`
- Town of Bedford charter: `https://law.lis.virginia.gov/charters/bedford/`

The South Dakota state canvass PDFs list Oglala Lakota in the presidential county tables for 2020 and 2024. The Bedford charter states the Town of Bedford Charter of 2013 became effective July 1, 2013, so Bedford City is not treated as a separate reporting geography for later presidential elections.
