# Plugin Guide

How to extend LVPP today: drop-in backend modules, custom AI providers, and MCP servers — plus the plugin registry that exists in the DB but is not yet wired to a loader.

## What "plugin" means right now

| Extension path | Status | Core changes needed |
|---|---|---|
| Backend feature module under `app/modules/` | Works today (primary path) | None |
| AI chat provider via `app.core.ai.registry.register()` | Works today | None |
| MCP server (catalog entry or custom via API) | Works today | None (API-only for custom) |
| Plugin manifests loaded from the `plugins` table | **Roadmap** — storage exists, loading hooks do not | — |

## 1. Backend feature modules (the primary path)

The backend auto-discovers modules at startup (`backend/app/core/registry.py`). Any package under `backend/app/modules/<name>/` is picked up if it has:

- `router.py` exposing a module-level `router: APIRouter` (required)
- `models.py` with SQLAlchemy models (optional — tables are created automatically in dev)

No imports to add anywhere. No core edits. Routers are mounted under `/api` and appear in the OpenAPI docs at `http://127.0.0.1:8321/docs`.

### Full example: a `moodboard` module

`backend/app/modules/moodboard/__init__.py` — empty file.

`backend/app/modules/moodboard/models.py`:

```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Moodboard(Base, TimestampMixin):
    __tablename__ = "moodboards"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    images: Mapped[list] = mapped_column(default=list)  # dict/list map to JSON columns
    meta: Mapped[dict] = mapped_column(default=dict)
```

`backend/app/modules/moodboard/schemas.py`:

```python
from app.core.schemas import OrmModel, Timestamped


class MoodboardCreate(OrmModel):
    project_id: int
    name: str
    images: list = []
    meta: dict = {}


class MoodboardUpdate(OrmModel):
    name: str | None = None
    images: list | None = None
    meta: dict | None = None


class MoodboardRead(Timestamped):
    project_id: int
    name: str
    images: list
    meta: dict
```

`backend/app/modules/moodboard/router.py`:

```python
from app.core.crud_router import crud_router
from app.modules.moodboard.models import Moodboard
from app.modules.moodboard.schemas import MoodboardCreate, MoodboardRead, MoodboardUpdate

router = crud_router(
    model=Moodboard,
    create_schema=MoodboardCreate,
    read_schema=MoodboardRead,
    update_schema=MoodboardUpdate,
    prefix="/moodboards",
    tag="moodboards",
    entity="moodboard",
)
```

Restart the backend. You now have `GET/POST /api/moodboards`, `GET/PATCH/DELETE /api/moodboards/{id}`, `?project_id=` filtering, and `moodboard.created|updated|deleted` events on the bus — from three small files.

### Custom endpoints and events

`crud_router` is optional; any `APIRouter` works (see `app/modules/comfyui/router.py` for a non-CRUD module). Modules communicate through the in-process event bus (`app/core/events.py`), never direct cross-module imports:

```python
# in router.py — this file is imported at startup, so subscriptions register then
from app.core.events import bus


def on_asset_generated(topic: str, payload: dict) -> None:
    ...  # e.g. add generated images to a moodboard


bus.subscribe("asset.generated", on_asset_generated)  # also: "asset.*" or "*"
```

Useful topics emitted today: `<entity>.created|updated|deleted` (every CRUD module), `asset.generated` (ComfyUI, voice, timeline export), `comfyui.job.queued|finished`, `mcp.discovered|toggled`, `agent.ran`.

Configuration comes from `app.core.config.settings` (env prefix `LVPP_`, `.env` supported). Extend `Settings` only if your module needs a new setting.

## 2. Registering an AI provider

Every AI service sits behind `ChatProvider` (`app/core/ai/base.py`). Implement it and register a factory — the provider becomes selectable by name in chat conversations and agent profiles, and shows up in `GET /api/settings/providers`:

```python
# backend/app/modules/myprovider/router.py
from fastapi import APIRouter

from app.core.ai import registry
from app.core.ai.base import ChatMessage, ChatProvider, ChatResponse, ProviderError


class MyProvider(ChatProvider):
    name = "myprovider"

    def chat(self, messages: list[ChatMessage], model: str,
             temperature: float = 0.7, max_tokens: int = 4096) -> ChatResponse:
        # call your service; raise ProviderError on failure (mapped to HTTP 502)
        return ChatResponse(content="...", model=model, provider=self.name)

    def is_available(self) -> bool:
        return True  # probe your service; drives the availability dot in Settings


registry.register("myprovider", MyProvider)

router = APIRouter()  # empty router so module discovery imports this file
```

If your service speaks the OpenAI chat-completions dialect, skip the class entirely and reuse `OpenAICompatProvider` (`app/core/ai/openai_compat.py`) — that is how `openai`, `openrouter`, and `lmstudio` are registered in `app/core/ai/registry.py`.

## 3. MCP servers

Two ways, neither touches core code:

- **Catalog entry**: add a dict to `CATALOG` in `backend/app/modules/mcp/catalog.py` (name, description, command, args, env). `POST /api/mcp/discover` imports catalog entries into the DB, disabled by default.
- **Custom server via API/UI**: `POST /api/mcp/servers` with the same shape — no code at all.

Toggle with `POST /api/mcp/servers/{id}/toggle`. `GET /api/mcp/export` emits a standard `mcpServers` JSON block consumable by Claude Desktop, Cursor, or the desktop app. See [mcp-guide.md](mcp-guide.md).

## 4. The plugins DB module (registry only — loading is roadmap)

`app/modules/plugins/` provides CRUD at `/api/plugins` over this model:

| Column | Type | Purpose |
|---|---|---|
| `name` | str | Plugin display name |
| `path` | str | Where the plugin lives on disk |
| `enabled` | bool | Intended activation flag |
| `manifest` | JSON | Plugin metadata (see below) |
| `meta` | JSON | Free-form extra data |

**Be clear about what this does today: it stores rows.** Nothing reads `path` or `manifest` at startup, and `enabled` gates nothing. Loading hooks (import the entry package, register its routers/providers, enforce permissions) are on the [roadmap](roadmap.md). Until then, "installing a plugin" means placing its package under `app/modules/` yourself — the registry row is bookkeeping.

### Suggested manifest shape

So that manifests written now survive the loader landing later, use:

```json
{
  "name": "moodboard",
  "version": "0.1.0",
  "entry": "app.modules.moodboard",
  "permissions": ["db", "events", "ai"]
}
```

- `entry` — importable package exposing `router` (same contract as built-in modules)
- `permissions` — declared capabilities; advisory today, intended to be enforced by the loader

## Checklist for shipping a module

1. Package under `backend/app/modules/<name>/` with `__init__.py`, `router.py` (+ `models.py`, `schemas.py` as needed).
2. Restart the backend; confirm your routes at `/docs`.
3. Emit/subscribe events instead of importing other modules.
4. Add tests under `backend/tests/` and run `pytest -q` (see [development.md](development.md)).
5. Optionally register it at `POST /api/plugins` with a manifest.
