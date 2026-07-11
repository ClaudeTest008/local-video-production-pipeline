# Acceptance report — v1.0.0 → v1.0.1

Runtime validation of the **installed** Windows application, performed 2026-07-11 on Windows 11 / RTX 3090 24 GB / Ollama (`gemma4:latest`) / ComfyUI (flux2 + LTX-2 models) — a real end-user machine, not a dev sandbox. Method: install → wizard → produce a real video → inspect every artifact → fix what broke → retest.

## Verified by runtime execution (installed app)

| Check | Evidence |
|---|---|
| Silent NSIS install | 3.9 s, per-user, no admin |
| Cold start → backend healthy | 2.1 s (first), 2.4 s (restart) |
| Memory footprint idle | shell 29 MB + backend 96 MB |
| Sidecar lifecycle | backend up with app; killed on exit; watchdog kills it on force-kill too |
| Setup wizard | full walk-through in UI: detection (Python 3.12.10, Git, Ollama+1 model, ComfyUI+6 checkpoints, RTX 3090 24 GB via nvidia-smi, fix hints for missing FFmpeg/Whisper/TTS), auto defaults (`ollama`/`gemma4:latest`, render sizing `heavy`), brand creation, sample project; wizard→dashboard transition verified post-fix |
| Dependency detection accuracy | FFmpeg flipped to detected immediately after `winget install` — live re-probe, no restart |
| **Full production pipeline (real AI)** | Project "Introduction to Local AI": research (7,867 chars, gemma4) → script (551 words, **revised after a real Creative-Director review verdict**) → 8 storyboard scenes → 8 engineered prompts → 8 ComfyUI renders (brand-preferred workflow) → SEO pack → thumbnail concepts, **3 m 38 s** for the text stages, voice skipped cleanly (no TTS engine) |
| ComfyUI integration | availability, checkpoint discovery (6), queueing, per-job tracking, output extraction, `/view` download — all against the real instance; workflow-stats learned 9 jobs / 100 % success |
| Knowledge engine | render learnings recorded automatically from job events |
| Video export | `Intro_to_Local_AI.mp4`: h264, 1280×720, 30 fps, **67 s**, 1.8 MB — plays, ffprobe-clean |
| Artifacts | 8 scene PNGs (~1.2 MB each, visually verified), thumbnail PNG (legible "LOCAL AI" text, genuinely usable), captions.srt (valid cue format), project archive zip (11 entries) |
| Logs | rotating file with timestamps/levels; in-app tail endpoint |
| GPU/CPU observation | 86 % GPU, 24 GB VRAM during combined LLM+render load; backend CPU idle between stages |

## Defects found by using the app — all fixed in v1.0.1

1. **Data-dir/install-dir collision** — user data sat next to `uninstall.exe`; moved to `%APPDATA%`.
2. **httpx log spam** — 133 KB of INFO health-poll lines; silenced.
3. **Wizard bounce** — finishing setup returned the user to Welcome (query-cache race); fixed and re-verified in UI.
4. *(harness, not product)* stale-cache test servers caused two false alarms; the packaged app is unaffected (Tauri serves hashed assets from its own protocol).
5. **Packaged logs wrote CWD-relative** — `LVPP_LOG_DIR` now set by the launcher.
6. **Prompt injection missed primitive-node prompts** — real saved workflows route prompts through `PrimitiveStringMultiline`; now covered.
7. **Bare 400 on workflow rejection** — ComfyUI's node-level errors now surfaced (found via a real graph whose `PreviewAny` nodes lost inputs in UI→API conversion).
8. **SEO parser vs markdown** — `**TITLE:**` broke marker matching; emphasis stripped first.
9. **Image clips in timeline export** — stills now loop for their scene duration; without this the "video" was 8 frames.

## Verified only by inspection (not runtime)

- PostgreSQL path (SQLite exercised throughout), VTT export (SRT exercised; same serializer), macOS/Linux data-dir branches of the launcher, provider failover in the packaged build (covered by unit test + code path shared with dev).

## Could not be verified — and why

- **Tauri webview UI automation** — no driver for the embedded WebView2. Mitigation used: the *identical* static bundle was driven in a browser against the *installed* app's backend. Manual check: launch LVPP Studio, expect the same wizard/dashboard behavior. Expected result: identical (same HTML/JS, same API).
- **Clean-machine install** — this machine already had WebView2 and the dev toolchain. Manual: run the setup exe on a fresh Windows 11 VM; expect install + first-run wizard with all detections "not found" except Python-bundled backend.
- **Voice/whisper stages with engines installed** — no TTS engine/faster-whisper on this machine; stages verified to skip cleanly with actionable messages. Manual: install piper, re-run pipeline, expect `voice: done` and a WAV in `assets/audio`.
- **Uninstaller behavior** — not executed (would remove the app under test). Manual: run uninstall.exe, verify `%APPDATA%\LVPP Studio` survives (v1.0.1 layout).

## Performance summary

| Metric | Value |
|---|---|
| Install | 3.9 s |
| Cold start → API healthy | 2.1 s |
| Idea → all text artifacts (real 4-cls LLM, review loop, 8 scenes) | 3 m 38 s |
| Single 1280×720 flux2-turbo render | 86 s first (model load), ~30–60 s warm |
| 8 renders end-to-end (serialized queue) | ~9 min |
| Timeline MP4 export (8 stills → 67 s h264) | < 10 s |
| Idea → finished video, thumbnail, captions, SEO, archive | **~15 min wall clock** |

Bottleneck: GPU render serialization (expected — one queue). Workflow-stats currently measures created→done, which includes queue wait — noted for v1.1 (per-job execution time from ComfyUI history).

## Would a real creator be satisfied?

The core loop — type an idea, get a reviewed script, rendered scenes, a usable thumbnail, captions, SEO, and a stitched MP4 without touching ComfyUI — works and feels genuinely magical for a v1. Honest gaps a creator would hit next: no voice-over out of the box (needs piper install), captions are script-split rather than audio-aligned (needs Whisper + voice), the MP4 is a slideshow of stills (video-generation workflows are the obvious v1.1 headline given LTX-2 models were detected), and renders don't auto-import into Assets (assembled via API this run). All tracked in ROADMAP.md.

## Recommendations for v1.1 (priority order)

1. Auto-import rendered outputs into project assets + auto-assemble the timeline (the one manual step left in idea→video)
2. Video-generation workflows (LTX-2 class) as the images stage's big sibling
3. Voice stage one-click piper install; Whisper-aligned captions
4. Workflow manual mode UI (list/enable/favorite/tag/benchmark) — API exists, needs surface
5. Per-job execution-time stats from ComfyUI history (exclude queue wait)
6. Code signing + auto-update
