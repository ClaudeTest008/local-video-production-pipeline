"""Knowledge engine v1: the studio learns from its own events.

Event subscribers turn operational signals (render outcomes, pipeline failures,
analytics snapshots) into Learning rows; digest() feeds the strongest ones back
into every agent's context. Richer scoring/embedding retrieval is roadmap.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.events import bus
from app.modules.knowledge.models import Learning

logger = logging.getLogger(__name__)

DIGEST_LIMIT = 8


def record(
    db: Session,
    kind: str,
    insight: str,
    key: str = "",
    data: dict | None = None,
    score: float = 0.0,
    brand_id: int | None = None,
    project_id: int | None = None,
) -> Learning:
    learning = Learning(
        kind=kind,
        key=key,
        insight=insight,
        data=data or {},
        score=score,
        brand_id=brand_id,
        project_id=project_id,
    )
    db.add(learning)
    db.commit()
    db.refresh(learning)
    return learning


def digest(db: Session, brand_id: int | None = None) -> str:
    """Compact text block of the strongest learnings, for agent context."""
    stmt = select(Learning).order_by(Learning.score.desc(), Learning.id.desc()).limit(DIGEST_LIMIT)
    if brand_id is not None:
        stmt = stmt.where((Learning.brand_id == brand_id) | (Learning.brand_id.is_(None)))
    rows = list(db.scalars(stmt))
    return "\n".join(f"- [{r.kind}] {r.insight}" for r in rows if r.insight)


# ── event subscribers (registered once at import) ───────────────────────────


def _on_comfy_finished(topic: str, payload: dict) -> None:
    from app.modules.comfyui.models import ComfyJob

    with SessionLocal() as db:
        job = db.get(ComfyJob, payload.get("id"))
        if job is None:
            return
        duration = (job.updated_at - job.created_at).total_seconds()
        ok = job.status == "done"
        record(
            db,
            kind="render",
            key=f"workflow:{job.workflow_def_id}",
            insight=(
                f"workflow #{job.workflow_def_id} {'succeeded' if ok else 'failed'} "
                f"in {duration:.0f}s"
                if job.workflow_def_id
                else ""
            ),
            data={"status": job.status, "duration_s": duration, "outputs": len(job.outputs)},
            score=1.0 if ok else -1.0,
            project_id=job.project_id,
        )


def _on_pipeline_failed(topic: str, payload: dict) -> None:
    with SessionLocal() as db:
        record(
            db,
            kind="pipeline",
            key=f"stage:{payload.get('stage')}",
            insight=f"pipeline stage '{payload.get('stage')}' failed — check provider/model",
            data=payload,
            score=-0.5,
        )


def _on_metric_created(topic: str, payload: dict) -> None:
    from app.modules.analytics.models import MetricSnapshot

    with SessionLocal() as db:
        snapshot = db.get(MetricSnapshot, payload.get("id"))
        if snapshot is None:
            return
        record(
            db,
            kind="analytics",
            key=f"project:{snapshot.project_id}",
            insight=(
                f"project {snapshot.project_id} on {snapshot.platform}: "
                f"{snapshot.views} views, {snapshot.likes} likes"
            ),
            data={"views": snapshot.views, "likes": snapshot.likes},
            score=min(snapshot.views / 1000, 10.0),
            project_id=snapshot.project_id,
        )


_subscribed = False


def subscribe() -> None:
    global _subscribed
    if _subscribed:  # idempotent under repeated imports
        return
    bus.subscribe("comfyui.job.finished", _on_comfy_finished)
    bus.subscribe("pipeline.stage.failed", _on_pipeline_failed)
    bus.subscribe("metric_snapshot.created", _on_metric_created)
    _subscribed = True


subscribe()
