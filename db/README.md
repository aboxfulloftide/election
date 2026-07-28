# Database

The project uses the local MySQL server as the normalized election-data store.

## Local Connection

Database connection details live in `.env`, which is ignored by git.

The helper script supports either format:

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=election
DB_PASSWORD=...
DB_NAME=election
```

or:

```text
host:localhost
port:3306
user:election
pass:...
db:election
```

## Apply Schema and Seeds

```bash
bash scripts/db_apply.sh
```

The script:

1. Reads `.env`.
2. Creates the database if it does not exist.
3. Applies SQL files in `db/migrations/`.
4. Applies SQL files in `db/seeds/`.

Migrations are written to be safe to rerun.

## Current Tables

Core normalized tables:

- `sources`
- `source_files`
- `elections`
- `jurisdictions`
- `offices`
- `parties`
- `candidates`
- `contests`
- `contest_candidates`
- `reporting_units`
- `results`
- `data_quality_notes`

Support tables:

- `migration_versions`

## Pipeline Direction

The intended flow is:

```text
raw source file -> importer -> MySQL -> validation -> generated frontend JSON
```

The current frontend summary file is regenerated from MySQL with:

```bash
npm run data:fetch
```
