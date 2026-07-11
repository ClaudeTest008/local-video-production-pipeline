# Local Video Production Pipeline

Local-first **AI Creator Operating System**. You are the Creative Director; a crew of specialized AI agents does the work — from *"what should I create next?"* through research, script, storyboard, ComfyUI renders, voice, captions, SEO, and analytics. Multi-brand, provider-agnostic, MCP-native. See [docs/vision.md](docs/vision.md).

**Strategy (scored opportunities) → approve → Pipeline: Research → Script → Storyboard → Prompts → Images → Voice → SEO → Thumbnail → … → Analytics → Knowledge (the studio learns)**

## Philosophy

- **Local-first** — your data lives on your machine (SQLite + local file tree). PostgreSQL optional.
- **AI-first, provider-agnostic** — every AI service is replaceable. Ollama, LM Studio, OpenAI, Anthropic, Gemini, OpenRouter behind one interface.
- **MCP-native** — discover, enable, and disable MCP servers from the UI; add new ones without touching core code.
- **Modular** — feature-first modules auto-registered at startup; plugins and new modules need zero core changes.
- **Offline-capable** — everything except cloud AI providers and publishing works offline.

## Monorepo layout

```
apps/
  web/          Next.js web app (UI)
  desktop/      Tauri desktop shell wrapping the web UI
packages/
  shared/       Shared TypeScript types + API client
backend/        FastAPI backend (Python 3.12), SQLAlchemy, Alembic
docs/           Architecture, guides, roadmap
examples/       Example ComfyUI workflows, sample project, seeds
```

## Quick start

Prereqs: Python ≥ 3.11, Node ≥ 20, (optional) Rust toolchain for the desktop build, (optional) FFmpeg on PATH, (optional) local [ComfyUI](https://github.com/comfyanonymous/ComfyUI) and [Ollama](https://ollama.com).

```bash
# Backend (from the repo root)
cd backend
python -m venv .venv
source .venv/bin/activate                    # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python seed.py                               # optional: sample data
uvicorn app.main:app --reload --port 8321    # http://localhost:8321  (docs at /docs)

# Web app (new shell, from the repo root)
npm install
npm run dev:web                              # http://localhost:3000

# Desktop (new shell, from the repo root; requires Rust)
cd apps/desktop && npm install && npm run dev
```

## Documentation

| Doc | Contents |
|---|---|
| [docs/vision.md](docs/vision.md) | The Creator OS vision, autopilot ladder, learning loop |
| [docs/architecture.md](docs/architecture.md) | Clean architecture, module system, event bus |
| [docs/folder-structure.md](docs/folder-structure.md) | Repo + project asset layout |
| [docs/installation.md](docs/installation.md) | Full install guide |
| [docs/development.md](docs/development.md) | Dev workflow, testing, lint |
| [docs/deployment.md](docs/deployment.md) | Packaging + deployment |
| [docs/ai-providers.md](docs/ai-providers.md) | Configuring Ollama/OpenAI/Anthropic/Gemini/LM Studio/OpenRouter |
| [docs/mcp-guide.md](docs/mcp-guide.md) | MCP server discovery + adding servers |
| [docs/comfyui-guide.md](docs/comfyui-guide.md) | ComfyUI integration |
| [docs/plugin-guide.md](docs/plugin-guide.md) | Writing plugins |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues |
| [docs/roadmap.md](docs/roadmap.md) | Phases + status |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributing guide |

## License

MIT
