"""Ollama — the local-first default provider."""

import logging

import httpx

from app.core.ai.base import ChatProvider, ChatResponse, ProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(ChatProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_url).rstrip("/")

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        payload_messages = [{"role": m.role, "content": m.content} for m in messages]
        try:
            return self._request(payload_messages, model, temperature, max_tokens)
        except httpx.HTTPStatusError as e:
            # Ollama answers /api/chat with 404 when the model isn't pulled. Rather
            # than fail the whole pipeline over a config default (e.g. llama3.1)
            # the user never installed, fall back to a model that is installed.
            if e.response.status_code != 404:
                raise ProviderError(f"ollama: {e}") from e
            resolved = self._resolve_model(model)
            if resolved == model:
                raise ProviderError(
                    f"ollama: model {model!r} not installed and no other model is "
                    f"available — run `ollama pull {model}` or set "
                    f"LVPP_DEFAULT_CHAT_MODEL to an installed model"
                ) from e
            logger.warning("ollama: model %r not installed, falling back to %r", model, resolved)
            try:
                return self._request(payload_messages, resolved, temperature, max_tokens)
            except httpx.HTTPError as e2:
                raise ProviderError(f"ollama: {e2}") from e2
        except httpx.HTTPError as e:
            raise ProviderError(f"ollama: {e}") from e

    def _request(self, payload_messages, model, temperature, max_tokens) -> ChatResponse:
        resp = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": payload_messages,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=300,
        )
        resp.raise_for_status()
        data = resp.json()
        return ChatResponse(
            content=data["message"]["content"],
            model=model,
            provider=self.name,
            usage={"eval_count": data.get("eval_count")},
        )

    def _resolve_model(self, model: str) -> str:
        """The configured model if installed, else a tag-insensitive match
        (llama3.1 ~ llama3.1:latest), else the first installed model."""
        available = self.list_models()
        if model in available:
            return model
        base = model.split(":")[0]
        for candidate in available:
            if candidate.split(":")[0] == base:
                return candidate
        return available[0] if available else model

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
