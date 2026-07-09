from app.core.schemas import OrmModel, Timestamped


class PluginCreate(OrmModel):
    name: str
    path: str = ""
    enabled: bool = False
    manifest: dict = {}
    meta: dict = {}


class PluginUpdate(OrmModel):
    name: str | None = None
    path: str | None = None
    enabled: bool | None = None
    manifest: dict | None = None
    meta: dict | None = None


class PluginRead(Timestamped):
    id: int
    name: str
    path: str
    enabled: bool
    manifest: dict
    meta: dict
