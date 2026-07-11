from app.core.schemas import OrmModel, Timestamped


class BrandCreate(OrmModel):
    name: str
    description: str = ""
    voice: str = ""
    style: str = ""
    audience: str = ""
    guidelines: str = ""
    platforms: list[str] = []
    schedule: dict = {}
    goals: str = ""


class BrandUpdate(OrmModel):
    name: str | None = None
    description: str | None = None
    voice: str | None = None
    style: str | None = None
    audience: str | None = None
    guidelines: str | None = None
    platforms: list[str] | None = None
    schedule: dict | None = None
    goals: str | None = None
    memory: dict | None = None


class BrandRead(Timestamped):
    name: str
    description: str
    voice: str
    style: str
    audience: str
    guidelines: str
    platforms: list
    schedule: dict
    goals: str
    memory: dict
    meta: dict
