from app.core.schemas import OrmModel, Timestamped


class ResearchNoteCreate(OrmModel):
    project_id: int
    query: str = ""
    content: str = ""
    sources: list = []
    meta: dict = {}


class ResearchNoteUpdate(OrmModel):
    query: str | None = None
    content: str | None = None
    sources: list | None = None
    meta: dict | None = None


class ResearchNoteRead(Timestamped):
    project_id: int
    query: str
    content: str
    sources: list
    meta: dict
