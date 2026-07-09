from app.core.schemas import OrmModel, Timestamped


class ScriptCreate(OrmModel):
    project_id: int
    title: str
    content: str = ""
    version: int = 1
    meta: dict = {}


class ScriptUpdate(OrmModel):
    title: str | None = None
    content: str | None = None
    version: int | None = None
    meta: dict | None = None


class ScriptRead(Timestamped):
    id: int
    project_id: int
    title: str
    content: str
    version: int
    meta: dict
