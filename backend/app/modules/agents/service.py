"""Agent runner: builds context (system prompt + memory + history), calls the
configured provider, persists the conversation.
"""

import logging

from sqlalchemy.orm import Session

from app.core.ai import registry as ai_registry
from app.core.ai.base import ChatMessage
from app.core.config import settings
from app.core.events import bus
from app.core.repository import Repository
from app.modules.agents.models import AgentConversation, AgentMessage, AgentProfile

HISTORY_LIMIT = 20
logger = logging.getLogger(__name__)


def run_agent(
    db: Session,
    agent: AgentProfile,
    user_input: str,
    project_id: int | None = None,
    conversation_id: int | None = None,
    context: str = "",
    provider_override: str = "",
    model_override: str = "",
) -> tuple[AgentConversation, str, str, str]:
    conversations = Repository(AgentConversation, db)
    messages = Repository(AgentMessage, db)

    conversation = conversations.get(conversation_id) if conversation_id else None
    if conversation is None:
        conversation = conversations.create(
            agent_id=agent.id, project_id=project_id, title=user_input[:80]
        )

    system = agent.system_prompt
    if agent.memory:
        system += f"\n\nPersistent memory:\n{agent.memory}"
    if context:
        system += f"\n\nProject context:\n{context}"

    history = messages.list(limit=HISTORY_LIMIT, conversation_id=conversation.id)
    chat: list[ChatMessage] = [ChatMessage("system", system)]
    chat += [ChatMessage(m.role, m.content) for m in history]
    chat.append(ChatMessage("user", user_input))

    # precedence: agent profile → caller override (brand) → wizard-set default → env default
    from app.modules.settings import service as settings_service

    runtime_provider = settings_service.get_value(db, "default_chat_provider")
    runtime_model = settings_service.get_value(db, "default_chat_model")
    provider_name = (
        agent.provider or provider_override or runtime_provider or settings.default_chat_provider
    )
    model = agent.model or model_override or runtime_model or settings.default_chat_model
    provider = ai_registry.get_provider(provider_name)
    try:
        response = provider.chat(chat, model=model, temperature=agent.temperature)
    except Exception as first_error:
        # failover: one retry on the configured fallback provider (Settings key
        # "fallback_chat_provider"), never the one that just failed
        fallback = settings_service.get_value(db, "fallback_chat_provider")
        fallback_model = settings_service.get_value(db, "fallback_chat_model") or model
        if not fallback or fallback == provider_name:
            raise
        logger.warning(
            "provider %s failed (%s) — failing over to %s", provider_name, first_error, fallback
        )
        response = ai_registry.get_provider(fallback).chat(
            chat, model=fallback_model, temperature=agent.temperature
        )

    messages.create(conversation_id=conversation.id, role="user", content=user_input)
    messages.create(
        conversation_id=conversation.id,
        role="assistant",
        content=response.content,
        meta={"provider": response.provider, "model": response.model, "usage": response.usage},
    )
    bus.emit("agent.ran", {"agent_id": agent.id, "conversation_id": conversation.id})
    return conversation, response.content, response.provider, response.model
