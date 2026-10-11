# MISPTool

A lightweight triage layer for MISP.

The goal is to give blue-team users a simpler interface than the default MISP UI: show the events that matter, explain their basic context, and keep the full MISP event one click away.

## Current features

- Polls MISP for recent events.
- Scores events using configurable rules.
- Detects changed events using fingerprints.
- Classifies changes as `new`, `updated`, or `enriched`.
- Sends terminal and Discord webhook notifications.
- Stores event state in either local JSON or PostgreSQL.
- Exposes a FastAPI JSON API.
- Provides a React/Vite frontend with:
  - event triage table
  - inline event detail expansion
  - manual refresh
  - 60-second auto-refresh
  - refresh countdown
  - light/dark theme toggle
  - direct “Open in MISP” links
- Supports MISP galaxy helper commands.

## Architecture

```text
React frontend
  -> FastAPI API
    -> application services / ports
      -> PostgreSQL or JSON repository
      -> MISP client
      -> notifier
```

Important directories:

```text
src/misptool/
  api/                 FastAPI app, routes, schemas, response presenters
  application/         Event processor, filters, ports/interfaces, CLI commands
  domain/              Scoring and event snapshot logic
  infrastructure/      DB, filesystem, MISP, notification implementations

frontend/
  src/                 React TypeScript frontend

alembic/
  versions/            Database migrations

tests/
```

## Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy and edit the config:

```bash
cp config.example.yaml config.yaml
```

For PostgreSQL storage:

```yaml
storage:
  backend: "postgres"
  database_url_env: "MISP_DB_URL"
```

Export the database URL:

```bash
export MISP_DB_URL='postgresql+psycopg://user:password@host:5432/misptool'
```

Do not commit `config.yaml`, `.env`, database URLs, MISP API keys, or Discord webhooks.

## Database migrations

```bash
.venv/bin/alembic upgrade head
```

If your database password contains `%`, URL-encode it as `%25` in `MISP_DB_URL`.

## CLI usage

```bash
.venv/bin/python3 main.py --config config.yaml <command>
```

Available commands:

```text
test-connection
test-storage
test-scorer
run-once
run
migrate-state
import-cluster
import-all
list-galaxies
create-galaxy
ensure-galaxies
export-events
```

Run one processing cycle:

```bash
.venv/bin/python3 main.py --config config.yaml run-once
```

Run continuously:

```bash
.venv/bin/python3 main.py --config config.yaml run
```

Migrate old JSON state into PostgreSQL:

```bash
.venv/bin/python3 main.py --config config.yaml migrate-state --input state.json
```

## FastAPI backend

Start the API:

```bash
.venv/bin/uvicorn src.misptool.api.app:app --reload
```

Useful endpoints:

```text
GET /health
GET /events
GET /events/{event_id}
```

Supported event query parameters:

```text
limit
min_score
from_date
to_date
published
```

Example:

```text
http://localhost:8000/events?min_score=5&published=true&limit=25
```

FastAPI docs:

```text
http://localhost:8000/docs
```

## React frontend

```bash
cd frontend
npm install
npm run dev
```

By default, the frontend expects the API at:

```text
http://localhost:8000
```

You can override this with:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

Build:

```bash
npm run build
```

## Tests

Run Python tests:

```bash
.venv/bin/python3 -m pytest -q
```

Some PostgreSQL integration tests are skipped unless `MISP_DB_URL` is set.

Run frontend checks:

```bash
cd frontend
npm run build
```

## Galaxy cluster import

Import one cluster JSON file:

```bash
.venv/bin/python3 main.py --config config.yaml import-cluster cluster.json
```

Import all cluster JSON files from a folder:

```bash
.venv/bin/python3 main.py --config config.yaml import-all clusters/
```

Expected cluster fields include:

- `value`
- `type`
- `description`

Optional fields can include:

- `source`
- `authors`
- `distribution`
- `GalaxyElement`

