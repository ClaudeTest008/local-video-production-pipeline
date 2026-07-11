from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import files
from app.core.db import get_db
from app.core.events import bus
from app.core.repository import Repository
from app.modules.projects.models import Project, ProjectSnapshot
from app.modules.projects.schemas import (
    PIPELINE_STAGES,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    SnapshotRead,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _repo(db: Annotated[Session, Depends(get_db)]) -> Repository[Project]:
    return Repository(Project, db)


def _get_or_404(r: Repository[Project], project_id: int) -> Project:
    project = r.get(project_id)
    if project is None:
        raise HTTPException(404, f"project {project_id} not found")
    return project


@router.get("", response_model=list[ProjectRead])
def list_projects(
    r: Annotated[Repository, Depends(_repo)],
    offset: int = 0,
    limit: int = 100,
    brand_id: int | None = None,
):
    return r.list(offset=offset, limit=limit, brand_id=brand_id)


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, r: Annotated[Repository, Depends(_repo)]):
    project = r.create(**payload.model_dump())
    files.create_project_tree(project.id)
    bus.emit("project.created", {"id": project.id})
    return project


@router.get("/stages", response_model=list[str])
def pipeline_stages():
    return list(PIPELINE_STAGES)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, r: Annotated[Repository, Depends(_repo)]):
    return _get_or_404(r, project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int, payload: ProjectUpdate, r: Annotated[Repository, Depends(_repo)]
):
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in PIPELINE_STAGES:
        raise HTTPException(422, f"invalid stage; one of {PIPELINE_STAGES}")
    project = r.update(project_id, **data)
    if project is None:
        raise HTTPException(404, f"project {project_id} not found")
    bus.emit("project.updated", {"id": project.id})
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, r: Annotated[Repository, Depends(_repo)]):
    if not r.delete(project_id):
        raise HTTPException(404, f"project {project_id} not found")
    files.delete_project_tree(project_id)
    bus.emit("project.deleted", {"id": project_id})


@router.post("/{project_id}/snapshots", response_model=SnapshotRead, status_code=201)
def create_snapshot(
    project_id: int,
    r: Annotated[Repository, Depends(_repo)],
    db: Annotated[Session, Depends(get_db)],
    label: str = "",
):
    project = _get_or_404(r, project_id)
    data = {
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "idea": project.idea,
        "tags": project.tags,
        "meta": project.meta,
    }
    return Repository(ProjectSnapshot, db).create(project_id=project_id, label=label, data=data)


@router.get("/{project_id}/snapshots", response_model=list[SnapshotRead])
def list_snapshots(project_id: int, db: Annotated[Session, Depends(get_db)]):
    return Repository(ProjectSnapshot, db).list(project_id=project_id)


@router.post("/{project_id}/snapshots/{snapshot_id}/restore", response_model=ProjectRead)
def restore_snapshot(
    project_id: int,
    snapshot_id: int,
    r: Annotated[Repository, Depends(_repo)],
    db: Annotated[Session, Depends(get_db)],
):
    snap = Repository(ProjectSnapshot, db).get(snapshot_id)
    if snap is None or snap.project_id != project_id:
        raise HTTPException(404, f"snapshot {snapshot_id} not found for project {project_id}")
    project = r.update(project_id, **snap.data)
    bus.emit("project.restored", {"id": project_id, "snapshot_id": snapshot_id})
    return project


@router.post("/{project_id}/archive")
def archive(project_id: int, r: Annotated[Repository, Depends(_repo)]):
    _get_or_404(r, project_id)
    files.create_project_tree(project_id)  # ensure tree exists
    path = files.archive_project(project_id)
    return {"archive": str(path)}
