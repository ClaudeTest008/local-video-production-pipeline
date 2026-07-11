# Roadmap — single source of truth

The vision lives in [docs/vision.md](docs/vision.md). This file tracks execution.

## Completed

- **Core architecture** — module auto-discovery (zero-core-change extension), event bus, generic repository + CRUD factory, SQLite default / PostgreSQL option, Alembic (`182a492d4e63`, `7e48a7c0ef51`)
- **Provider-agnostic AI layer** — ollama, lmstudio, openai, openrouter, anthropic, gemini behind one `ChatProvider` registry
- **20+ feature modules** — projects, scripts, storyboard, prompts, assets, comfyui, voice, subtitles, timeline, thumbnail, seo, publishing, analytics, research, rag, chat, agents, workflows, mcp, model_manager, templates, plugins, settings
- **Agent crew** — 19 role presets, per-profile provider/model/temperature/memory
- **MCP manager** — 13-server catalog, discover/toggle, `mcpServers` config export
- **ComfyUI integration** — client (nodes, installed-model introspection, queue, history), job tracking, positive-prompt injection, per-workflow success/speed stats
- **Web UI** — dark studio shell, command palette, 16 module pages; `@lvpp/shared` typed client; `@lvpp/ui` primitives
- **Desktop shell** — Tauri v2 scaffold (dev mode; packaging manual)
- **Brands** — multi-brand identities; brand context in every agent call
- **Pipeline orchestrator** — autonomous stage runner with lenient parsers; assisted (`/step`) + producer (`/run-all`) modes; media stages best-effort
- **Strategy Center** — scored opportunities (Brave evidence or model knowledge), approve → project
- **Knowledge Engine v1** — event-driven learnings (render outcomes, failures, analytics) fed into agent context
- **Docs, seed, examples, CI** — 12 docs, idempotent seed, GitHub Actions (lint + tests + typecheck + build)
- **Quality review loop** — Creative Director critique → revise pass on scripts (`LVPP_PIPELINE_REVIEW`)
- **Background pipeline execution** — threaded `run-all?background=true`, polling, stage retry, interrupted-run recovery
- **Brand engine preferences** — provider/model/ComfyUI-workflow per brand, honored across all agent runs and the images stage
- **System health + studio dashboard** — `/api/system/health` aggregate; home page is the studio overview (project list at `/projects`)

## In Progress

_(updated per milestone — empty when the tree is green)_

## Planned

| Item | What exists today | What's missing |
|---|---|---|
| Review loops beyond scripts | Script stage has critique→revise | Apply the same pattern to SEO packs, thumbnails, storyboards |
| Studio/Agency autopilot | Assisted + producer per project; background execution | Calendar planning from brand goals, batch approval, scheduled multi-project production |
| Trend ingestion | Brave web search (key) or model knowledge | RSS/Reddit/Google Trends/YouTube trending collectors feeding strategy evidence |
| WebSocket streaming progress | Pull-based job polling | Push progress for renders, voice, exports (ComfyUI exposes a WS already) |
| ComfyUI model downloads | Model metadata registry + installed listing | Download queue into ComfyUI folders, progress, checksum verify |
| Publishing integrations | Publish-job records only | YouTube Data API upload, OAuth, status sync; then Shorts/TikTok/etc. |
| Analytics sync | Manual metric snapshots | Scheduled platform pulls (YouTube Analytics first) |
| Plugin loading hooks | Manifest registry + drop-in modules | Import `manifest.entry` for enabled plugins, permission model |
| LangGraph agent graphs | Single-shot agent runner; `[agents]` extra installs langgraph | Multi-step graphs with tool use across stages |
| RAG-assisted research | `/rag` API works with `[rag]` extra | Auto-index research notes, retrieved context in agent runs |
| Drag-and-drop timeline | CRUD + FFmpeg export | Interactive editor: drag, trim, scrub |
| Video generation stage | Image stage via ComfyUI | Video workflows (img2vid), stitch into timeline |
| Music / SFX stage | Sound Designer agent (briefs only) | Local music generation integration + SFX cue placement |
| GPU resource manager | ComfyUI queue counts | VRAM-aware scheduling, priorities, estimated completion |
| Packaged desktop builds | Tauri dev shell | Sidecar backend binary, bundling, per-OS installers |

## Future Ideas

- Multi-format derivation (Shorts/TikTok cutdowns, blog + newsletter from the same research)
- A/B thumbnail/title variants with performance-driven selection
- Embedding-based knowledge retrieval (replace score-ranked digest)
- Community template/plugin marketplace
- Business dashboards: revenue, ROI, growth per brand

## Technical debt

- `Repository.list` filters are equality-only; no pagination metadata (fine at current scale)
- `next lint` replaced by direct eslint invocation (Next 15.5 deprecation) — revisit on Next 16
- Static export blocks `/projects/[id]` (desktop bundling) — needs `generateStaticParams` or query-param route
- Agent `get_agent` picks the first profile per role; duplicate-role profiles are user-managed
