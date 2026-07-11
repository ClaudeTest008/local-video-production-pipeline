from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.repository import Repository
from app.modules.subtitles.models import SubtitleTrack
from app.modules.subtitles.service import to_srt, to_vtt

router = APIRouter(prefix="/subtitles", tags=["subtitles"])

DB = Annotated[Session, Depends(get_db)]


def _repo(db: DB) -> Repository[SubtitleTrack]:
    return Repository(SubtitleTrack, db)


Tracks = Annotated[Repository, Depends(_repo)]


class TrackCreate(BaseModel):
    project_id: int
    language: str = "en"
    segments: list[dict] = []


class TrackUpdate(BaseModel):
    language: str | None = None
    segments: list[dict] | None = None


@router.get("")
def list_tracks(tracks: Tracks, project_id: int | None = None):
    return tracks.list(project_id=project_id)


@router.post("", status_code=201)
def create_track(payload: TrackCreate, tracks: Tracks):
    return tracks.create(**payload.model_dump())


@router.patch("/{track_id}")
def update_track(track_id: int, payload: TrackUpdate, tracks: Tracks):
    track = tracks.update(track_id, **payload.model_dump(exclude_unset=True))
    if track is None:
        raise HTTPException(404, f"track {track_id} not found")
    return track


@router.delete("/{track_id}", status_code=204)
def delete_track(track_id: int, tracks: Tracks):
    if not tracks.delete(track_id):
        raise HTTPException(404, f"track {track_id} not found")


@router.get("/{track_id}/export", response_class=PlainTextResponse)
def export_track(track_id: int, tracks: Tracks, fmt: Literal["srt", "vtt"] = "srt") -> str:
    track = tracks.get(track_id)
    if track is None:
        raise HTTPException(404, f"track {track_id} not found")
    return to_srt(track.segments) if fmt == "srt" else to_vtt(track.segments)
