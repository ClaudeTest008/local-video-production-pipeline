from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import files
from app.core.db import get_db
from app.core.events import bus
from app.core.media import ffmpeg
from app.core.repository import Repository
from app.modules.timeline.models import Timeline

router = APIRouter(prefix="/timelines", tags=["timeline"])

DB = Annotated[Session, Depends(get_db)]


def _repo(db: DB) -> Repository[Timeline]:
    return Repository(Timeline, db)


Timelines = Annotated[Repository, Depends(_repo)]


class TimelineCreate(BaseModel):
    project_id: int
    name: str = "Main"
    tracks: list[dict] = []
    fps: float = 30.0
    resolution: str = "1920x1080"


class TimelineUpdate(BaseModel):
    name: str | None = None
    tracks: list[dict] | None = None
    fps: float | None = None
    resolution: str | None = None
    meta: dict | None = None


class ExportRequest(BaseModel):
    format: Literal["mp4", "mov"] = "mp4"
    run: bool = True  # False = dry-run, return the ffmpeg command only


def _video_clips(timeline: Timeline) -> list[dict]:
    return [
        {"path": clip["path"], "duration": clip.get("duration")}
        for track in timeline.tracks
        if track.get("kind") == "video"
        for clip in track.get("clips", [])
        if clip.get("path")
    ]


@router.get("")
def list_timelines(timelines: Timelines, project_id: int | None = None):
    return timelines.list(project_id=project_id)


@router.post("", status_code=201)
def create_timeline(payload: TimelineCreate, timelines: Timelines):
    return timelines.create(**payload.model_dump())


@router.get("/{timeline_id}")
def get_timeline(timeline_id: int, timelines: Timelines):
    timeline = timelines.get(timeline_id)
    if timeline is None:
        raise HTTPException(404, f"timeline {timeline_id} not found")
    return timeline


@router.patch("/{timeline_id}")
def update_timeline(timeline_id: int, payload: TimelineUpdate, timelines: Timelines):
    timeline = timelines.update(timeline_id, **payload.model_dump(exclude_unset=True))
    if timeline is None:
        raise HTTPException(404, f"timeline {timeline_id} not found")
    return timeline


@router.delete("/{timeline_id}", status_code=204)
def delete_timeline(timeline_id: int, timelines: Timelines):
    if not timelines.delete(timeline_id):
        raise HTTPException(404, f"timeline {timeline_id} not found")


@router.post("/{timeline_id}/export")
def export(timeline_id: int, payload: ExportRequest, timelines: Timelines) -> dict:
    timeline = timelines.get(timeline_id)
    if timeline is None:
        raise HTTPException(404, f"timeline {timeline_id} not found")
    clips = _video_clips(timeline)
    if not clips:
        raise HTTPException(422, "timeline has no video clips")
    output = (
        files.project_dir(timeline.project_id)
        / "exports"
        / f"{timeline.name.replace(' ', '_')}.{payload.format}"
    )
    cmd = ffmpeg.build_concat_command(
        clips, str(output), fps=timeline.fps, resolution=timeline.resolution
    )
    if not payload.run:
        return {"status": "dry_run", "command": cmd}
    if not ffmpeg.has_ffmpeg():
        return {"status": "ffmpeg_missing", "command": cmd}
    proc = ffmpeg.run(cmd)
    if proc.returncode != 0:
        raise HTTPException(500, f"ffmpeg failed: {proc.stderr[-800:]}")
    bus.emit(
        "asset.generated",
        {"project_id": timeline.project_id, "kind": "video", "path": str(output)},
    )
    return {"status": "done", "output": str(output)}
