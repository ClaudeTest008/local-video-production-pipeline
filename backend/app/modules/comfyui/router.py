from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.events import bus
from app.core.repository import Repository
from app.modules.comfyui.client import ComfyUIClient
from app.modules.comfyui.models import ComfyJob

router = APIRouter(prefix="/comfyui", tags=["comfyui"])


def get_client() -> ComfyUIClient:
    return ComfyUIClient()


Client = Annotated[ComfyUIClient, Depends(get_client)]


def _jobs(db: Annotated[Session, Depends(get_db)]) -> Repository[ComfyJob]:
    return Repository(ComfyJob, db)


Jobs = Annotated[Repository, Depends(_jobs)]


class QueueRequest(BaseModel):
    workflow: dict
    project_id: int | None = None
    workflow_def_id: int | None = None


@router.get("/status")
def status(client: Client) -> dict:
    if not client.is_available():
        return {"available": False, "url": client.base_url}
    return {"available": True, "url": client.base_url, "queue": client.get_queue()}


@router.get("/nodes")
def nodes(client: Client) -> list[dict]:
    try:
        return client.list_nodes()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"ComfyUI unreachable: {e}") from e


@router.get("/models")
def models(client: Client) -> dict:
    if not client.is_available():
        raise HTTPException(503, "ComfyUI unreachable")
    return client.list_models()


@router.post("/queue", status_code=201)
def queue(payload: QueueRequest, client: Client, jobs: Jobs) -> dict:
    try:
        prompt_id = client.queue_prompt(payload.workflow)
    except httpx.HTTPError as e:
        raise HTTPException(503, f"ComfyUI queue failed: {e}") from e
    job = jobs.create(
        project_id=payload.project_id,
        prompt_id=prompt_id,
        workflow=payload.workflow,
        workflow_def_id=payload.workflow_def_id,
    )
    bus.emit("comfyui.job.queued", {"id": job.id, "prompt_id": prompt_id})
    return {"job_id": job.id, "prompt_id": prompt_id}


@router.get("/jobs")
def list_jobs(jobs: Jobs, project_id: int | None = None, offset: int = 0, limit: int = 100):
    return jobs.list(offset=offset, limit=limit, project_id=project_id)


@router.get("/jobs/{job_id}")
def get_job(job_id: int, client: Client, jobs: Jobs) -> dict:
    """Job with live status refresh from ComfyUI history."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, f"job {job_id} not found")
    if job.status == "queued":
        try:
            entry = client.get_history(job.prompt_id)
        except httpx.HTTPError:
            entry = None
        if entry is not None:
            completed = entry.get("status", {}).get("completed", bool(entry.get("outputs")))
            outputs = ComfyUIClient.extract_outputs(entry)
            job = jobs.update(job_id, status="done" if completed else "error", outputs=outputs)
            bus.emit("comfyui.job.finished", {"id": job_id, "status": job.status})
            if job.status == "done":
                bus.emit(
                    "asset.generated",
                    {"job_id": job_id, "project_id": job.project_id, "outputs": outputs},
                )
    return {
        "id": job.id,
        "project_id": job.project_id,
        "prompt_id": job.prompt_id,
        "status": job.status,
        "outputs": job.outputs,
        "created_at": job.created_at,
    }


@router.get("/workflow-stats")
def workflow_stats(db: Annotated[Session, Depends(get_db)]) -> list[dict]:
    """Per-workflow render intelligence: success rate + speed, from job history.

    The orchestrator (and the user) can pick workflows on evidence, not guesses.
    """
    from sqlalchemy import select

    from app.modules.workflows.models import WorkflowDef

    jobs = db.scalars(select(ComfyJob).where(ComfyJob.workflow_def_id.is_not(None))).all()
    by_def: dict[int, list[ComfyJob]] = {}
    for job in jobs:
        by_def.setdefault(job.workflow_def_id, []).append(job)
    stats = []
    for def_id, items in by_def.items():
        wf = db.get(WorkflowDef, def_id)
        done = [j for j in items if j.status == "done"]
        durations = [(j.updated_at - j.created_at).total_seconds() for j in done]
        stats.append(
            {
                "workflow_def_id": def_id,
                "name": wf.name if wf else f"#{def_id}",
                "version": wf.version if wf else None,
                "jobs": len(items),
                "success_rate": round(len(done) / len(items), 3) if items else 0,
                "avg_duration_s": round(sum(durations) / len(durations), 1) if durations else None,
            }
        )
    return sorted(stats, key=lambda s: (-s["success_rate"], s["avg_duration_s"] or 1e9))


@router.post("/interrupt")
def interrupt(client: Client) -> dict:
    try:
        client.interrupt()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"ComfyUI unreachable: {e}") from e
    return {"interrupted": True}
