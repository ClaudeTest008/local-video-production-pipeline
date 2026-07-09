from app.core.schemas import OrmModel, Timestamped


class SceneCreate(OrmModel):
    project_id: int
    order_index: int = 0
    title: str = ""
    description: str = ""
    prompt: str = ""
    duration_s: float = 5.0
    image_asset_id: int | None = None
    meta: dict = {}


class SceneUpdate(OrmModel):
    order_index: int | None = None
    title: str | None = None
    description: str | None = None
    prompt: str | None = None
    duration_s: float | None = None
    image_asset_id: int | None = None
    meta: dict | None = None


class SceneRead(Timestamped):
    project_id: int
    order_index: int
    title: str
    description: str
    prompt: str
    duration_s: float
    image_asset_id: int | None
    meta: dict
