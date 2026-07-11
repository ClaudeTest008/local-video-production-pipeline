# Architecture

How the LVPP backend, web app, and desktop shell fit together, and the conventions every feature module follows.

## Clean architecture layers

Requests flow through four layers. Each layer only knows about the one below it.

```
HTTP request
  │
  ▼
API router        app/modules/<name>/router.py   FastAPI APIRouter; validation via Pydantic schemas
  │
  ▼
Service           app/modules/<name>/service.py  Business logic (only where a module needs it)
  │
  ▼
Repository        app/core/repository.py         Generic CRUD over any SQLAlchemy model
  │
  ▼
SQLAlchemy model  app/modules/<name>/models.py   Tables; Base + TimestampMixin from app/core/db.py
```

Thin CRUD modules (prompts, scripts, storyboard, seo, templates, ...) skip the service layer entirely — their routers come from a factory (see below). Modules with real logic add a `service.py` (agents, subtitles) or an external client (`comfyui/client.py`).

## Feature-first module system with auto-discovery

All features live under `backend/app/modules/` — 23 modules at present (projects, prompts, scripts, storyboard, comfyui, assets, timeline, voice, subtitles, chat, agents, rag, mcp, plugins, research, seo, thumbnail, templates, publishing, analytics, settings, model_manager, workflows).

`app/core/registry.py` discovers them at startup with `pkgutil.iter_modules`:

- `collect_routers()` imports `app.modules.<name>.router` and picks up the module-level `router` if it is an `APIRouter`. `app/main.py` mounts each one under `/api`.
- `import_all_models()` imports `app.modules.<name>.models` (if present) so `Base.metadata` sees every table before `create_all` / Alembic autogenerate.

**The zero-core-change contract**: to add a feature, drop a package under `app/modules/<name>/` containing

| File | Required | Contract |
|---|---|---|
| `router.py` | yes | exposes `router: APIRouter` |
| `models.py` | no | SQLAlchemy models on `app.core.db.Base` |
| `schemas.py` | no | Pydantic request/response models |
| `service.py` | no | business logic, external clients |

No import to add, no list to edit, no core file touched. Delete the folder and the feature is gone.

## Generic Repository + crud_router factory

`app/core/repository.py` is one generic `Repository[M]` (get / list-with-filters / create / update / delete) shared by every module — there are no per-entity repository classes.

`app/core/crud_router.py` turns a model + three schemas into a full REST router:

```python
# app/modules/prompts/router.py — a complete module router
from app.core.crud_router import crud_router
from app.modules.prompts.models import Prompt
from app.modules.prompts.schemas import PromptCreate, PromptRead, PromptUpdate

router = crud_router(
    model=Prompt,
    create_schema=PromptCreate,
    read_schema=PromptRead,
    update_schema=PromptUpdate,
    prefix="/prompts",
    tag="prompts",
    entity="prompt",
)
```

Generated endpoints: `GET ""` (offset/limit ≤ 500, optional `project_id` filter), `POST ""`, `GET /{id}`, `PATCH /{id}` (partial, `exclude_unset`), `DELETE /{id}`. Every write emits `<entity>.created|updated|deleted` on the event bus. Twelve modules use the factory; the rest (projects, comfyui, timeline, voice, chat, agents, mcp, rag, settings, subtitles, workflows) hand-write routers because they do more than CRUD.

## In-process EventBus

`app/core/events.py` — a synchronous, in-process pub/sub singleton (`bus`). Modules communicate through events, never direct cross-module imports.

- **Subscribe** with an exact topic (`"asset.generated"`), a wildcard suffix (`"comfyui.job.*"`), or `"*"` for everything. Handler signature: `(topic: str, payload: dict) -> None`.
- **Emit** never raises: a failing handler is logged and skipped, so one bad subscriber can't break the emitter.

Events currently emitted:

| Topic | Emitted by | Payload keys |
|---|---|---|
| `project.created` / `project.updated` / `project.deleted` | projects router | `id` |
| `project.restored` | snapshot restore | `id`, `snapshot_id` |
| `<entity>.created` / `.updated` / `.deleted` | every `crud_router` module | `id` |
| `comfyui.job.queued` | comfyui queue | `id`, `prompt_id` |
| `comfyui.job.finished` | comfyui job poll | `id`, `status` |
| `asset.generated` | comfyui (job done), timeline (ffmpeg render) | `project_id`, plus `outputs` or `kind`/`path` |
| `agent.ran` | agents service | `agent_id`, `conversation_id` |
| `mcp.discovered` / `mcp.toggled` | mcp router | `added` / `id`, `enabled` |

The bus is in-process only — no broker, no persistence. If LVPP ever needs cross-process events (e.g. background workers), that is a replacement of `EventBus`, not a new API for modules.

## Provider-agnostic AI layer

`app/core/ai/base.py` defines the contract: `ChatProvider` (ABC with `chat(messages, model, temperature, max_tokens) -> ChatResponse` and `is_available()`), plus the `ChatMessage` / `ChatResponse` dataclasses and `ProviderError`.

`app/core/ai/registry.py` maps names to factories:

| Name | Implementation |
|---|---|
| `ollama` | `OllamaProvider` (local, default) |
| `lmstudio` | `OpenAICompatProvider` pointed at `LVPP_LMSTUDIO_URL` |
| `openai` | `OpenAICompatProvider` → api.openai.com |
| `openrouter` | `OpenAICompatProvider` → openrouter.ai |
| `anthropic` | `AnthropicProvider` |
| `gemini` | `GeminiProvider` |

`register(name, factory)` at import time is all a plugin needs to add a provider — same zero-core-change idea as modules. Callers use `get_provider(name)` and never import a concrete provider. Defaults come from settings (`LVPP_DEFAULT_CHAT_PROVIDER` / `LVPP_DEFAULT_CHAT_MODEL`, default `ollama` / `llama3.1`).

## Dependency injection

Plain FastAPI `Depends`, no container:

- `get_db()` (`app/core/db.py`) yields a `Session` per request and closes it.
- Routers build repositories from it: `Depends(lambda db=Depends(get_db): Repository(Model, db))` (or a named `_repo` function).
- Configuration is a single `pydantic-settings` object (`app/core/config.py`), env prefix `LVPP_`, `.env` supported. SQLite at `backend/data/studio.db` by default; set `LVPP_DATABASE_URL` for PostgreSQL.
- `init_db()` runs `create_all` at startup for dev/test; production schema changes go through Alembic.

Tests override `get_db` via `app.dependency_overrides` (see `backend/tests/conftest.py`).

## Versioning

Three mechanisms, one per shape of problem:

| What | Mechanism | Where |
|---|---|---|
| Projects | **Snapshots** — `POST /api/projects/{id}/snapshots` copies the project fields into a `ProjectSnapshot` row; `POST .../snapshots/{sid}/restore` writes them back and emits `project.restored`. | `modules/projects` |
| Prompts | **Lineage fields** — every prompt has `version: int` and `parent_id`; iterating on a prompt means creating a new row pointing at its parent. Chains are client-driven; the API just stores them. | `modules/prompts` |
| Workflows | **Immutable versions** — `POST /api/workflows/{id}/new-version` copies the workflow, bumps `version`, sets `parent_id` to the source. Old versions are never mutated. | `modules/workflows` |

## Monorepo composition

```
┌──────────────────────────────────────────────────────────────┐
│ apps/desktop  (Tauri 2 shell, "LVPP Studio")                 │
│   wraps ───► apps/web  (Next.js, :3000 dev / static export)  │
│                │  imports                                    │
│                ├─ packages/shared   ApiClient + TS types     │
│                └─ packages/ui       headless primitives      │
└────────────────┼─────────────────────────────────────────────┘
                 │ HTTP (fetch)
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ backend  FastAPI @ http://127.0.0.1:8321  (OpenAPI at /docs) │
│   /api/<module> routers ── services ── Repository ── models  │
│   EventBus (in-process) · AI provider registry · MCP · files │
└──┬───────────┬───────────┬───────────────┬───────────────────┘
   │           │           │               │
   ▼           ▼           ▼               ▼
 SQLite     project      ComfyUI        Ollama :11434 / LM Studio :1234
 data/      file tree    :8188          OpenAI / Anthropic / Gemini /
 studio.db  data/projects/              OpenRouter (cloud, optional)
```

The desktop shell adds no API of its own: its CSP allows connections only to the backend (`:8321`) and ComfyUI (`:8188`), and everything else is the same web app.
