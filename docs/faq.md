# FAQ

**Do I need an account or API key?**
No. With Ollama installed everything runs locally. Cloud providers (OpenAI, Anthropic, Gemini, OpenRouter) are optional and configured via `backend/.env`.

**Does anything leave my machine?**
Only calls to a cloud AI provider *you* configured, and web searches if you set a Brave/Tavily key. Database, media, logs: all local. No telemetry.

**The pipeline "skipped" images/voice — why?**
ComfyUI wasn't reachable, or no TTS engine (piper/xtts/kokoro) was found. The run continues; install/start the tool and re-run — completed stages aren't repeated.

**Which AI model should I use?**
Anything that follows instructions decently. `llama3.1` (Ollama) is the tested local default. Bigger models → better scripts. Change per agent, per brand, or globally in Settings.

**Can it run fully offline?**
Yes — Ollama + ComfyUI + piper are all local. Strategy then reasons without live web evidence and labels it accordingly. The `echo` provider even demos the pipeline with no AI installed.

**Where is my data? How do I back it up / reset?**
`%LOCALAPPDATA%\LVPP Studio` (installed) or `backend/data` (dev). Copy the folder to back up; delete it to reset. Per-project archives: project page → "Export archive".

**How do I publish to YouTube?**
v1.0 records publishing plans locally; actual upload integration is on the [roadmap](../ROADMAP.md) for v1.1.

**SmartScreen blocks the installer.**
The build is unsigned (no certificate yet — see deployment docs). "More info → Run anyway", or build from source.

**Something broke — where do I look?**
Settings → Application log, [troubleshooting.md](troubleshooting.md), or run the smoke test from a source checkout: `python scripts/smoke.py`.

**GPU requirements?**
None for writing/strategy. Image rendering follows your ComfyUI setup; the wizard sizes workflow expectations by VRAM (≥16 GB → heavy, less → light).
