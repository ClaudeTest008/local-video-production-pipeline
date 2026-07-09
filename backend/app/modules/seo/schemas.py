from app.core.schemas import OrmModel, Timestamped


class SeoPackCreate(OrmModel):
    project_id: int
    title: str = ""
    description: str = ""
    tags: list = []
    keywords: list = []
    meta: dict = {}


class SeoPackUpdate(OrmModel):
    title: str | None = None
    description: str | None = None
    tags: list | None = None
    keywords: list | None = None
    meta: dict | None = None


class SeoPackRead(Timestamped):
    id: int
    project_id: int
    title: str
    description: str
    tags: list
    keywords: list
    meta: dict
