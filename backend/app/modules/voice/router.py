from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import files
from app.core.db import get_db
from app.core.events import bus
from app.core.media import tts
from app.core.repository import Repository
from app.modules.voice.models import VoiceJob

router = APIRouter(prefix="/voice", tags=["voice"])

DB = Annotated[Session, Depends(get_db)]


def _repo(db: DB) -> Repository[VoiceJob]:
    return Repository(VoiceJob, db)


Jobs = Annotated[Repository, Depends(_repo)]


class SynthesizeRequest(BaseModel):
    project_id: int
    text: str
    engine: str = "piper"
    voice: str = ""


@router.get("/engines")
def engines() -> list[dict]:
    return [{"name": e, "available": tts.engine_available(e)} for e in tts.ENGINES]


@router.get("/jobs")
def list_jobs(jobs: Jobs, project_id: int | None = None):
    return jobs.list(project_id=project_id)


@router.post("/synthesize", status_code=201)
def synthesize(payload: SynthesizeRequest, jobs: Jobs):
    if payload.engine not in tts.ENGINES:
        raise HTTPException(422, f"unknown engine '{payload.engine}'; known: {tts.ENGINES}")
    job = jobs.create(**payload.model_dump())
    output = files.project_dir(payload.project_id) / "assets" / "audio" / f"voice-{job.id}.wav"
    try:
        tts.synthesize(payload.engine, payload.text, str(output), voice=payload.voice)
    except Exception as e:
        return jobs.update(job.id, status="error", meta={"error": str(e)[:500]})
    job = jobs.update(job.id, status="done", output_path=str(output))
    bus.emit(
        "asset.generated",
        {"project_id": payload.project_id, "kind": "audio", "path": str(output)},
    )
    return job


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: int, jobs: Jobs):
    if not jobs.delete(job_id):
        raise HTTPException(404, f"job {job_id} not found")
