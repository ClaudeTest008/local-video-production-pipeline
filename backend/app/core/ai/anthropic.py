"""Anthropic Messages API provider."""

import httpx

from app.core.ai.base import ChatProvider, ChatResponse, ProviderError
from app.core.config import settings


class AnthropicProvider(ChatProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.anthropic_api_key

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        system = "\n".join(m.content for m in messages if m.role == "system")
        chat_messages = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }
        if system:
            body["system"] = system
        try:
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json=body,
                timeout=300,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise ProviderError(f"anthropic: {e}") from e
        data = resp.json()
        return ChatResponse(
            content="".join(b.get("text", "") for b in data["content"]),
            model=model,
            provider=self.name,
            usage=data.get("usage", {}),
        )

    def is_available(self) -> bool:
        return bool(self.api_key)
