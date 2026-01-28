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

Required variables (initial scaffold):

- `APP_NAME`
- `APP_VERSION`
- `API_PREFIX` (default `/api`)
- `BACKEND_CORS_ORIGINS` (recommended JSON array)
- `LOG_LEVEL`

Placeholders for later steps:

- `DATABASE_URL`
- `KEYCLOAK_ISSUER_URL`
- `KEYCLOAK_AUDIENCE`

### 4) Run the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

- `GET /` → `{ "name": "...", "version": "..." }`
- `GET /health` → `{ "status": "ok" }`
- `GET /api/` → `{ "message": "..." }`
- `GET /api/info` → service metadata

OpenAPI docs:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Notes

- CORS is enabled only when `BACKEND_CORS_ORIGINS` is set (non-empty).
- Each response includes `X-Request-Id` for correlation/tracing.
