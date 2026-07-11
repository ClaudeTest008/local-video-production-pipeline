"""Studio telemetry — one aggregate health endpoint the dashboard polls."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.ai.registry import get_provider, list_providers
from app.core.config import settings
from app.core.db import get_db
from app.core.media import ffmpeg, transcribe, tts
from app.modules.comfyui.client import ComfyUIClient
from app.modules.comfyui.models import ComfyJob
from app.modules.pipeline.models import PipelineRun

router = APIRouter(prefix="/system", tags=["system"])

DB = Annotated[Session, Depends(get_db)]


def _comfy_health() -> dict:
    client = ComfyUIClient()
    if not client.is_available():
        return {"available": False, "url": client.base_url}
    health: dict = {"available": True, "url": client.base_url, "queue": client.get_queue()}
    try:
        devices = client.system_stats().get("devices", [])
        health["devices"] = [
            {
                "name": d.get("name"),
                "vram_total_mb": round(d.get("vram_total", 0) / 1024**2),
                "vram_free_mb": round(d.get("vram_free", 0) / 1024**2),
            }
            for d in devices
        ]
    except Exception:  # stats are decoration, never break health
        health["devices"] = []
    return health


@router.get("/detect")
def detect() -> dict:
    """Full dependency scan for the setup wizard (slow-ish: probes every tool)."""
    from app.modules.system.detect import detect_all

    return detect_all()


@router.get("/setup/status")
def setup_status(db: DB) -> dict:
    from app.modules.settings import service as settings_service

    return {"complete": bool(settings_service.get_value(db, "setup_complete", False))}


@router.post("/setup/complete")
def setup_complete(payload: dict, db: DB) -> dict:
    """Persist wizard choices + intelligent defaults; mark setup done."""
    from app.modules.settings import service as settings_service
    from app.modules.system.detect import detect_all

    detected = detect_all()
    provider = payload.get("default_chat_provider") or (
        "ollama" if detected["ollama"]["found"] else ""
    )
    model = payload.get("default_chat_model") or (
        (detected["ollama"].get("models") or [""])[0] if detected["ollama"]["found"] else ""
    )
    if provider:
        settings_service.set_value(db, "default_chat_provider", provider)
    if model:
        settings_service.set_value(db, "default_chat_model", model)
    settings_service.set_value(db, "workflow_hint", detected["workflow_hint"])
    settings_service.set_value(db, "setup_complete", True)
    return {
        "complete": True,
        "default_chat_provider": provider,
        "default_chat_model": model,
        "workflow_hint": detected["workflow_hint"],
    }


@router.get("/health")
def health(db: DB) -> dict:
    providers = []
    for name in list_providers():
        try:
            providers.append({"name": name, "available": get_provider(name).is_available()})
        except Exception:
            providers.append({"name": name, "available": False})

    def count_runs(status: str) -> int:
        return db.scalar(
            select(func.count()).select_from(PipelineRun).where(PipelineRun.status == status)
        )

    return {
        "backend": "ok",
        "database": settings.database_url.split(":", 1)[0],
        "comfyui": _comfy_health(),
        "providers": providers,
        "engines": {
            "ffmpeg": ffmpeg.has_ffmpeg(),
            "whisper": transcribe.whisper_available(),
            "tts": [{"name": e, "available": tts.engine_available(e)} for e in tts.ENGINES],
        },
        "pipeline": {
            "running": count_runs("running"),
            "errored": count_runs("error"),
        },
        "render_queue": {
            "queued_jobs": db.scalar(
                select(func.count()).select_from(ComfyJob).where(ComfyJob.status == "queued")
            )
        },
    }
