# User guide

You are the Creative Director. The studio's agent crew does the work. This guide walks every surface; [quick-start.md](quick-start.md) is the 5-minute version.

## Studio (home)

Live overview: system health (backend, ComfyUI + VRAM, AI providers, FFmpeg), active production runs, top open opportunities, brands, and the latest things the studio learned. Green dots = ready; anything off shows what to do in the Setup wizard's scan (Settings → rerun detection via `/api/system/detect`).

## Brands

Every agent call runs inside a brand: voice, visual style, audience, guidelines, and goals shape research, scripts, prompts, and strategy. Per-brand engine preferences (provider, model, ComfyUI workflow) override app defaults for that brand's projects. Create one brand per channel/identity — each behaves like its own business.

## Strategy

Answers *"what should I create next?"* before *"how?"*. Generate opportunities (optionally around a focus topic); each is scored 0–10 on growth, competition, virality, evergreen value, short/long-form fit, audience fit, and urgency. With a Brave API key configured the Strategy Director cites live web evidence; without one it reasons from model knowledge and says so. **Approve** turns an opportunity into a project; **Reject** archives it.

## Pipeline

The production line: research → script → storyboard → prompts → video (voice + lip-sync via your ComfyUI workflows) → captions → SEO → thumbnail. Rendered outputs auto-import into Assets and the timeline is assembled for you.

- **Assisted run** — one stage per click; review artifacts between stages.
- **Producer run** — every runnable stage back-to-back; "Run all" also works in the background (the board keeps updating).
- **Quality review** — the Creative Director critiques scripts, SEO packs, and thumbnail concepts; on a REVISE verdict the producing agent rewrites once. The critique is stored with the artifact. Disable with `LVPP_PIPELINE_REVIEW=false`.
- **Degrading gracefully** — the video stage skips cleanly when ComfyUI isn't running or no workflow is enabled; a failed stage shows the reason and retries on the next run.
- Stage artifacts land in their modules: Scripts, Prompt Studio, Assets, Timeline, SEO records on the project.

## ComfyUI

Connects to a local instance (`http://127.0.0.1:8188` by default). Status, node browser, installed checkpoints/LoRAs/VAEs/ControlNets, manual job queueing (API-format workflows — export via "Save (API format)"), job history with output tracking, and per-workflow stats (success rate + speed) that drive automatic workflow choice. The **Workflows page** discovers every workflow saved in your ComfyUI library (Discover button), accepts .json uploads, classifies each one (Video + Lip-Sync / Avatar / Cinematic Video / Image), and lets you enable/favorite them. Automatic mode picks the best enabled video+voice workflow; you never edit nodes.

## Chat, Prompt Studio, Scripts, Assets, Timeline

- **AI Chat** — free-form chat with the default provider; the dock (status-bar toggle) pins to your active project.
- **Prompt Studio** — Monaco editor with version chains ("Save as v+1" keeps history).
- **Scripts** — markdown editor with word count + runtime estimate; export `.md`.
- **Assets** — everything generated or registered, filterable by kind.
- **Timeline** — track/clip structure with FFmpeg export (MP4/MOV); "Dry run" shows the exact command without executing.

## Agents

19 preset roles. Each profile has its own system prompt, provider, model, temperature, and persistent memory — edit any of them. Provider precedence per call: agent profile → brand preference → wizard default → env default. Configure a fallback provider (Settings key `fallback_chat_provider`) and any failed call retries there once.

## MCP servers

A 12-server catalog (filesystem, git, github, python, sqlite, docker, playwright, brave-search, comfyui, ffmpeg, browser, local-rag). Discover, toggle, add custom servers, and export the `mcpServers` JSON for Claude Desktop / Cursor.

## Settings

Provider availability, chat defaults (wizard-set; editable), and the application log viewer. Cloud API keys go in `backend/.env` (`LVPP_OPENAI_API_KEY`, …) — they never leave your machine except to the provider you configured.

## Data & privacy

Everything is local: SQLite database, project files, and logs under `%APPDATA%\LVPP Studio` (installed) or `backend/data` (dev). No telemetry. Cloud AI providers are opt-in per agent/brand/default.
