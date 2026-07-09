from app.core.schemas import OrmModel, Timestamped


class PromptCreate(OrmModel):
    project_id: int
    name: str
    text: str = ""
    kind: str = "image"
    version: int = 1
    parent_id: int | None = None
    meta: dict = {}


class PromptUpdate(OrmModel):
    name: str | None = None
    text: str | None = None
    kind: str | None = None
    version: int | None = None
    parent_id: int | None = None
    meta: dict | None = None


class PromptRead(Timestamped):
    id: int
    project_id: int
    name: str
    text: str
    kind: str
    version: int
    parent_id: int | None
    meta: dict
