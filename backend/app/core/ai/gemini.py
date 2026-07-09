"""Google Gemini provider (generateContent REST API)."""

import httpx

from app.core.ai.base import ChatProvider, ChatResponse, ProviderError
from app.core.config import settings


class GeminiProvider(ChatProvider):
    name = "gemini"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        system = "\n".join(m.content for m in messages if m.role == "system")
        contents = [
            {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
            for m in messages
            if m.role != "system"
        ]
        body: dict = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        try:
            resp = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": self.api_key},
                json=body,
                timeout=300,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise ProviderError(f"gemini: {e}") from e
        data = resp.json()
        parts = data["candidates"][0]["content"]["parts"]
        return ChatResponse(
            content="".join(p.get("text", "") for p in parts),
            model=model,
            provider=self.name,
            usage=data.get("usageMetadata", {}),
        )

    def is_available(self) -> bool:
        return bool(self.api_key)
