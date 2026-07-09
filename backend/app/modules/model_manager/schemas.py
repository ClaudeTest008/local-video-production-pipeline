from app.core.schemas import OrmModel, Timestamped


class ManagedModelCreate(OrmModel):
    name: str
    provider: str = "ollama"
    kind: str = "llm"
    location: str = ""
    enabled: bool = True
    meta: dict = {}


class ManagedModelUpdate(OrmModel):
    name: str | None = None
    provider: str | None = None
    kind: str | None = None
    location: str | None = None
    enabled: bool | None = None
    meta: dict | None = None


class ManagedModelRead(Timestamped):
    name: str
    provider: str
    kind: str
    location: str
    enabled: bool
    meta: dict
