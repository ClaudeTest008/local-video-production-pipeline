from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.repository import Repository
from app.modules.workflows.models import WorkflowDef

router = APIRouter(prefix="/workflows", tags=["workflows"])

DB = Annotated[Session, Depends(get_db)]


def _repo(db: DB) -> Repository[WorkflowDef]:
    return Repository(WorkflowDef, db)


Workflows = Annotated[Repository, Depends(_repo)]


class WorkflowCreate(BaseModel):
    name: str
    kind: str = "comfyui"
    graph: dict = {}


class WorkflowUpdate(BaseModel):
    name: str | None = None
    graph: dict | None = None
    enabled: bool | None = None
    favorite: bool | None = None
    wf_type: str | None = None
    content_types: list[str] | None = None
    meta: dict | None = None


class UploadRequest(BaseModel):
    name: str
    workflow: dict  # UI or API format — converted automatically


@router.get("")
def list_workflows(workflows: Workflows, kind: str | None = None):
    return workflows.list(limit=500, kind=kind)


@router.post("/discover")
def discover(db: DB) -> dict:
    """Import every workflow saved in the user's ComfyUI library (converted
    from UI format automatically; issues recorded, never guessed)."""
    from app.modules.workflows import service

    return service.discover(db)


@router.get("/templates")
def templates() -> dict:
    """The ComfyUI Browse Templates index. Templates become importable once
    saved to the user's library from the ComfyUI UI (listed here for guidance)."""
    from app.modules.comfyui.client import ComfyUIClient

    client = ComfyUIClient()
    if not client.is_available():
        return {"available": False, "templates": {}}
    try:
        return {"available": True, "templates": client.list_templates()}
    except Exception:
        return {"available": True, "templates": {}}


@router.post("/upload", status_code=201)
def upload(payload: UploadRequest, db: DB):
    from app.modules.workflows import service

    return service.upload(db, payload.name, payload.workflow)


@router.get("/selection")
def selection_preview(db: DB, preferred_id: int | None = None) -> dict:
    """What automatic mode would pick right now, and why. When ComfyUI is
    reachable, selection is dependency-aware — ready workflows are preferred
    over ones whose nodes/models are not installed."""
    from app.modules.comfyui.client import ComfyUIClient
    from app.modules.workflows.service import select_workflow

    client = ComfyUIClient()
    object_info = client.object_info() if client.is_available() else None
    wf, note = select_workflow(
        db,
        preferred_id=preferred_id,
        want=("video_lipsync", "avatar", "video"),
        object_info=object_info,
    )
    return {
        "workflow_id": wf.id if wf else None,
        "name": wf.name if wf else None,
        "wf_type": wf.wf_type if wf else None,
        "note": note,
    }


@router.post("", status_code=201)
def create_workflow(payload: WorkflowCreate, workflows: Workflows):
    return workflows.create(**payload.model_dump())


@router.get("/{workflow_id}")
def get_workflow(workflow_id: int, workflows: Workflows):
    wf = workflows.get(workflow_id)
    if wf is None:
        raise HTTPException(404, f"workflow {workflow_id} not found")
    return wf


@router.get("/{workflow_id}/dependencies")
def workflow_dependencies(workflow_id: int, workflows: Workflows) -> dict:
    """Which custom nodes / models this workflow needs that the connected
    ComfyUI lacks — so the UI can guide the user instead of surfacing a raw
    ComfyUI console error. Computed live against the server (no DB storage)."""
    wf = workflows.get(workflow_id)
    if wf is None:
        raise HTTPException(404, f"workflow {workflow_id} not found")
    from app.modules.comfyui.client import ComfyUIClient
    from app.modules.workflows.service import analyze_dependencies

    client = ComfyUIClient()
    if not client.is_available():
        return {"available": False, "workflow_id": workflow_id, "name": wf.name}
    deps = analyze_dependencies(wf.graph, client.object_info())
    return {"available": True, "workflow_id": workflow_id, "name": wf.name, **deps}


@router.patch("/{workflow_id}")
def update_workflow(workflow_id: int, payload: WorkflowUpdate, workflows: Workflows):
    wf = workflows.update(workflow_id, **payload.model_dump(exclude_unset=True))
    if wf is None:
        raise HTTPException(404, f"workflow {workflow_id} not found")
    return wf


@router.delete("/{workflow_id}", status_code=204)
def delete_workflow(workflow_id: int, workflows: Workflows):
    if not workflows.delete(workflow_id):
        raise HTTPException(404, f"workflow {workflow_id} not found")


@router.post("/{workflow_id}/new-version", status_code=201)
def new_version(workflow_id: int, payload: WorkflowUpdate, workflows: Workflows):
    """Immutable versioning: copy the workflow, bump version, link parent."""
    wf = workflows.get(workflow_id)
    if wf is None:
        raise HTTPException(404, f"workflow {workflow_id} not found")
    data = payload.model_dump(exclude_unset=True)
    return workflows.create(
        name=data.get("name", wf.name),
        kind=wf.kind,
        graph=data.get("graph", wf.graph),
        version=wf.version + 1,
        parent_id=wf.id,
        meta=data.get("meta", wf.meta),
    )
