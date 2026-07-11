# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/); versioning: [SemVer](https://semver.org/) (pre-1.0 — minor bumps may break).

## [Unreleased]

### Added
- **Quality review loop** — Creative Director critiques generated scripts (APPROVE/REVISE verdict); the Script Writer revises on REVISE; critique persists on the script. Opt-out: `LVPP_PIPELINE_REVIEW=false`
- **Background pipeline execution** — `run-all?background=true` detaches into a worker thread with polling; failed stages retry on the next step; runs interrupted by a restart are marked with a resume hint
- **Brand engine preferences** — `preferred_provider` / `preferred_model` / `preferred_workflow_id`; precedence: agent profile → brand → app default; images stage renders with the brand's workflow
- **System health** — `GET /api/system/health`: database, ComfyUI (+per-device VRAM), provider availability, FFmpeg/Whisper/TTS, pipeline and render-queue depth
- **Studio dashboard** — the app now opens on a studio overview (system health, active production, top opportunities, brands, latest learnings); the project list moved to `/projects`
- Root `ROADMAP.md` (single source of truth) and this changelog

### Fixed
- Migration `9b6ae3ffca66` adds NOT NULL brand columns with a server default (SQLite cannot alter populated tables otherwise); troubleshooting doc covers upgrading pre-existing dev databases

## [0.2.0] — 2026-07-11

### Added
- **Brands** — multi-brand identities (voice, style, audience, guidelines, goals, memory); projects belong to brands; brand context injected into every agent call
- **Pipeline orchestrator** — autonomous stage runner (research → script → storyboard → prompts → images → voice → seo → thumbnail) with lenient LLM-output parsers; assisted (`/step`) and producer (`/run-all`) modes; media stages skip cleanly when local engines are absent
- **Strategy Center** — Strategy Director generates scored opportunities (growth/competition/virality/evergreen/format-fit/urgency) from Brave evidence or model knowledge; approve → project
- **Knowledge Engine v1** — event subscribers turn render outcomes, pipeline failures, and analytics into learnings; digest feeds agent context
- **Workflow intelligence** — jobs link to workflow definitions; `/comfyui/workflow-stats` ranks by success rate and speed; positive-prompt injection into saved API-format graphs
- 5 new agent roles: Creative Director, Strategy Director, Publisher, Sound Designer, Business Manager (19 total)
- Web pages: Brands, Strategy (score bars, approve → project), Pipeline (stage board, step / run-all)
- `docs/vision.md` (Creator OS loop, autopilot ladder); migration `7e48a7c0ef51`

### Fixed
- CORS: any localhost port accepted via origin regex (dev server may not get :3000); Tauri Windows origins (`http(s)://tauri.localhost`)

## [0.1.0] — 2026-07-10

### Added
- Monorepo: FastAPI backend, Next.js 15 web app, Tauri v2 desktop scaffold, `@lvpp/shared` + `@lvpp/ui` packages
- Core architecture: module auto-discovery, event bus, generic repository + CRUD router factory, provider-agnostic AI layer (ollama/lmstudio/openai/openrouter/anthropic/gemini)
- 20+ feature modules incl. ComfyUI client with injectable transport, agents (14 presets), MCP manager (13-server catalog + export), subtitles (SRT/VTT + optional faster-whisper), voice (piper/xtts/kokoro), timeline (FFmpeg export), local RAG (optional chromadb)
- Studio web UI: dark theme, nav rail, command palette (Ctrl+K), chat dock, 13 pages
- Docs suite (12), CI (ruff/black/pytest, tsc/eslint/next build), idempotent seed, Alembic initial schema `182a492d4e63`
- Review fixes: README quick start, ESLint 9 flat config, Tauri static-export trigger, Windows WebView2 CORS

[0.2.0]: https://github.com/ClaudeTest008/local-video-production-pipeline/releases/tag/v0.2.0
[0.1.0]: https://github.com/ClaudeTest008/local-video-production-pipeline/releases/tag/v0.1.0
