from app.core.schemas import OrmModel, Timestamped


class PublishJobCreate(OrmModel):
    project_id: int
    platform: str = "youtube"
    status: str = "draft"
    scheduled_at: str = ""
    video_asset_id: int | None = None
    meta: dict = {}


class PublishJobUpdate(OrmModel):
    platform: str | None = None
    status: str | None = None
    scheduled_at: str | None = None
    video_asset_id: int | None = None
    meta: dict | None = None


class PublishJobRead(Timestamped):
    project_id: int
    platform: str
    status: str
    scheduled_at: str
    video_asset_id: int | None
    meta: dict
