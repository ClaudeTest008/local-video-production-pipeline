# Quick start

Five minutes from install to your first AI-produced content plan.

## 1. Install

Download **LVPP Studio_1.0.0_x64-setup.exe** from the [latest release](https://github.com/ClaudeTest008/local-video-production-pipeline/releases), run it (per-user install, no admin needed), and launch **LVPP Studio**. The backend starts automatically — nothing else to run.

> Unsigned build: Windows SmartScreen may warn on first run — choose "More info → Run anyway". See [deployment.md](deployment.md#code-signing) for signing status.

## 2. Setup wizard

First launch opens the wizard. It scans your machine (Ollama, ComfyUI, FFmpeg, GPU/VRAM, …) and shows a fix hint for anything missing — everything is optional, but for the full experience install:

- **[Ollama](https://ollama.com)** + `ollama pull llama3.1` — local AI for all agents (no account, no cloud)
- **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** — image rendering
- **FFmpeg** (`winget install Gyan.FFmpeg`) — video export

Create your first brand in the wizard (name + goal is enough) and keep "sample project" checked.

## 3. Produce

1. **Strategy** → "Generate opportunities" — the Strategy Director proposes scored topics for your brand.
2. **Approve** the one you like — it becomes a project.
3. **Pipeline** → select the project → **New producer run** → **Run all**. The crew researches, writes (with a Creative-Director review pass), storyboards, writes image prompts, renders via ComfyUI (if running), voices (if a TTS engine is installed), and produces SEO + thumbnail concepts.
4. Review everything from the **project page**; export SRT captions, script markdown, MP4 (timeline), or a full project archive.

No Ollama yet? Set provider `echo` in Settings to watch the pipeline run with deterministic placeholder output.

## 4. Where things live

- Your data: `%LOCALAPPDATA%\LVPP Studio` (database, projects, logs) — delete it to factory-reset.
- Logs: Settings → Application log, or `GET /api/system/logs`.
- API playground: http://127.0.0.1:8321/docs while the app runs.
