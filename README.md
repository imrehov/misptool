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

## Docker Compose

The containerized setup runs four services:

```text
postgres        PostgreSQL database
api             FastAPI backend
worker          EventProcessor polling loop
web             Built React frontend served by nginx
```

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and choose a real PostgreSQL password. If you change the password,
keep `POSTGRES_PASSWORD` and `MISP_DB_URL` in sync.

Make sure `config.yaml` exists:

```bash
cp config.example.yaml config.yaml
```

For Docker Compose, `config.yaml` should use PostgreSQL storage:

```yaml
storage:
  backend: "postgres"
  database_url_env: "MISP_DB_URL"
```

If MISP is running directly on your host machine, containers usually cannot use
`http://localhost` to reach it. Use this in `config.yaml` instead:

```yaml
misp:
  url: "http://host.docker.internal"
```

Build the containers:

```bash
docker compose build
```

Run database migrations:

```bash
docker compose run --rm api alembic upgrade head
```

Start everything:

```bash
docker compose up -d
```

Open the app:

```text
http://localhost:8080
```

Useful commands:

```bash
docker compose logs -f worker
docker compose logs -f api
docker compose ps
docker compose down
```

The frontend container proxies API calls through nginx:

```text
Browser -> http://localhost:8080/api -> api:8000 inside Docker
```

That means the browser does not need to call the API container directly.

## Tests

Install test dependencies:

```bash
.venv/bin/python3 -m pip install -r requirements-dev.txt
```

Run Python tests:

```bash
.venv/bin/python3 -m pytest -q
```

Some PostgreSQL integration tests are skipped unless `MISP_DB_URL` is set.
Authentication HTTP tests use an isolated in-memory database and never connect to your configured database.

Run frontend checks:

```bash
cd frontend
npm run build
```

## Shared-password access

Event lists, details and change history require the shared password. There are no accounts,
usernames, registrations or invitation codes. The MISP worker and CLI
continue running independently of browser logins. `/health` remains public.

Generate a password hash locally (the password is entered privately, not as a command argument):

```bash
.venv/bin/python -m scripts.hash_password
```

The generator requires a 15–128 character password and prints a single-quoted
`APP_PASSWORD_HASH='...'` line. Copy that line into `.env`; keep the single quotes so Compose
preserves the dollar signs in the Argon2id hash. Share the password privately with colleagues.
If you only have Docker installed, build first and use
`docker compose run --rm --no-deps api python -m scripts.hash_password` instead.

Set these variables in `.env` for Docker Compose (export them in your shell when running
uvicorn directly; Python does not automatically load `.env`):

```dotenv
# Paste the generated, single-quoted APP_PASSWORD_HASH line here.
AUTH_COOKIE_SECURE=true
AUTH_ALLOWED_ORIGINS=https://your-domain.example
```

An empty, missing or invalid `APP_PASSWORD_HASH` blocks access. The plaintext password is
not stored in the application database or configuration. Remove the old `INVITATION_CODE`
setting if it exists; it is no longer used.

Sessions expire after eight hours and are revoked immediately on logout. Only a SHA-256 hash
of the random session token is stored in PostgreSQL; the browser receives an HttpOnly,
SameSite=Lax cookie. Authentication POST requests require `X-CSRF-Protection: 1`; requests
with an Origin header must match `AUTH_ALLOWED_ORIGINS` exactly. The React client sends
this header and credentials automatically. API responses use `Cache-Control: no-store`.

For local **HTTP** development only:

```dotenv
AUTH_COOKIE_SECURE=false
AUTH_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
```

Use `localhost` consistently for the frontend and API during development. On your public
Cloudflare domain keep `AUTH_COOKIE_SECURE=true`, use HTTPS, and include the exact domain
in `AUTH_ALLOWED_ORIGINS`. Secure cookies cannot support login on a plain HTTP LAN address.

Deploy the schema before starting the updated API:

```bash
docker compose build
docker compose stop api
docker compose run --rm api alembic upgrade head
docker compose up -d
```

The migration removes old account records and invalidates all previous sessions. Event data
and history are preserved. The previous migration remains in the migration chain so databases
that already applied it can upgrade; downgrading cannot recover deleted accounts.

To rotate the password, generate a new hash, replace `APP_PASSWORD_HASH` in `.env`, then run:

```bash
docker compose up -d --force-recreate api
```

Changing the configured hash invalidates every previous session, including sessions of people
already logged in. A plain container restart does not load changed Compose environment values.
There is no automatic daily rotation; repeat these steps when you want to change the password.

Login attempts are limited across API processes using PostgreSQL: 30 per minute in total.
Successful attempts also count. This small-team limit can temporarily block legitimate
logins during repeated attempts. Invalid requests rejected by input/CSRF validation do not count.
Expired throttle entries are removed during authentication attempts; expired sessions are
removed when a new login creates a session, along with sessions for previous password hashes.

Argon2id uses 64 MiB, three iterations and four lanes. Benchmark login on your deployment
hardware before exposing it to users. Generate a new hash when changing hashing parameters.

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
