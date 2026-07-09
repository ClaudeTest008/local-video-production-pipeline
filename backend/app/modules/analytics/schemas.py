from app.core.schemas import OrmModel, Timestamped


class MetricSnapshotCreate(OrmModel):
    project_id: int
    platform: str = "youtube"
    views: int = 0
    likes: int = 0
    comments: int = 0
    watch_time_h: float = 0.0
    captured_at: str = ""
    meta: dict = {}


class MetricSnapshotUpdate(OrmModel):
    platform: str | None = None
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    watch_time_h: float | None = None
    captured_at: str | None = None
    meta: dict | None = None


class MetricSnapshotRead(Timestamped):
    project_id: int
    platform: str
    views: int
    likes: int
    comments: int
    watch_time_h: float
    captured_at: str
    meta: dict
