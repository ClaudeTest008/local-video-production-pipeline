from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ai.base import ProviderError
from app.core.db import get_db
from app.core.repository import Repository
from app.modules.agents import service
from app.modules.agents.models import AgentConversation, AgentMessage, AgentProfile
from app.modules.agents.presets import PRESETS
from app.modules.agents.schemas import AgentCreate, AgentRead, AgentUpdate, RunRequest, RunResponse

router = APIRouter(prefix="/agents", tags=["agents"])

DB = Annotated[Session, Depends(get_db)]


def _repo(db: DB) -> Repository[AgentProfile]:
    return Repository(AgentProfile, db)


Agents = Annotated[Repository, Depends(_repo)]


@router.get("/presets")
def presets() -> list[dict]:
    return PRESETS


@router.post("/seed-defaults", response_model=list[AgentRead])
def seed_defaults(db: DB, agents: Agents):
    """Create a profile for every preset role that doesn't exist yet."""
    existing = {a.role for a in db.scalars(select(AgentProfile))}
    return [agents.create(**p) for p in PRESETS if p["role"] not in existing]


@router.get("", response_model=list[AgentRead])
def list_agents(agents: Agents, offset: int = 0, limit: int = 100):
    return agents.list(offset=offset, limit=limit)


@router.post("", response_model=AgentRead, status_code=201)
def create_agent(payload: AgentCreate, agents: Agents):
    return agents.create(**payload.model_dump())


@router.get("/{agent_id}", response_model=AgentRead)
def get_agent(agent_id: int, agents: Agents):
    agent = agents.get(agent_id)
    if agent is None:
        raise HTTPException(404, f"agent {agent_id} not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentRead)
def update_agent(agent_id: int, payload: AgentUpdate, agents: Agents):
    agent = agents.update(agent_id, **payload.model_dump(exclude_unset=True))
    if agent is None:
        raise HTTPException(404, f"agent {agent_id} not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: int, agents: Agents):
    if not agents.delete(agent_id):
        raise HTTPException(404, f"agent {agent_id} not found")


@router.post("/{agent_id}/run", response_model=RunResponse)
def run(agent_id: int, payload: RunRequest, db: DB, agents: Agents):
    agent = agents.get(agent_id)
    if agent is None:
        raise HTTPException(404, f"agent {agent_id} not found")
    try:
        conversation, content, provider, model = service.run_agent(
            db,
            agent,
            payload.input,
            project_id=payload.project_id,
            conversation_id=payload.conversation_id,
            context=payload.context,
        )
    except ProviderError as e:
        raise HTTPException(502, str(e)) from e
    return RunResponse(
        conversation_id=conversation.id, content=content, provider=provider, model=model
    )


@router.get("/{agent_id}/conversations")
def conversations(agent_id: int, db: DB):
    return Repository(AgentConversation, db).list(agent_id=agent_id)


@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: int, db: DB):
    return Repository(AgentMessage, db).list(conversation_id=conversation_id)
