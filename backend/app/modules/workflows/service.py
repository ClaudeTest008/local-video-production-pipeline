"""Workflow discovery, import, and automatic selection.

Users never touch nodes: LVPP consumes workflows that already exist in the
user's ComfyUI (saved library + Browse Templates index) or that they upload
as .json. Selection prefers integrated video+voice/lip-sync workflows.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.repository import Repository
from app.modules.comfyui.client import ComfyUIClient
from app.modules.comfyui.convert import ui_to_api
from app.modules.workflows.classify import MODEL_EXTS, TYPE_PRIORITY, classify
from app.modules.workflows.models import WorkflowDef

logger = logging.getLogger(__name__)


def _upsert(db: Session, name: str, graph: dict, source: str, issues: list[str]) -> WorkflowDef:
    meta = {"conversion_issues": issues, "conversion_status": "check_required" if issues else "ok"}
    info = classify(name, graph)
    existing = db.scalar(
        select(WorkflowDef).where(WorkflowDef.name == name, WorkflowDef.source == source)
    )
    repo = Repository(WorkflowDef, db)
    if existing:
        return repo.update(existing.id, graph=graph, meta={**existing.meta, **meta}, **info)
    return repo.create(name=name, kind="comfyui", graph=graph, source=source, meta=meta, **info)


def discover(db: Session) -> dict:
    """Import every workflow saved in the user's ComfyUI library."""
    client = ComfyUIClient()
    if not client.is_available():
        return {"imported": [], "failed": [], "error": "ComfyUI not reachable"}
    object_info = client.object_info()
    imported, failed = [], []
    for filename in client.list_server_workflows():
        name = filename.rsplit("/", 1)[-1].removesuffix(".json")
        try:
            ui = client.get_server_workflow(filename)
            if "nodes" in ui:  # UI format → convert
                result = ui_to_api(ui, object_info)
                graph, issues = result["graph"], result["issues"]
            else:  # already API format
                graph, issues = ui, []
            wf = _upsert(db, name, graph, "imported", issues)
            imported.append(
                {"id": wf.id, "name": name, "wf_type": wf.wf_type, "issues": len(issues)}
            )
        except Exception as e:
            logger.warning("workflow import failed for %s: %s", filename, e)
            failed.append({"name": name, "error": str(e)[:200]})
    return {"imported": imported, "failed": failed}


def upload(db: Session, name: str, payload: dict) -> WorkflowDef:
    """User-uploaded .json — UI or API format, converted as needed."""
    if "nodes" in payload and isinstance(payload.get("nodes"), list):
        client = ComfyUIClient()
        object_info = client.object_info() if client.is_available() else {}
        result = ui_to_api(payload, object_info)
        graph, issues = result["graph"], result["issues"]
        if not object_info:
            issues.append("converted without a live ComfyUI (widget mapping unverified)")
    else:
        graph, issues = payload, []
    return _upsert(db, name, graph, "uploaded", issues)


def _installed_model_names(object_info: dict) -> set[str]:
    """Every model filename the server offers across all loader combo widgets."""
    names: set[str] = set()
    for info in object_info.values():
        spec = info.get("input", {})
        for section in ("required", "optional"):
            for definition in spec.get(section, {}).values():
                if isinstance(definition, (list, tuple)) and definition and isinstance(
                    definition[0], list
                ):
                    names |= {
                        opt
                        for opt in definition[0]
                        if isinstance(opt, str) and opt.lower().endswith(MODEL_EXTS)
                    }
    return names


def _basename(path: str) -> str:
    return path.replace("\\", "/").rsplit("/", 1)[-1].lower()


def analyze_dependencies(graph: dict, object_info: dict) -> dict:
    """What a converted workflow needs that this server lacks.

    ``missing_nodes`` is authoritative — a class absent from object_info is not
    registered. ``missing_models`` is best-effort: workflows reference models by
    varying subfolder/separator conventions, so a filename counts as present if
    its exact string OR its basename matches an installed model (the basename
    fallback avoids false positives like ``LTXvideo/LTX-2/foo.gguf`` vs ``foo.gguf``).
    """
    installed = _installed_model_names(object_info)
    installed_base = {_basename(m) for m in installed}
    classes = {n.get("class_type") for n in graph.values()}
    missing_nodes = sorted(c for c in classes if c and c not in object_info)
    referenced = {
        value
        for node in graph.values()
        for value in (node.get("inputs") or {}).values()
        if isinstance(value, str) and value.lower().endswith(MODEL_EXTS)
    }
    missing_models = sorted(
        m for m in referenced if m not in installed and _basename(m) not in installed_base
    )
    return {
        "missing_nodes": missing_nodes,
        "missing_models": missing_models,
        "renderable": not missing_nodes and not missing_models,
    }


def _missing_summary(wf: WorkflowDef, object_info: dict) -> list[str]:
    deps = analyze_dependencies(wf.graph, object_info)
    return deps["missing_nodes"] + deps["missing_models"]


def select_workflow(
    db: Session,
    preferred_id: int | None = None,
    want: tuple[str, ...] = (),
    exclude: tuple[int, ...] = (),
    object_info: dict | None = None,
) -> tuple[WorkflowDef | None, str]:
    """Best enabled workflow. Order: explicit preference → favorites → type
    priority (video_lipsync > avatar > video > image) → newest. Returns
    (workflow, note); note explains degradations ("only image workflows").

    When ``object_info`` (the live ComfyUI node registry) is supplied, selection
    becomes dependency-aware: a workflow whose custom nodes or models are not
    installed can never render, so ready workflows are always preferred over
    unrenderable ones regardless of favorite/recency. Automatic mode only falls
    back to an unrenderable workflow when nothing ready exists, and the note
    then names what is missing so the UI can guide the user.
    """
    if preferred_id and preferred_id not in exclude:
        preferred = db.get(WorkflowDef, preferred_id)
        if preferred is not None and preferred.enabled and preferred.graph:
            note = f"brand-preferred workflow '{preferred.name}'"
            if object_info is not None:
                missing = _missing_summary(preferred, object_info)
                if missing:
                    note += f" — warning, not ready; missing: {', '.join(missing[:6])}"
            return preferred, note

    candidates = [
        wf
        for wf in db.scalars(select(WorkflowDef).where(WorkflowDef.kind == "comfyui"))
        if wf.enabled and wf.graph and wf.id not in exclude
    ]
    if want:
        wanted = [wf for wf in candidates if wf.wf_type in want]
        candidates = wanted or candidates
    if not candidates:
        return None, "no enabled ComfyUI workflows — discover or upload one first"

    candidates.sort(
        key=lambda wf: (
            not wf.favorite,
            TYPE_PRIORITY.get(wf.wf_type, 9),
            -(wf.id or 0),
        )
    )

    if object_info is not None:
        ready = [wf for wf in candidates if not _missing_summary(wf, object_info)]
        if ready:
            candidates = ready
        else:
            chosen = candidates[0]
            missing = _missing_summary(chosen, object_info)
            return chosen, (
                f"auto-selected '{chosen.name}' ({chosen.wf_type}) — no ready workflow; "
                f"it needs: {', '.join(missing[:6])}"
            )

    chosen = candidates[0]
    note = f"auto-selected '{chosen.name}' ({chosen.wf_type})"
    if chosen.wf_type == "image":
        note += (
            " — only image workflows available; save or upload a video/lip-sync "
            "workflow for full video generation"
        )
    return chosen, note
