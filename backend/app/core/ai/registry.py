"""Provider registry. Plugins register new providers at import time."""

from collections.abc import Callable

from app.core.ai.anthropic import AnthropicProvider
from app.core.ai.base import ChatProvider, ProviderError
from app.core.ai.gemini import GeminiProvider
from app.core.ai.ollama import OllamaProvider
from app.core.ai.openai_compat import OpenAICompatProvider
from app.core.config import settings

_factories: dict[str, Callable[[], ChatProvider]] = {}


def register(name: str, factory: Callable[[], ChatProvider]) -> None:
    _factories[name] = factory


def get_provider(name: str) -> ChatProvider:
    if name not in _factories:
        raise ProviderError(f"unknown provider '{name}'. Known: {sorted(_factories)}")
    return _factories[name]()


def list_providers() -> list[str]:
    return sorted(_factories)


from app.core.ai.echo import EchoProvider  # noqa: E402

register("echo", EchoProvider)
register("ollama", OllamaProvider)
register("anthropic", AnthropicProvider)
register("gemini", GeminiProvider)
register(
    "openai",
    lambda: OpenAICompatProvider("openai", "https://api.openai.com/v1", settings.openai_api_key),
)
register(
    "openrouter",
    lambda: OpenAICompatProvider(
        "openrouter", "https://openrouter.ai/api/v1", settings.openrouter_api_key
    ),
)
register("lmstudio", lambda: OpenAICompatProvider("lmstudio", settings.lmstudio_url))
