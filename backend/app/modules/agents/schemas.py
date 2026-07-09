from app.core.schemas import OrmModel, Timestamped


class AgentCreate(OrmModel):
    role: str
    name: str
    system_prompt: str = ""
    provider: str = ""
    model: str = ""
    temperature: float = 0.7
    settings: dict = {}


class AgentUpdate(OrmModel):
    name: str | None = None
    system_prompt: str | None = None
    provider: str | None = None
    model: str | None = None
    temperature: float | None = None
    settings: dict | None = None
    memory: dict | None = None


class AgentRead(Timestamped):
    role: str
    name: str
    system_prompt: str
    provider: str
    model: str
    temperature: float
    settings: dict
    memory: dict


class RunRequest(OrmModel):
    input: str
    project_id: int | None = None
    conversation_id: int | None = None
    context: str = ""


class RunResponse(OrmModel):
    conversation_id: int
    content: str
    provider: str
    model: str
