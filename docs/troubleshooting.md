# Troubleshooting

Real failure modes and their fixes, roughly in the order you'll meet them.

## Status bar says "backend offline"

The web UI polls `GET /api/health` every 15 s (`apps/web/components/shell/AppShell.tsx`) and expects the backend at `http://127.0.0.1:8321/api`.

1. Is the backend running? Start it **with the port flag** — plain `uvicorn app.main:app --reload` listens on uvicorn's default 8000, not 8321:

   ```bash
   cd backend
   .venv/Scripts/activate            # Windows
   source .venv/bin/activate         # macOS/Linux
   uvicorn app.main:app --reload --port 8321
   ```

2. Verify directly: open `http://127.0.0.1:8321/api/health` — expect `{"status": "ok", ...}`.
3. Running the backend elsewhere? Point the UI at it with `NEXT_PUBLIC_API_URL` (e.g. `http://127.0.0.1:9000/api`) and restart `npm run dev:web`.

## CORS errors after changing ports

Allowed origins default to `http://localhost:3000` and `tauri://localhost` (`backend/app/core/config.py`). If the web app runs on any other port, the browser blocks responses. Override the list (JSON syntax — it's a `list[str]` setting):

```powershell
# Windows PowerShell
$env:LVPP_CORS_ORIGINS = '["http://localhost:3005"]'
```

```bash
# macOS/Linux
export LVPP_CORS_ORIGINS='["http://localhost:3005"]'
```

Or in `backend/.env`: `LVPP_CORS_ORIGINS=["http://localhost:3005"]`. Restart the backend.

## 503 "ComfyUI unreachable"

`/api/comfyui/*` endpoints return 503 when ComfyUI isn't answering at `LVPP_COMFYUI_URL` (default `http://127.0.0.1:8188`).

- Start ComfyUI and confirm `http://127.0.0.1:8188/system_stats` responds.
- Non-default port/host: set `LVPP_COMFYUI_URL` and restart the backend.
- `GET /api/comfyui/status` reports availability without erroring — use it to probe.

## 502 from chat or agents (provider errors)

Chat and agent runs map `ProviderError` to HTTP 502, with the cause in `detail`.

| Detail looks like | Cause | Fix |
|---|---|---|
| `ollama: [Errno …] connection …` | Ollama not running | `ollama serve`, confirm `http://127.0.0.1:11434/api/tags` |
| `ollama: … 404 …` | Model not pulled | `ollama pull llama3.1` (or the model you configured) |
| `unknown provider 'x'. Known: […]` | Conversation/agent references an unregistered provider | Use a name from `GET /api/settings/providers` |
| `openai/anthropic/gemini: … 401 …` | API key missing/invalid | Set `LVPP_OPENAI_API_KEY` / `LVPP_ANTHROPIC_API_KEY` / `LVPP_GEMINI_API_KEY` / `LVPP_OPENROUTER_API_KEY`, restart backend |

`GET /api/settings/providers` shows a live availability flag per provider — check it first.

## 501 "requires the optional extra"

RAG (`/api/rag/*`) and transcription (`/api/subtitles/transcribe`) are optional extras and return 501 until installed:

```bash
cd backend
pip install -e ".[rag]"         # ChromaDB + sentence-transformers
pip install -e ".[transcribe]"  # faster-whisper
```

Restart the backend. `GET /api/rag/status` confirms availability.

## Timeline export returns `"status": "ffmpeg_missing"`

`POST /api/timelines/{id}/export` builds the FFmpeg command but only runs it if `ffmpeg` is on PATH. The response includes the full `command` so nothing is lost — you can run it by hand.

- Windows: `winget install Gyan.FFmpeg` (new terminal afterwards), or download from ffmpeg.org and add the `bin` folder to PATH.
- macOS: `brew install ffmpeg`. Debian/Ubuntu: `sudo apt install ffmpeg`.
- Verify: `ffmpeg -version`. Restart the backend so the running process sees the new PATH.

## Voice synthesis fails / piper not found

`GET /api/voice/engines` shows `available: false` for `piper` when the binary isn't on PATH; `POST /api/voice/synthesize` then returns a job with `status: "error"` and the cause in `meta.error`.

- Install [piper](https://github.com/rhasspy/piper), put the executable on PATH, restart the backend. Pass a voice model path via the `voice` field.
- Alternatively use the HTTP engines: `xtts` (expects `http://127.0.0.1:8020`) or `kokoro` (`http://127.0.0.1:8880`) — an openedai-speech-style `/v1/audio/speech` server must be running.

## SQLite "database is locked"

The default DB is `backend/data/studio.db`. SQLite allows one writer; a second backend instance, a stuck `seed.py`, or a DB browser (DB Browser for SQLite, DBeaver, a `sqlite3` shell) holding a transaction will lock it.

- Close the other process. Find it on Windows: `Get-Process | Where-Object {$_.Path -like "*python*"}`; Unix: `fuser backend/data/studio.db`.
- Multi-process or heavier use: switch to PostgreSQL — `pip install -e ".[postgres]"` and set `LVPP_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/lvpp`.

## 500 errors after pulling new code ("no such column")

Dev mode creates tables with `create_all`, which never **alters** existing tables — after a schema change your old `backend/data/studio.db` misses new columns and affected endpoints return 500.

- Migrate in place (stop the backend first — SQLite locks): `alembic stamp <previous-revision>` (only if the DB predates Alembic tracking), then `alembic upgrade head`.
- Or, if the data is disposable: delete `backend/data/studio.db` and re-run `python seed.py`.

## Windows: `python` not found or opens the Microsoft Store

Windows ships stub "App execution aliases" for `python`/`python3` that redirect to the Store.

- Settings → Apps → Advanced app settings → **App execution aliases** → turn off both `python.exe` and `python3.exe`, then reopen the terminal; or
- Use the launcher instead: `py -3.12 -m venv .venv`.

## Port already in use (8321 / 3000 / 8188)

Find the holder:

```powershell
# Windows
netstat -ano | findstr :8321
taskkill /PID <pid> /F
```

```bash
# macOS/Linux
lsof -i :8321
kill <pid>
```

Or move: backend `uvicorn app.main:app --port 9000` (then set `NEXT_PUBLIC_API_URL=http://127.0.0.1:9000/api` for the UI, and fix CORS as above); web `npm run dev:web -- -p 3005` (CORS again); ComfyUI → `LVPP_COMFYUI_URL`.

## Type errors across workspaces after adding a package

After adding/renaming anything under `packages/*` (e.g. new exports in `@lvpp/shared`), the editor's TypeScript server keeps stale project references and reports phantom errors that `npm run typecheck` doesn't.

1. `npm install` at the repo root (re-links workspaces).
2. Restart the TS server: VS Code — `Ctrl+Shift+P` → "TypeScript: Restart TS Server".
3. Still failing? Trust the CLI: `npm run typecheck` from the root is the source of truth.

## Still stuck

- Interactive API docs: `http://127.0.0.1:8321/docs` — every module's endpoints, try them live.
- Backend logs print to the uvicorn terminal; event-handler failures are logged, never swallowed silently.
- [installation.md](installation.md) for a clean-slate setup, [development.md](development.md) for test/lint commands.
