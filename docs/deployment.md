# Deployment

Running LVPP as a persistent local install: backend as a service, production database, web build options, desktop packaging status, and CI.

LVPP is local-first by design. "Deployment" here means a single machine you own — there is no hosted/multi-tenant mode.

## Backend as a long-running service

Without `--reload`, uvicorn is production-ready for a single-user local install:

```bash
# from backend/, venv active
uvicorn app.main:app --host 127.0.0.1 --port 8321
```

Keep it bound to `127.0.0.1` — the API has no authentication and must not be exposed to a network.

**Windows** — register a Task Scheduler job that runs at logon:

```powershell
$action = New-ScheduledTaskAction -Execute "C:\path\to\repo\backend\.venv\Scripts\uvicorn.exe" `
  -Argument "app.main:app --host 127.0.0.1 --port 8321" `
  -WorkingDirectory "C:\path\to\repo\backend"
Register-ScheduledTask -TaskName "LVPP Backend" -Action $action `
  -Trigger (New-ScheduledTaskTrigger -AtLogOn)
```

**Linux (systemd user unit)** — `~/.config/systemd/user/lvpp-backend.service`:

```ini
[Unit]
Description=LVPP backend

[Service]
WorkingDirectory=/path/to/repo/backend
ExecStart=/path/to/repo/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8321
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable --now lvpp-backend
```

**macOS** — a `launchd` user agent with the same command works; or just run it in a terminal. The desktop shell does not spawn the backend for you today — starting it is your responsibility regardless of platform.

## Switching to PostgreSQL

SQLite (`backend/data/studio.db`) is the default and fine for single-user use. For PostgreSQL:

```bash
pip install -e ".[postgres]"
```

In `backend/.env`:

```
LVPP_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/lvpp
```

Then manage the schema with Alembic instead of relying on startup `create_all` (which still runs, but migrations are the supported path for schema evolution on a database you can't recreate):

```bash
alembic revision --autogenerate -m "initial schema"   # first time only
alembic upgrade head
```

`alembic/env.py` reads `LVPP_DATABASE_URL`, so the same `.env` drives both the app and migrations. Note `alembic/versions/` ships empty — you generate the initial revision yourself. See [development.md](development.md#database-migrations-alembic).

## Web app: server build vs static export

Two modes, selected at build time (`apps/web/next.config.ts`): static export activates when `LVPP_DESKTOP` is set **or** when the build runs under the Tauri CLI (which sets `TAURI_ENV_PLATFORM` for its hook commands — so `tauri build` picks export mode automatically):

**Server build (default)** — for running the web UI in a browser:

```bash
npm run build:web
npm run start --workspace apps/web    # serves on :3000
```

**Static export (desktop shell)** — `LVPP_DESKTOP=1` switches Next.js to `output: "export"`, producing plain files in `apps/web/out/` that the Tauri shell embeds:

```bash
# Windows (PowerShell)
$env:LVPP_DESKTOP = "1"; npm run build:web

# macOS / Linux
LVPP_DESKTOP=1 npm run build:web
```

Project detail uses a query-param route (`/project?id=N`) instead of a dynamic segment specifically so static export works — keep new routes export-compatible (no `[param]` segments without `generateStaticParams`).

## Desktop packaging (Tauri)

The release pipeline, end to end:

1. **Backend sidecar** — from `backend/` (venv active):
   `pyinstaller --noconfirm --onefile --console --name lvpp-backend --collect-submodules app --collect-all sqlalchemy run_server.py`
   then copy `dist/lvpp-backend.exe` to `apps/desktop/src-tauri/binaries/lvpp-backend-x86_64-pc-windows-msvc.exe` (Tauri requires the target triple suffix). The frozen backend stores data under `%LOCALAPPDATA%\LVPP Studio` and exits with the shell (parent-PID watchdog).
2. **Icons** — `python scripts/make_icon.py` regenerates `app-icon.png`; `npx tauri icon ../../app-icon.png` derives all sizes (checked in under `src-tauri/icons/`).
3. **Installer** — `cd apps/desktop && npx tauri build`. `beforeBuildCommand` builds the web static export automatically (`TAURI_ENV_PLATFORM` triggers `output: "export"`); NSIS per-user installer lands at `src-tauri/target/release/bundle/nsis/LVPP Studio_<version>_x64-setup.exe`.
4. **Portable** — zip `target/release/lvpp-desktop.exe` together with the sidecar `lvpp-backend-…exe` from the same folder; both must sit side by side.

### Code signing

Release artifacts are currently **unsigned** (SmartScreen warns on first run). To sign: obtain an OV/EV code-signing certificate, then set `bundle.windows.certificateThumbprint` (+ `digestAlgorithm`, `timestampUrl`) in `tauri.conf.json`, or sign post-build with `signtool sign /sha1 <thumbprint> /tr http://timestamp.digicert.com /td sha256 /fd sha256 <artifact>`. Sign both the installer and the sidecar exe.

### Auto-updates

Not enabled in v1.0 (needs a signing keypair + update server/manifest). Tauri's updater plugin is the intended path — roadmap.

## CI overview

`.github/workflows/ci.yml` runs on pushes to `main` and on pull requests, with two independent jobs:

| Job | Environment | Steps |
|---|---|---|
| `backend` | ubuntu, Python 3.12 | `pip install -e ".[dev]"` → `ruff check app tests` → `black --check app tests` → `pytest -q` |
| `web` | ubuntu, Node 22 | `npm ci` → `npm run typecheck` → `npm run build:web` |

There is no CD: CI verifies, humans deploy (locally). No desktop build runs in CI (no Rust job) — consistent with packaging being a manual step.
