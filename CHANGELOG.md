# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/); versioning: [SemVer](https://semver.org/) (pre-1.0 — minor bumps may break).

## [Unreleased]

## [1.2.1] — 2026-07-11

**Real AI video, verified end-to-end.** The converter now handles modern ComfyUI serialization well enough that the LTX 2.3 Dual Character Lip Sync workflow imports, enqueues with zero node errors, and renders an actual H.264+AAC video (1440×768, 217 frames, 9s) through the app pipeline.

### Fixed
- **Schema self-heals on startup** — `init_db` runs `alembic upgrade head` (was `create_all`, which never adds columns; existing installs crashed with `no such column: workflow_defs.source`); frozen builds fall back to `create_all` if migration data is missing
- **Paths anchored for desktop bundles** — relative sqlite/projects/log paths resolve against the backend root, not the launch cwd
- **Converter**: subgraph flattening (incl. dict-shaped links), KJNodes SetNode/GetNode resolution, bypass (mode 4) rewiring with type-matched passthrough, muted-node handling, legacy PrimitiveNode inlining, modern `["COMBO", {options}]` widget recognition (was shifting every following widget), name-keyed `widgets_values` dicts (VHS), `COMFY_DYNAMICCOMBO_V3` sub-input expansion, model-path normalization to the server's exact combo entry on unique basename match
- **False success eliminated** — `queue_prompt` rejects HTTP 200 responses carrying `node_errors` (ComfyUI silently drops invalid outputs and runs the rest); the video stage reports `skipped` with the cause when a render finishes without producing frames
- **Ollama resilience** — a configured-but-not-pulled chat model falls back to an installed one instead of 404-failing every pipeline stage
- **Workflow selection** — dependency-aware (never picks a workflow whose nodes/models are missing when a ready one exists), deprioritizes workflows ComfyUI already rejected, exhausts all candidates instead of giving up after 3; utility/LLM graphs that merely load media are no longer classified as video workflows

### Added
- `GET /api/workflows/{id}/dependencies` — missing custom nodes / models per workflow, against the live server
- `docs/workflow-compatibility.md` + `backend/scripts/wf_sweep.py` — reproducible compatibility report (26 workflows, 8 render-ready at time of writing)
- Regression tests for every converter/client/selection fix (97 passing)

## [1.2.0] — 2026-07-11

**Pure-ComfyUI Creator OS.** Video, voice, lip-sync, and animation all come from your ComfyUI workflows — no bundled TTS, no Whisper, no separate audio stack.

### Added
- **Workflow discovery** — one click imports every workflow saved in your ComfyUI library; UI-format graphs are converted automatically (issues reported per node, never guessed); Browse-Templates index surfaced
- **Workflow upload** — drop any workflow `.json` (UI or API format) through the app
- **Workflow management** — type classification (Video + Lip-Sync / Avatar / Cinematic Video / Image), referenced models, VRAM estimate, enabled/favorite flags; users never edit nodes
- **Automatic workflow selection** — integrated video+voice workflows first, favorites win within the capable pool, brand preference overrides; the Create page previews the plan
- **Video pipeline stage** — renders every scene through the selected workflow, waits, auto-imports outputs into project assets, and assembles the timeline; on ComfyUI rejection the stage flags the workflow with the node-level error and automatically tries the next candidate
- **Captions stage** — script-timed caption track + SRT in the project tree; timeline export can burn captions into the video
- **Create page** — idea in, autonomous background production out; prominent sidebar button
- **Timeline editing** — clip reorder/remove, burn-captions toggle, AI editing box (the Editor agent proposes concrete edit plans)
- `POST /pipeline/runs/{id}/retry-stage` — re-run a skipped/errored stage after fixing its cause
- Focused sidebar (core loop up top, power tools under Advanced)

### Removed
- **Whisper and all standalone TTS engines** (piper/xtts/kokoro), the voice module, `/api/subtitles/transcribe`, the whisper MCP catalog entry, and the `[transcribe]` extra. Voice comes from ComfyUI AV workflows (LTX-2.3 class generates synchronized speech + video from text).

### Known limitations
- The built-in UI→API converter handles standard graphs; heavily customized nodes (LTXDirector-style) and subgraphs may fail validation — the app flags them and falls back; export those from ComfyUI as **API format** and upload instead
- Migration `ff13f0dcce8f`

## [1.0.1] — 2026-07-11

Acceptance-testing patch: every fix below came from running the installed app end-to-end and producing a real video (see `docs/acceptance-report-v1.0.0.md`).

### Fixed
- **User data survives uninstall** — data dir moved from `%LOCALAPPDATA%\LVPP Studio` (the NSIS install dir, wiped on uninstall) to `%APPDATA%\LVPP Studio`
- **Timeline export of still images** — image clips are now looped for their scene duration (`-loop 1 -t`); a storyboard of renders becomes a real video instead of a 3-frame flicker
- **Prompt injection covers real-world graphs** — `PrimitiveStringMultiline`/`PrimitiveString` prompt nodes are now injected (many saved workflows route prompts through primitives, not literal `CLIPTextEncode` text)
- **ComfyUI validation errors are actionable** — queue failures surface ComfyUI's own node-level diagnosis instead of a bare 400
- **SEO parser handles markdown-wrapped markers** (`**TITLE:**`)
- **Setup wizard no longer bounces back to Welcome** after finishing (stale query-cache race)
- **Logs write to the data directory** in packaged builds (`LVPP_LOG_DIR` was unset → CWD-relative)
- **Log noise** — httpx request lines (health polling) silenced to WARNING

## [1.0.0] — 2026-07-11

First public release: an installable Windows desktop app a non-developer can set up and use.

### Added
- **Windows installer** (NSIS, per-user) with the backend bundled as a PyInstaller sidecar — data in `%LOCALAPPDATA%\LVPP Studio`, backend exits with the shell even on force-kill (parent-PID watchdog)
- **Setup wizard** — dependency scan (Ollama+models, ComfyUI+checkpoints, FFmpeg, Git, Whisper, TTS engines, NVIDIA GPU/VRAM via nvidia-smi) with fix hints; intelligent defaults (auto-Ollama, VRAM-based workflow sizing); first brand + sample project; app redirects to the wizard until completed
- **Runtime settings override env** — wizard choices (default provider/model) win without editing `.env`
- **Provider failover** — any agent call retries once on the configured fallback provider
- **Structured logging** — rotating file log + `GET /api/system/logs` + in-app viewer (Settings)
- **Review loops extended** — Creative Director now also gates SEO packs and thumbnail concepts
- **`echo` provider** — deterministic offline provider; the full pipeline runs with zero AI tools installed
- **End-to-end smoke test** (`scripts/smoke.py`, 19 checks, runs in CI): fresh backend → wizard → brand → project → full producer pipeline → artifact/export verification
- Docs: quick start, user guide, FAQ; packaging + code-signing guide
- **Quality review loop** — Creative Director critiques generated scripts (APPROVE/REVISE verdict); the Script Writer revises on REVISE; critique persists on the script. Opt-out: `LVPP_PIPELINE_REVIEW=false`
- **Background pipeline execution** — `run-all?background=true` detaches into a worker thread with polling; failed stages retry on the next step; runs interrupted by a restart are marked with a resume hint
- **Brand engine preferences** — `preferred_provider` / `preferred_model` / `preferred_workflow_id`; precedence: agent profile → brand → app default; images stage renders with the brand's workflow
- **System health** — `GET /api/system/health`: database, ComfyUI (+per-device VRAM), provider availability, FFmpeg/Whisper/TTS, pipeline and render-queue depth
- **Studio dashboard** — the app now opens on a studio overview (system health, active production, top opportunities, brands, latest learnings); the project list moved to `/projects`
- Root `ROADMAP.md` (single source of truth) and this changelog

### Changed
- Project detail moved to `/project?id=` (static export compatibility for the desktop bundle)

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

[1.2.0]: https://github.com/ClaudeTest008/local-video-production-pipeline/releases/tag/v1.2.0
[1.0.1]: https://github.com/ClaudeTest008/local-video-production-pipeline/releases/tag/v1.0.1
[1.0.0]: https://github.com/ClaudeTest008/local-video-production-pipeline/releases/tag/v1.0.0
[0.2.0]: https://github.com/ClaudeTest008/local-video-production-pipeline/releases/tag/v0.2.0
[0.1.0]: https://github.com/ClaudeTest008/local-video-production-pipeline/releases/tag/v0.1.0
