from app.core.crud_router import crud_router
from app.modules.analytics.models import MetricSnapshot
from app.modules.analytics.schemas import (
    MetricSnapshotCreate,
    MetricSnapshotRead,
    MetricSnapshotUpdate,
)

router = crud_router(
    model=MetricSnapshot,
    create_schema=MetricSnapshotCreate,
    read_schema=MetricSnapshotRead,
    update_schema=MetricSnapshotUpdate,
    prefix="/analytics",
    tag="analytics",
    entity="metric_snapshot",
)
