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
    meta: dict | None = None


@router.get("")
def list_workflows(workflows: Workflows, kind: str | None = None):
    return workflows.list(limit=500, kind=kind)


@router.post("", status_code=201)
def create_workflow(payload: WorkflowCreate, workflows: Workflows):
    return workflows.create(**payload.model_dump())


@router.get("/{workflow_id}")
def get_workflow(workflow_id: int, workflows: Workflows):
    wf = workflows.get(workflow_id)
    if wf is None:
        raise HTTPException(404, f"workflow {workflow_id} not found")
    return wf


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
