"""Ollama — the local-first default provider."""

import httpx

from app.core.ai.base import ChatProvider, ChatResponse, ProviderError
from app.core.config import settings


class OllamaProvider(ChatProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_url).rstrip("/")

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
                timeout=300,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise ProviderError(f"ollama: {e}") from e
        data = resp.json()
        return ChatResponse(
            content=data["message"]["content"],
            model=model,
            provider=self.name,
            usage={"eval_count": data.get("eval_count")},
        )

    def is_available(self) -> bool:
        try:
            return httpx.get(f"{self.base_url}/api/tags", timeout=2).status_code == 200
        except httpx.HTTPError:
            return False

    def list_models(self) -> list[str]:
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except httpx.HTTPError:
            return []
