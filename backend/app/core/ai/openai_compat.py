"""OpenAI-compatible chat completions — covers OpenAI, LM Studio, OpenRouter,
and any other /v1/chat/completions server with one class.
"""

import httpx

from app.core.ai.base import ChatProvider, ChatResponse, ProviderError


class OpenAICompatProvider(ChatProvider):
    def __init__(self, name: str, base_url: str, api_key: str = "") -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=300,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise ProviderError(f"{self.name}: {e}") from e
        data = resp.json()
        return ChatResponse(
            content=data["choices"][0]["message"]["content"],
            model=model,
            provider=self.name,
            usage=data.get("usage", {}),
        )
