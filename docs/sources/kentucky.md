# Kentucky Sources

## Statewide General Election Results

Source: Kentucky State Board of Elections.

- 2020 result page: `https://elect.ky.gov/results/2020-2029/Pages/2020.aspx`
- 2020 certified general election PDF: `https://elect.ky.gov/results/2020-2029/Documents/2020%20General%20Election%20Results.pdf`

The official 2022 and 2024 recap pages expose county reports for the full election:

- 2022 recap page: `https://elect.ky.gov/results/2020-2029/Pages/2022-General-Recap-Sheets.aspx`
- 2024 recap page: `https://elect.ky.gov/results/2020-2029/Pages/2024General-Recap-Sheets.aspx`

The project parses the official certified 2020 general election PDF with `pdftotext -raw` and imports the presidential county rows. Because the source is an official PDF instead of structured CSV/JSON, imported rows are marked quality grade `B`.

Implemented commands:

```bash
npm run data:official:ky:download
npm run data:official:ky:merge
npm run data:official:ky
npm run kentucky:certified:download -- --year 2022
npm run kentucky:certified:ocr
npm run kentucky:certified:parse
npm run kentucky:recaps:download
npm run kentucky:recaps:ocr -- --year 2022 --file 2022_Allen_County.pdf
npm run kentucky:generate
npm run kentucky:check
```

Current coverage:

- 2020: all 120 Kentucky counties matched and replaced.
- 2022: 118 county recap PDFs staged, but only 51 have usable text layers; 67 are blank and the official Butler County link currently returns HTTP 404.
- 2024: all 120 county recap PDFs staged; 118 have usable text layers, one is blank (Elliott), and one is mail-in-only (Magoffin).

The 2022 and 2024 recap PDFs are precinct-level reports. The parser now handles the county recap, precinct-summary, wrapped-ticket, and write-in layouts. Each generated contest records the number of county reports that actually contributed to that contest; this varies by district instead of being reported as the full statewide file count. The generated statewide output remains `partial` until every county/contest total reconciles against an independent official check.

The schema audit also records raw-file quality. The staged 2024 archive currently includes a blank Elliott County PDF and a Magoffin County PDF containing only a Mail In column, so those files cannot support a complete county total without replacement or an official statewide reference.

The 2022 official results page also links `1.17.2023 Certified General Election Results.pdf`, a 258-page image-only statewide county table. It is staged by `kentucky:certified:download` as the independent reconciliation source. The OCR-backed Senate diagnostic now finds all 120 counties and matches the printed Republican and Democratic totals; write-in columns and other offices still require validation before any values can replace the partial recap-derived summary.

The certified PDF is image-only. Run `kentucky:certified:ocr` on a machine with `ocrmypdf` and `pdftotext` installed; it creates an ignored searchable PDF and layout-preserving text file. Then `kentucky:certified:parse` emits a diagnostic U.S. Senate county-table extraction under the ignored raw-data directory, including the parsed row count, summed columns, and the source's printed `Total Votes` line. It is intentionally not merged into the published summary until OCR values reconcile independently.

For image-only 2022 reports, `npm run kentucky:recaps:ocr -- --year 2022 --limit N` stages OCR text under the ignored raw-data directory using a 100-DPI, resumable pass and Tesseract page-segmentation mode 4. Use `--psm 6` for precinct-style pages when needed. The generator and schema audit automatically use staged OCR text when present. OCR output still needs layout-specific normalization for recap-sheet scans, so OCR-derived rows are not promoted automatically.

Rows written to `public/results/county-presidential-summary.json` are marked with `official: true`, Kentucky State Board of Elections source metadata, and quality grade `B`.
