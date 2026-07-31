# Source Registry

This directory is the machine-readable backlog for bulk data collection.

Each state file contains registry entries with:

- `id`: stable unique source id.
- `state_po`: two-letter state abbreviation.
- `scope`: result family, such as `statewide`, `district`, `geometry`, `mayor`, or `precinct`.
- `offices`: target offices covered by the source family.
- `years`: imported or explicitly targeted years.
- `status`: `imported`, `source_identified`, `needs_discovery`, or `blocked`.
- `format`: source format or parser family.
- `geography`: best expected reporting geography.
- `urls`: official source pages or files.
- `parser`: existing or planned parser family.

Use:

```bash
npm run sources:report
```

The report validates the registry and writes `docs/source-registry-report.md`.
