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
        if not isinstance(node, dict) or node.get("class_type") != "CLIPTextEncode":
            continue
        inputs = node.get("inputs", {})
        current = inputs.get("text", "")
        if isinstance(current, str) and not any(h in current.lower() for h in NEGATIVE_HINTS):
            inputs["text"] = prompt
    return graph


def record_queued(job) -> None:
    bus.emit(
        "comfyui.job.queued",
        {"id": job.id, "prompt_id": job.prompt_id, "workflow_def_id": job.workflow_def_id},
    )
