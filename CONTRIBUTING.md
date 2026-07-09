# Contributing

## Setup

See [docs/installation.md](docs/installation.md). Short version: Python ≥3.11 venv in `backend/` with `pip install -e ".[dev]"`, `npm install` at the repo root.

## Ground rules

- **Conventional Commits** (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`). One focused change per commit.
- **Tests required**: backend changes need pytest coverage; `pytest -q` must pass.
- **Lint before pushing**: `ruff check app tests && black app tests` (backend), `npm run typecheck` (frontend).
- **Adding a feature module**: drop a package under `backend/app/modules/<name>/` with `router.py` exposing `router`. No core changes — the registry discovers it. Mirror the pattern in `app/modules/scripts/`.
- **Adding an AI provider**: implement `ChatProvider` and `register()` it (`app/core/ai/registry.py`).
- **Adding an MCP server**: add a catalog entry (`app/modules/mcp/catalog.py`) or register at runtime via `POST /api/mcp/servers`.
- Never commit secrets, `.env`, or generated media.

## PR checklist

- [ ] Tests pass locally (`pytest -q`, `npm run build:web`)
- [ ] Lint clean (ruff, black, tsc)
- [ ] Docs updated if behavior or architecture changed
- [ ] No unrelated changes
