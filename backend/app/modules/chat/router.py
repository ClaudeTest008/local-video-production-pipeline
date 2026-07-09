from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.ai import registry as ai_registry
from app.core.ai.base import ChatMessage, ProviderError
from app.core.config import settings
from app.core.db import get_db
from app.core.repository import Repository
from app.modules.chat.models import ChatMsg, Conversation

router = APIRouter(prefix="/chat", tags=["chat"])

DB = Annotated[Session, Depends(get_db)]
HISTORY_LIMIT = 50


class ConversationCreate(BaseModel):
    title: str = ""
    project_id: int | None = None
    provider: str = ""
    model: str = ""


class MessageIn(BaseModel):
    content: str


@router.get("/conversations")
def list_conversations(db: DB, project_id: int | None = None):
    return Repository(Conversation, db).list(project_id=project_id)


@router.post("/conversations", status_code=201)
def create_conversation(payload: ConversationCreate, db: DB):
    return Repository(Conversation, db).create(**payload.model_dump())


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, db: DB):
    if not Repository(Conversation, db).delete(conversation_id):
        raise HTTPException(404, f"conversation {conversation_id} not found")


@router.get("/conversations/{conversation_id}/messages")
def messages(conversation_id: int, db: DB):
    return Repository(ChatMsg, db).list(limit=500, conversation_id=conversation_id)


@router.post("/conversations/{conversation_id}/messages")
def send(conversation_id: int, payload: MessageIn, db: DB) -> dict:
    conversations = Repository(Conversation, db)
    conversation = conversations.get(conversation_id)
    if conversation is None:
        raise HTTPException(404, f"conversation {conversation_id} not found")

    msgs = Repository(ChatMsg, db)
    history = msgs.list(limit=HISTORY_LIMIT, conversation_id=conversation_id)
    chat = [ChatMessage(m.role, m.content) for m in history]
    chat.append(ChatMessage("user", payload.content))

    provider_name = conversation.provider or settings.default_chat_provider
    model = conversation.model or settings.default_chat_model
    try:
        response = ai_registry.get_provider(provider_name).chat(chat, model=model)
    except ProviderError as e:
        raise HTTPException(502, str(e)) from e

    msgs.create(conversation_id=conversation_id, role="user", content=payload.content)
    assistant = msgs.create(
        conversation_id=conversation_id,
        role="assistant",
        content=response.content,
        meta={"provider": response.provider, "model": response.model},
    )
    if not conversation.title:
        conversations.update(conversation_id, title=payload.content[:80])
    return {
        "content": assistant.content,
        "provider": response.provider,
        "model": response.model,
    }
