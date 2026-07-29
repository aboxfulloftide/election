# Kentucky Sources

## Statewide General Election Results

Source: Kentucky State Board of Elections.

- 2020 result page: `https://elect.ky.gov/results/2020-2029/Pages/2020.aspx`
- 2020 certified general election PDF: `https://elect.ky.gov/results/2020-2029/Documents/2020%20General%20Election%20Results.pdf`

The project parses the official certified 2020 general election PDF with `pdftotext -raw` and imports the presidential county rows. Because the source is an official PDF instead of structured CSV/JSON, imported rows are marked quality grade `B`.

Implemented commands:

```bash
npm run data:official:ky:download
npm run data:official:ky:merge
npm run data:official:ky
```

Current coverage:

- 2020: all 120 Kentucky counties matched and replaced.

Rows written to `public/results/county-presidential-summary.json` are marked with `official: true`, Kentucky State Board of Elections source metadata, and quality grade `B`.
