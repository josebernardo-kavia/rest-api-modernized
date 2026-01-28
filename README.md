# rest-api-modernized (FastAPI)

Modernized REST API backend for the security operations platform.

## Quickstart

### 1) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -U pip
pip install -e ".[dev]"
```

### 3) Configure environment

Copy `.env.example` to `.env` and adjust values.

Core variables:

- `APP_NAME`
- `APP_VERSION`
- `API_PREFIX` (default `/api`)
- `PORT` (default for preview/dev: `3002`)
- `BACKEND_CORS_ORIGINS` (recommended JSON array; default for preview/dev: `["http://localhost:3003"]`)
- `LOG_LEVEL`

Database (when enabled):

- `DATABASE_URL`

OIDC / Keycloak-compatible auth (JWT validation):

- `OIDC_ISSUER_URL` (e.g. `https://keycloak.example.com/realms/<realm>`)
- `OIDC_AUDIENCE` (expected `aud` claim; depends on your Keycloak client/mapper setup)
- `OIDC_CLIENT_ID` (used for extracting client roles from `resource_access[client_id].roles`)
- `OIDC_CACHE_TTL_SECONDS` (optional; default 300)

Deprecated (back-compat):

- `KEYCLOAK_ISSUER_URL`
- `KEYCLOAK_AUDIENCE`

### 4) Apply database migrations (required for DB features)

```bash
alembic upgrade head
```

### 5) Seed demo data (optional, for local development)

This inserts a small demo dataset (Projects/Tasks/Vulnerabilities) for UI testing.

```bash
python -m app.cli seed
```

If you want to clear existing rows first:

```bash
python -m app.cli seed --reset
```

Notes:
- The CLI uses `DATABASE_URL` from your environment (or `.env`).
- Ensure migrations are applied (`alembic upgrade head`) before seeding.

### 6) Run the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload
```

Notes:
- In containerized deployments, the platform may use `PORT` to decide which port to bind; the command above explicitly sets `--port`.

## Endpoints

Public:

- `GET /` → `{ "name": "...", "version": "..." }`
- `GET /health` → `{ "status": "ok" }`
- `GET /api/` → `{ "message": "..." }`
- `GET /api/info` → service metadata

Protected (requires `Authorization: Bearer <access_token>`):

- `GET /api/me` → current user identity derived from token
- `GET /api/protected` → protected example
- `GET /api/protected/admin` → requires token + one of example roles (`admin`, `realm-admin`)

OpenAPI docs:

- Swagger UI: `/docs` (use the "Authorize" button and paste `Bearer <token>`)
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Notes

- CORS is enabled only when `BACKEND_CORS_ORIGINS` is set (non-empty).
- Each response includes `X-Request-Id` for correlation/tracing.
