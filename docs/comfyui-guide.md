# ComfyUI Guide

Connecting LVPP to a local ComfyUI instance for image (and video) generation: status, models, queueing workflows, tracking jobs.

## Connecting

LVPP talks to ComfyUI over plain HTTP. Point it at your instance with:

```
LVPP_COMFYUI_URL=http://127.0.0.1:8188   # default
```

(env var or `backend/.env`). Start ComfyUI as usual; LVPP needs no ComfyUI plugins or custom nodes. Verify:

```bash
curl http://127.0.0.1:8321/api/comfyui/status
# {"available": true, "url": "http://127.0.0.1:8188", "queue": {"running": 0, "pending": 0}}
```

The **ComfyUI** page in the web UI (`http://localhost:3000/comfyui`) shows the same status plus models, a workflow paste box, and the job list.

## What the integration does

| Endpoint | What it does |
|---|---|
| `GET /api/comfyui/status` | Reachability + queue depth (`running` / `pending`) |
| `GET /api/comfyui/nodes` | Browse all node classes (name, category, display name) via ComfyUI's `/object_info` |
| `GET /api/comfyui/models` | List installed models by introspecting loader nodes (see below) |
| `POST /api/comfyui/queue` | Submit an API-format workflow; creates a tracked job, returns `job_id` + `prompt_id` |
| `GET /api/comfyui/jobs` | List jobs (filter by `project_id`) |
| `GET /api/comfyui/jobs/{id}` | Job detail with **live status refresh**: while a job is `queued`, LVPP polls ComfyUI's `/history`, flips the job to `done`/`error`, extracts outputs, and emits `asset.generated` on the event bus |
| `POST /api/comfyui/interrupt` | Interrupt the currently running ComfyUI execution |

Outputs are flattened to `[{filename, subfolder, type, kind}]` where `kind` is one of `images`, `gifs`, `videos`, `audio`. Files stay in ComfyUI's output directory; view them via ComfyUI's `/view?filename=...` URL.

## API-format vs UI-format workflows

ComfyUI has two JSON formats and LVPP accepts **only the API format** — a flat map of node id → `{class_type, inputs}`. The default *Save*/*Export* in ComfyUI produces the UI format (with `nodes`, `links`, positions), which ComfyUI's `/prompt` endpoint rejects.

To export the right one:

1. In ComfyUI: **Settings → Enable Dev mode Options** (older UI) or make sure the dev/API export option is on.
2. Use **Save (API Format)** — the exported JSON is what you POST to LVPP.

Quick check: API-format files have top-level numeric keys with `class_type` fields; UI-format files have a top-level `nodes` array.

## Walkthrough: queue the example workflow

The repo ships a minimal SDXL text-to-image workflow at `examples/comfyui-txt2img.json`. Edit `ckpt_name` in node `"4"` to a checkpoint you actually have (see `GET /api/comfyui/models`), then queue it.

Unix / Git Bash:

```bash
curl -X POST http://127.0.0.1:8321/api/comfyui/queue \
  -H "Content-Type: application/json" \
  -d "{\"workflow\": $(cat examples/comfyui-txt2img.json), \"project_id\": 1}"
# {"job_id": 1, "prompt_id": "..."}

curl http://127.0.0.1:8321/api/comfyui/jobs/1
```

Windows PowerShell:

```powershell
$wf = Get-Content examples/comfyui-txt2img.json -Raw | ConvertFrom-Json
$body = @{ workflow = $wf; project_id = 1 } | ConvertTo-Json -Depth 10
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8321/api/comfyui/queue `
  -ContentType "application/json" -Body $body

Invoke-RestMethod http://127.0.0.1:8321/api/comfyui/jobs/1
```

Poll `GET /jobs/{id}` until `status` is `done`; `outputs` then lists the generated files. Passing `project_id` links outputs to that project via the `asset.generated` event.

## Model management

`GET /api/comfyui/models` lists what is installed by reading the option lists of ComfyUI's loader nodes — no filesystem access needed:

| Kind | Loader node inspected |
|---|---|
| `checkpoints` | `CheckpointLoaderSimple` |
| `loras` | `LoraLoader` |
| `vae` | `VAELoader` |
| `controlnet` | `ControlNetLoader` |
| `upscale_models` | `UpscaleModelLoader` |

Scope: **listing only**. Downloading or installing models from LVPP is out of scope today (roadmap item) — install models into ComfyUI's `models/` directories yourself.

## Video workflows

There is nothing image-specific in the pipeline: any API-format workflow ComfyUI can run (AnimateDiff, SVD, etc.) can be queued the same way, and outputs saved as `gifs` or `videos` are picked up by the job's output extraction. LVPP ships no video workflow examples yet — bring your own API-format export.
