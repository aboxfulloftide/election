# Data

`npm run data:fetch` downloads the current Harvard Dataverse files into `data/raw/` and writes the frontend-ready file to:

```text
public/results/county-presidential-summary.json
```

Raw downloads are ignored by git. The generated summary is small enough to commit so the app can run immediately after `npm install`.

