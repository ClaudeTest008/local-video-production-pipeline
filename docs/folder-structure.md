# Folder structure

Where everything lives: the monorepo layout and the on-disk asset tree LVPP creates for each project.

## Repository tree

```
local-video-production-pipeline/
├── apps/
│   ├── web/                  Next.js UI — app/ has one route folder per feature
│   │                         (projects, studio, canvas, chat, agents, comfyui,
│   │                          assets, timeline, scripts, mcp, analytics, settings)
│   └── desktop/              Tauri 2 shell ("LVPP Studio") wrapping the web UI
│       └── src-tauri/        Rust crate, tauri.conf.json, CSP locked to :8321/:8188
├── packages/
│   ├── shared/               Typed API client (client.ts) + TS types (types.ts);
│   │                         framework-free, used by web and desktop
│   └── ui/                   Minimal UI primitives (primitives.tsx, cn.ts)
├── backend/                  FastAPI backend (Python ≥ 3.11)
│   ├── app/
│   │   ├── main.py           App factory; mounts every discovered router under /api
│   │   ├── core/             db, config, events, repository, crud_router, registry,
│   │   │                     files, ai/ (providers), media/ (ffmpeg)
│   │   └── modules/          23 auto-discovered feature modules (see architecture.md)
│   ├── alembic/              Migrations (production schema changes)
│   ├── tests/                pytest suite, one file per module
│   ├── data/                 Runtime data: studio.db (SQLite) + projects/ file trees
│   ├── seed.py               Idempotent sample data (project, agents, MCP catalog, templates)
│   └── pyproject.toml        Deps + extras: dev, postgres, rag, agents
├── docs/                     This documentation
├── examples/                 pipeline-walkthrough.md + comfyui-txt2img.json workflow
├── .github/workflows/        CI (ci.yml)
├── package.json              npm workspaces root (dev:web, build:web)
└── README.md
```

`backend/data/` is generated at runtime and git-ignored — delete it to reset to a blank studio (re-run `python seed.py` for sample data).

## Per-project asset tree

Creating a project (POST `/api/projects`) creates a matching folder tree on disk; deleting the project removes it. Root: `LVPP_PROJECTS_ROOT` (default `backend/data/projects/`). Defined in `backend/app/core/files.py` (`SUBFOLDERS`).

```
data/projects/project-<id>/
├── research/                 Collected notes and source material
├── scripts/                  Script drafts and exports
├── storyboard/               Scene boards
├── assets/
│   ├── images/               Generated stills (ComfyUI outputs)
│   ├── video/                Rendered clips (timeline/ffmpeg output)
│   ├── audio/                Voiceovers (voice module writes voice-<job>.wav here)
│   ├── music/                Background tracks
│   └── thumbnails/           Thumbnail candidates
├── captions/                 Subtitle files
└── exports/                  Final deliverables; POST /api/projects/<id>/archive
                              zips the whole tree to exports/project-<id>-archive.zip
```

The layout is predictable on purpose: generated outputs land in fixed folders, so you can browse a project in any file manager, sync it, or point external tools at it without asking the API where anything is.
