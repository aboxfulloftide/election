# Data

`npm run data:fetch` downloads the current Harvard Dataverse files into `data/raw/`, imports normalized MIT presidential results into MySQL, validates them, and writes the frontend-ready file to:

```text
public/results/county-presidential-summary.json
```

Raw downloads are ignored by git. The generated summary is small enough to commit so the app can run immediately after `npm install`.

Use lower-level commands when debugging the pipeline:

```bash
npm run data:download
npm run data:import
npm run data:generate
```

Florida pilot data is rebuilt with:

```bash
npm run florida:fetch
```

It downloads official Florida Division of Elections precinct-level ZIPs into `data/raw/`, imports normalized results into MySQL, validates them, and writes:

```text
public/results/florida-2012-statewide-summary.json
public/results/florida-2014-statewide-summary.json
public/results/florida-2016-statewide-summary.json
public/results/florida-2018-statewide-summary.json
public/results/florida-2020-statewide-summary.json
public/results/florida-2022-statewide-summary.json
public/results/florida-2024-statewide-summary.json
public/results/florida-statewide-summary.json
```

Raw downloads are ignored by git. Generated summaries are committed.
