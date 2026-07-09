# Roadmap

What is built, what is next, and — for each "next" item — what already exists that it builds on.

## Phases

| Phase | Scope | Status |
|---|---|---|
| 1 | Repo scaffold + backend core (module auto-discovery, event bus, CRUD router factory, settings, SQLite/PostgreSQL) | Done |
| 2 | Backend feature modules — projects, scripts, storyboard, prompts, assets, comfyui, voice, subtitles, timeline, thumbnail, seo, publishing, analytics, research, rag, chat, agents, workflows, mcp, model_manager, templates, plugins, settings | Done |
| 3 | Web UI (Next.js app shell, module pages, chat dock, command palette) + shared packages (`@lvpp/shared` client/types, `@lvpp/ui`) | Done |
| 4 | Tauri desktop shell scaffold (window, CSP for backend + ComfyUI, dev wiring) | Done — scaffold only; packaging is Next |
| 5 | Docs, examples, seed data, CI (ruff/black/pytest + typecheck/build) | Done |

## Next

Roughly priority-ordered. Nothing below exists yet unless the "today" column says so — treat all of it as unshipped.

| Item | What exists today | What's missing |
|---|---|---|
| WebSocket streaming progress | Job status is pull-based: the UI polls `GET /api/comfyui/jobs/{id}`, which refreshes from ComfyUI history on read | Push progress over WebSocket (ComfyUI already exposes one) for generation, voice, and export jobs |
| ComfyUI model downloads | `model_manager` is a plain CRUD registry of model metadata; `GET /api/comfyui/models` lists what's installed | Download queue into ComfyUI's model folders, progress reporting, checksum verify |
| Real publishing integrations (YouTube API) | `publishing` stores publish jobs (platform, status, schedule, video asset) as records only | OAuth flow, actual upload via YouTube Data API, status sync back to the job |
| Platform analytics sync | `analytics` stores manually created metric snapshots | Scheduled pull from platform APIs (YouTube Analytics first) into snapshots |
| Plugin loading hooks | `plugins` table + CRUD at `/api/plugins` stores manifests; modules dropped into `app/modules/` load automatically | Loader that imports `manifest.entry` for enabled rows, permission enforcement — see [plugin-guide.md](plugin-guide.md) |
| LangGraph agent pipelines | Agent profiles + presets + single-shot runner (system prompt, memory, history → one provider call); `pip install -e ".[agents]"` installs langgraph, unused | Multi-step graphs chaining agents across pipeline stages (research → script → storyboard) |
| RAG-assisted research UI | Backend RAG API works with the `[rag]` extra (`/api/rag/index`, `/api/rag/query`) | Research page wiring: index notes automatically, surface retrieved context in agent runs |
| Drag-and-drop timeline | Timeline CRUD + FFmpeg concat/mix export; UI renders track data read-only-ish | Interactive editor: drag clips between tracks, trim, reorder, scrub preview |
| Packaged desktop builds with sidecar backend | Tauri dev shell works against separately started servers; `bundle.active` is `false` in `tauri.conf.json` | Bundle the backend as a Tauri sidecar binary, enable bundling, installers per OS |

## Non-goals (for now)

- Cloud sync / multi-user collaboration — the project is local-first by design.
- A built-in video compositor beyond FFmpeg concat/mix — heavier editing belongs in dedicated NLEs.
