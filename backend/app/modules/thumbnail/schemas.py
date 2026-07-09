from app.core.schemas import OrmModel, Timestamped


class ThumbnailCreate(OrmModel):
    project_id: int
    title_text: str = ""
    asset_id: int | None = None
    status: str = "draft"
    variants: list = []
    meta: dict = {}


class ThumbnailUpdate(OrmModel):
    title_text: str | None = None
    asset_id: int | None = None
    status: str | None = None
    variants: list | None = None
    meta: dict | None = None


class ThumbnailRead(Timestamped):
    project_id: int
    title_text: str
    asset_id: int | None
    status: str
    variants: list
    meta: dict
