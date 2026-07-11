"""Workflow-graph helpers for the orchestrator."""

import copy

from app.core.events import bus

NEGATIVE_HINTS = ("watermark", "blurry", "deformed", "nsfw", "negative", "worst quality")


def inject_prompt(graph: dict, prompt: str) -> dict:
    """Replace the positive text of an API-format workflow with a new prompt.

    Heuristic: every CLIPTextEncode whose current text does NOT look like a
    negative prompt gets the new text. Unknown graphs pass through unchanged.
    """
    graph = copy.deepcopy(graph)
    for node in graph.values():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs", {})
        class_type = node.get("class_type")
        if class_type == "CLIPTextEncode":
            current = inputs.get("text", "")
            if isinstance(current, str) and not any(h in current.lower() for h in NEGATIVE_HINTS):
                inputs["text"] = prompt
        elif class_type in ("PrimitiveStringMultiline", "PrimitiveString", "CLIPTextEncodeSDXL"):
            # many real graphs route the prompt through a primitive/string node
            current = inputs.get("value", inputs.get("text", ""))
            if isinstance(current, str) and not any(h in current.lower() for h in NEGATIVE_HINTS):
                key = "value" if "value" in inputs else "text"
                inputs[key] = prompt
    return graph


def refresh_job(db, client, job):
    """Pull history for a queued job; persist status + outputs. Returns the job."""
    from app.core.events import bus as _bus
    from app.core.repository import Repository
    from app.modules.comfyui.models import ComfyJob

    if job.status != "queued":
        return job
    try:
        entry = client.get_history(job.prompt_id)
    except Exception:
        return job
    if entry is None:
        return job
    completed = entry.get("status", {}).get("completed", bool(entry.get("outputs")))
    from app.modules.comfyui.client import ComfyUIClient

    outputs = ComfyUIClient.extract_outputs(entry)
    job = Repository(ComfyJob, db).update(
        job.id, status="done" if completed else "error", outputs=outputs
    )
    _bus.emit("comfyui.job.finished", {"id": job.id, "status": job.status})
    return job


def download_output(client, output: dict, dest_dir) -> str:
    """Fetch one rendered output via /view into the project tree (auto-import)."""
    from pathlib import Path

    import httpx as _httpx

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / output["filename"].replace("/", "_")
    resp = _httpx.get(
        f"{client.base_url}/view",
        params={
            "filename": output["filename"],
            "subfolder": output.get("subfolder", ""),
            "type": output.get("type", "output"),
        },
        timeout=300,
    )
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return str(dest)


def record_queued(job) -> None:
    bus.emit(
        "comfyui.job.queued",
        {"id": job.id, "prompt_id": job.prompt_id, "workflow_def_id": job.workflow_def_id},
    )
