from app.core.schemas import OrmModel, Timestamped


class AssetCreate(OrmModel):
    project_id: int
    path: str
    kind: str = "image"
    source: str = "manual"
    tags: list[str] = []
    meta: dict = {}


class AssetUpdate(OrmModel):
    project_id: int | None = None
    path: str | None = None
    kind: str | None = None
    source: str | None = None
    tags: list[str] | None = None
    meta: dict | None = None


class AssetRead(Timestamped):
    project_id: int
    kind: str
    path: str
    source: str
    tags: list
    meta: dict
