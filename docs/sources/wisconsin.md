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
- The next Wisconsin work item is locating the official 2020 and 2022 county/district canvass exports and the 2024 non-presidential canvass exports. The homepage is confirmed as the official source hub, but no additional direct export URLs have been staged yet.
- Direct scripted access to the WEC site currently returns a Cloudflare challenge, so Wisconsin remains source-identified until the official exports are obtained through the browser workflow or a stable public file URL.

The browser staging contract expects the official WEC reports named `Canvass Results for 2020 General Election.pdf`, `Canvass Results for 2022 General Election.pdf`, and `County by County Report 2024 General Election.pdf` in the project root. Run `npm run wisconsin:stage` after staging them; it validates and copies them into ignored `data/raw/official/wisconsin/` paths for the importer.

Rows written to `public/results/county-presidential-summary.json` are marked with `official: true`, Wisconsin Elections Commission source metadata, and quality grade `B`.
