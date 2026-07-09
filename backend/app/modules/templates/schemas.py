from app.core.schemas import OrmModel, Timestamped


class TemplateCreate(OrmModel):
    name: str
    kind: str = "script"
    content: str = ""
    tags: list = []
    meta: dict = {}


class TemplateUpdate(OrmModel):
    name: str | None = None
    kind: str | None = None
    content: str | None = None
    tags: list | None = None
    meta: dict | None = None


class TemplateRead(Timestamped):
    id: int
    name: str
    kind: str
    content: str
    tags: list
    meta: dict
