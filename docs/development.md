# Development

Day-to-day workflow: dev servers, tests, lint, migrations, and how to extend the system.

Prerequisite: complete [installation.md](installation.md) first (backend venv with `pip install -e ".[dev]"`, `npm install` at the repo root).

## Dev loop

Two terminals:

```bash
# Terminal 1 — backend (from backend/, venv active)
uvicorn app.main:app --reload --port 8321

# Terminal 2 — web (from repo root)
npm run dev:web        # http://localhost:3000
```

Both hot-reload. The OpenAPI docs at `http://127.0.0.1:8321/docs` are the fastest way to poke any module's endpoints without the UI.

Desktop shell (optional, needs Rust): `cd apps/desktop && npm run dev` — starts the web dev server itself, but you still run the backend separately.

## Tests

Backend (from `backend/`):

```bash
pytest -q
```

Tests live in `backend/tests/` and run against an in-memory/dev database — no external services required. New backend features need pytest coverage (see [CONTRIBUTING.md](../CONTRIBUTING.md)).

There is no frontend test suite yet; `npm run typecheck` and `npm run build:web` are the frontend gates.

## Lint / format

Backend (from `backend/`):

```bash
ruff check app tests           # lint (add --fix to autofix)
black app tests                # format
black --check app tests       # what CI runs
```

Frontend (from repo root):

```bash
npm run typecheck              # tsc --noEmit across workspaces
npm run lint                   # next lint
```

Line length is 100 for both ruff and black (`backend/pyproject.toml`).

## Database migrations (Alembic)

Development and tests use `create_all` on startup (`init_db()` in `app/core/db.py`) — schema changes just appear when you restart the backend. **Migrations are for production databases** (typically PostgreSQL), where you cannot drop and recreate.

From `backend/` (venv active):

```bash
alembic revision --autogenerate -m "add scene transition column"
alembic upgrade head
```

Notes:

- `alembic/env.py` resolves the database URL from app settings, so `LVPP_DATABASE_URL` controls which database is migrated — same variable as the app.
- `import_all_models()` runs in `env.py`, so autogenerate sees every module's tables automatically.
- `alembic/versions/` is empty today; generate your first revision when you first deploy against PostgreSQL.
- Autogenerate output always needs review before committing — especially JSON columns and SQLite-vs-PostgreSQL type differences.

## Extending the system

Full rules in [CONTRIBUTING.md](../CONTRIBUTING.md). Short version:

**Add a feature module** — create `backend/app/modules/<name>/` with a `router.py` exposing `router` (an `APIRouter`) and optionally `models.py` (SQLAlchemy) and `schemas.py` (Pydantic). The registry (`app/core/registry.py`) auto-discovers it at startup; zero core changes. Mirror `app/modules/scripts/` as the reference pattern. For plain CRUD, `app/core/crud_router.py` generates the standard endpoints.

**Add an AI provider** — implement `ChatProvider` (`app/core/ai/base.py`) and `register("name", factory)` in `app/core/ai/registry.py` (or from a plugin at import time). See existing providers: `ollama.py`, `anthropic.py`, `gemini.py`, `openai_compat.py` (the last one covers any OpenAI-compatible endpoint — often you only need a `register()` call with a different base URL).

**Add an MCP server** — add a catalog entry in `app/modules/mcp/catalog.py` (ships with the app, seeded by `seed.py`) or register one at runtime via `POST /api/mcp/servers`. No code changes needed for runtime registration.

## Seed data

```bash
cd backend
python seed.py
```

Idempotent — safe to re-run. Creates a sample project ("Vertical Farming Deep-Dive") with a script, storyboard scenes, prompts, and an SEO pack, plus agent presets, the MCP server catalog, and a script template. Useful for exploring the UI without starting from an empty database.

## Before you push

Matches what CI enforces (`.github/workflows/ci.yml`):

```bash
# backend/
ruff check app tests && black --check app tests && pytest -q

# repo root
npm run typecheck && npm run build:web
```
