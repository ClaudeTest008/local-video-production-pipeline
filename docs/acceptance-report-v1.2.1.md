# Acceptance Report — LVPP Studio v1.2.1

Date: 2026-07-11. All evidence below is from runtime execution on the machine
described, not static analysis. Placeholders marked `PENDING` are filled from
the final run logs before release.

## System

| | |
| --- | --- |
| OS | Windows 11 Pro 10.0.26200 |
| CPU | Intel Core i9-12900KF |
| RAM | 64 GB |
| GPU | NVIDIA GeForce RTX 3090 (24 GB) |
| ComfyUI | 0.27.0 (Python 3.12.1, CUDA) |
| LLM provider | Ollama (gemma4:latest) |
| Video workflow | ComfyUI LTX 2.3 Dual Character Lip Sync LoRA Workflow (auto-selected, `video_lipsync`) |

## What was verified

### 1. Real AI video generation (single render, isolated)

The app-converted LTX 2.3 Dual Character graph was submitted through
`ComfyUIClient.queue_prompt` with **zero node_errors** and rendered:

- `output/lvpp_test/final_1783803006_00001_.mp4` — H.264 **1440×768**,
  **217 frames @ 24 fps**, **9.04 s**, **AAC audio track**, 2.74 MB
- ffprobe output on file; GPU at 100 %, 24.1/24.6 GB VRAM during render
- The workflow's VHS_VideoCombine node also produced its own audio-muxed mp4

This graph previously failed at three successive layers (enqueue rejection →
silent branch pruning → widget corruption); each was fixed with a regression
test (see CHANGELOG 1.2.1).

### 2. Full pipeline, dev backend (idea → assets)

`backend/scripts/accept_run.py`, fresh DB, live Ollama + ComfyUI:

| Stage | Status | Time | Output |
| --- | --- | --- | --- |
| research | done | 29 s | 7 038-char research note |
| script | done | 40 s | 285 words, revised after Creative-Director review |
| storyboard | done | 5 s | 5 scenes |
| prompts | done | 25 s | 5 scene prompts |
| video | done | 2 510 s (5 renders) | auto-selected LTX 2.3 Dual Character Lip Sync; 15 outputs auto-imported |
| captions | done | <1 s | 33-segment SRT written into the project tree |
| seo | done | | SEO pack saved |
| thumbnail | done | | thumbnail concepts saved |

Run status: **done** (all 8 stages). 15 assets imported (per scene: VHS
audio-muxed mp4 + SaveVideo copies — deduped to one timeline clip per scene by
the fix in `94ca80e`).

**Final export** (`POST /api/timelines/1/export`, `burn_subtitles: true`):
`data/projects/project-1/exports/Auto_assembly.mp4` — **1920×1080 H.264 +
AAC**, **45.17 s**, 1 355 frames, 21.7 MB, captions burned, concatenated from
the 5 AI-rendered lip-sync scenes (each with its generated voice track).
ffprobe-verified. GPU during renders: RTX 3090 at 100 %, 24.1/24.6 GB VRAM.

### 3. Installed desktop application (M7)

- NSIS installer `LVPP Studio_1.2.1_x64-setup.exe` built from source
- Silently installed **over v1.2.0**: registry version 1.2.0 → 1.2.1, binaries
  replaced
- **User data preserved**: pre-existing `%APPDATA%\LVPP Studio\studio.db`
  (4 projects) intact and served by the upgraded app
- Installed app launches; sidecar backend healthy on :8321; DB at migration
  head `ff13f0dcce8f`
- Frozen sidecar runs its **bundled Alembic migrations** on first boot
  (verified against an empty data dir: 4 migrations → 30 tables)
- Workflow discovery through the installed app: 26 imported, 0 failed;
  dependency-aware auto-selection picked the verified lip-sync workflow
- **Full production run through the installed app: done.** Project
  "Installed App Acceptance" (run 5) executed all 8 stages via the installed
  sidecar: research (6 795 chars) → script (723 words, review-revised) →
  storyboard (3 scenes) → prompts → video (3 scenes rendered via the
  auto-selected LTX lip-sync workflow, 9 outputs auto-imported) → captions →
  seo → thumbnail. First attempt hit `ollama: timed out` while the GPU was
  saturated by concurrent dev-run renders; the documented stage-retry
  (`/run-all` again) recovered cleanly once the queue drained.
- Final export through the installed backend:
  `%APPDATA%\LVPP Studio\projects\project-5\exports\Auto_assembly.mp4` —
  **1920×1080 H.264 + AAC, 27.1 s**, burned captions, 17.0 MB
  (ffprobe-verified)
- The final 1.2.1 build was then installed **over the mid-cycle 1.2.1 build**
  while that project existed — all 5 projects, the run history, and the
  exported video survived the second upgrade

### 4. Test suite

98 tests passing (`backend`, pytest). Every converter/client/selection defect
fixed in this release carries a regression test.

## Known limitations

- Release artifacts are unsigned (SmartScreen warning on first run)
- 18 of 26 discovered workflows need user-side model downloads or custom-node
  installs before they can render — exact per-workflow lists via
  `GET /api/workflows/{id}/dependencies` and `docs/workflow-compatibility.md`
- Voice/lip-sync comes from the ComfyUI workflow itself (LTX 2.3 AV class);
  there is no separate TTS stage — an image-only workflow set yields no audio
- LLM stages and video renders share one GPU: running both concurrently can
  time out the LLM provider (retry the stage once renders drain)

## Remaining roadmap

See ROADMAP.md — timeline editor polish, autopilot modes, trend engine,
knowledge engine feedback loop.
