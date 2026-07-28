# Data

`npm run data:fetch` downloads the current Harvard Dataverse files into `data/raw/`, imports normalized results into MySQL, and writes the frontend-ready file to:

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
