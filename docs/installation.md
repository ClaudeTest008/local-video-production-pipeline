# Installation

How to install the LVPP backend, web app, and (optionally) the desktop shell on Windows, macOS, and Linux.

## Prerequisites

| Requirement | Version | Needed for | Notes |
|---|---|---|---|
| Python | ≥ 3.11 | backend (required) | 3.12 used in CI |
| Node.js | ≥ 20 | web app (required) | npm workspaces |
| Rust toolchain | stable | desktop shell (optional) | Tauri 2; install via [rustup](https://rustup.rs) |
| FFmpeg | any recent | timeline render (optional) | must be on `PATH`; without it, render endpoints return the command as a dry-run |
| ComfyUI | local install | image generation (optional) | default endpoint `http://127.0.0.1:8188` |
| Ollama | local install | local LLM chat (optional) | default endpoint `http://127.0.0.1:11434`; default provider/model is `ollama` / `llama3.1` |

Everything optional degrades gracefully: the backend probes availability instead of assuming it.

## 1. Backend (FastAPI)

Windows (PowerShell):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python seed.py                                  # optional sample data
uvicorn app.main:app --reload --port 8321
```

macOS / Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python seed.py                                  # optional sample data
uvicorn app.main:app --reload --port 8321
```

Verify: `http://127.0.0.1:8321/api/health` returns `{"status": "ok", ...}`. Interactive OpenAPI docs at `http://127.0.0.1:8321/docs`.

The SQLite database is created automatically at `backend/data/studio.db` on first start. No migration step is needed for local development (tables are created via `create_all`; see [development.md](development.md) for Alembic).

### Optional extras

Install only what you use:

| Extra | Command | Enables |
|---|---|---|
| `dev` | `pip install -e ".[dev]"` | pytest, ruff, black |
| `postgres` | `pip install -e ".[postgres]"` | PostgreSQL driver (psycopg2) |
| `rag` | `pip install -e ".[rag]"` | ChromaDB + sentence-transformers for research/RAG |
| `agents` | `pip install -e ".[agents]"` | LangGraph for agent workflows |

Extras combine: `pip install -e ".[dev,postgres,rag]"`.

## 2. Web app (Next.js)

From the repo root (npm workspaces — do not `npm install` inside `apps/web`):

```bash
npm install
npm run dev:web        # http://localhost:3000
```

The web app talks to the backend at `http://127.0.0.1:8321/api` (the default baked into `@lvpp/shared`'s `ApiClient`). Start the backend first.

## 3. Desktop shell (Tauri, optional)

Requires the Rust toolchain. The desktop package is intentionally **not** part of the npm workspace, so install its dependencies separately:

```bash
cd apps/desktop
npm install            # installs @tauri-apps/cli
npm run dev            # or: cargo tauri dev (if tauri-cli is installed via cargo)
```

`tauri dev` starts the web dev server automatically (`beforeDevCommand`) and opens it in a native window. The backend must be running separately. Installer bundling is currently disabled (`bundle.active: false`) — see [deployment.md](deployment.md).

## Configuration (.env)

All backend settings are environment variables with the `LVPP_` prefix, loaded from `backend/.env` (see `backend/.env.example`). Every variable is optional — defaults are local-first.

| Variable | Default | Purpose |
|---|---|---|
| `LVPP_APP_NAME` | `Local Video Production Pipeline` | App title shown in OpenAPI docs and health endpoint |
| `LVPP_HOST` | `127.0.0.1` | Bind host (informational; pass `--host` to uvicorn to change the actual bind) |
| `LVPP_PORT` | `8321` | Backend port (informational; pass `--port 8321` to uvicorn) |
| `LVPP_CORS_ORIGINS` | `["http://localhost:3000", "tauri://localhost"]` | Allowed browser origins (JSON list) |
| `LVPP_DATABASE_URL` | `sqlite:///./data/studio.db` | SQLAlchemy URL; set to `postgresql+psycopg2://user:pass@localhost/lvpp` for PostgreSQL |
| `LVPP_PROJECTS_ROOT` | `./data/projects` | Root folder where per-project asset trees are created |
| `LVPP_COMFYUI_URL` | `http://127.0.0.1:8188` | Local ComfyUI endpoint |
| `LVPP_OLLAMA_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint |
| `LVPP_LMSTUDIO_URL` | `http://127.0.0.1:1234/v1` | Local LM Studio (OpenAI-compatible) endpoint |
| `LVPP_OPENAI_API_KEY` | *(empty)* | OpenAI cloud provider key |
| `LVPP_ANTHROPIC_API_KEY` | *(empty)* | Anthropic cloud provider key |
| `LVPP_GEMINI_API_KEY` | *(empty)* | Google Gemini cloud provider key |
| `LVPP_OPENROUTER_API_KEY` | *(empty)* | OpenRouter cloud provider key |
| `LVPP_BRAVE_API_KEY` | *(empty)* | Brave Search key (research module) |
| `LVPP_TAVILY_API_KEY` | *(empty)* | Tavily search key (research module) |
| `LVPP_DEFAULT_CHAT_PROVIDER` | `ollama` | Default AI provider for chat/agents |
| `LVPP_DEFAULT_CHAT_MODEL` | `llama3.1` | Default model name for the default provider |

Never commit `.env` — API keys stay local. See [ai-providers.md](ai-providers.md) for per-provider setup.

## Troubleshooting

Common install issues (port conflicts, missing FFmpeg, ComfyUI not reachable) are covered in [troubleshooting.md](troubleshooting.md).
