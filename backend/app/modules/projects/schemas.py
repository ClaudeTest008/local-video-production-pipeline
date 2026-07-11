from datetime import datetime

from app.core.schemas import OrmModel, Timestamped

PIPELINE_STAGES = (
    "idea",
    "research",
    "script",
    "storyboard",
    "prompts",
    "images",
    "video",
    "voice",
    "music",
    "captions",
    "editing",
    "thumbnail",
    "seo",
    "publishing",
    "done",
)


class ProjectCreate(OrmModel):
    name: str
    brand_id: int | None = None
    description: str = ""
    idea: str = ""
    tags: list[str] = []


class ProjectUpdate(OrmModel):
    name: str | None = None
    brand_id: int | None = None
    description: str | None = None
    status: str | None = None
    idea: str | None = None
    tags: list[str] | None = None
    meta: dict | None = None


class ProjectRead(Timestamped):
    name: str
    brand_id: int | None
    description: str
    status: str
    idea: str
    tags: list
    meta: dict


class SnapshotRead(OrmModel):
    id: int
    project_id: int
    label: str
    created_at: datetime
