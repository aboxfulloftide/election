# Wisconsin Sources

## Statewide General Election Results

Source: Wisconsin Elections Commission.

- Homepage: `https://elections.wi.gov/`
- 2024 county-by-county presidential canvass PDF: `https://elections.wi.gov/sites/default/files/documents/County%20by%20County%20Report_POTUS.pdf`

The project parses the official 2024 county-by-county presidential canvass PDF with `pdftotext -layout` and imports all Wisconsin county rows. Because the source is an official PDF instead of structured CSV/JSON, imported rows are marked quality grade `B`.

Implemented commands:

```bash
npm run data:official:wi:download
npm run data:official:wi:merge
npm run data:official:wi
```

Current coverage:

- 2024: all 72 Wisconsin counties matched and replaced.
- The 2020-2024 federal/state contest cohort remains in progress; the 2024 presidential PDF is not sufficient to mark the full cohort imported.

Rows written to `public/results/county-presidential-summary.json` are marked with `official: true`, Wisconsin Elections Commission source metadata, and quality grade `B`.
