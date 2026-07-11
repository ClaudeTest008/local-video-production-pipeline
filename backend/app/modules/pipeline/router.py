from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.repository import Repository
from app.modules.pipeline import service
from app.modules.pipeline.models import PipelineRun
from app.modules.projects.models import Project

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

DB = Annotated[Session, Depends(get_db)]

MAX_STAGES_PER_REQUEST = len(service.STAGE_NAMES)


def _runs(db: DB) -> Repository[PipelineRun]:
    return Repository(PipelineRun, db)


Runs = Annotated[Repository, Depends(_runs)]


class RunCreate(BaseModel):
    project_id: int
    mode: Literal["manual", "assisted", "producer"] = "assisted"


def _get_run(db: Session, runs: Repository, run_id: int) -> tuple[PipelineRun, Project]:
    run = runs.get(run_id)
    if run is None:
        raise HTTPException(404, f"run {run_id} not found")
    project = db.get(Project, run.project_id)
    if project is None:
        raise HTTPException(409, f"project {run.project_id} no longer exists")
    return run, project


@router.get("/stages")
def stages() -> list[str]:
    return service.STAGE_NAMES


@router.get("/runs")
def list_runs(runs: Runs, project_id: int | None = None):
    return runs.list(project_id=project_id)


@router.post("/runs", status_code=201)
def create_run(payload: RunCreate, db: DB, runs: Runs):
    if db.get(Project, payload.project_id) is None:
        raise HTTPException(404, f"project {payload.project_id} not found")
    return runs.create(**payload.model_dump())


@router.get("/runs/{run_id}")
def get_run(run_id: int, db: DB, runs: Runs):
    run, _ = _get_run(db, runs, run_id)
    return run


@router.post("/runs/{run_id}/step")
def step(run_id: int, db: DB, runs: Runs):
    """Execute the next stage (assisted mode: review between calls)."""
    run, project = _get_run(db, runs, run_id)
    entry = service.execute_stage(db, run, project)
    return {"entry": entry, "run": runs.get(run_id)}


@router.post("/runs/{run_id}/run-all")
def run_all(run_id: int, db: DB, runs: Runs):
    """Producer mode: run every remaining stage back-to-back.

    Synchronous by design for v1 — local LLM latency applies. Streaming
    progress over WebSocket is on the roadmap.
    """
    run, project = _get_run(db, runs, run_id)
    entries = []
    for _ in range(MAX_STAGES_PER_REQUEST):
        run = runs.get(run_id)
        if service.next_stage(run) is None:
            break
        entry = service.execute_stage(db, run, project)
        entries.append(entry)
        if entry["status"] == "error":
            break
    return {"entries": entries, "run": runs.get(run_id)}


@router.delete("/runs/{run_id}", status_code=204)
def delete_run(run_id: int, runs: Runs):
    if not runs.delete(run_id):
        raise HTTPException(404, f"run {run_id} not found")
