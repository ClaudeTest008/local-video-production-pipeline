# AI Providers

How LVPP talks to chat models — the `ChatProvider` abstraction, the six built-in providers, and how to add your own.

## The abstraction

Every AI service sits behind one interface (`backend/app/core/ai/base.py`):

```python
class ChatProvider(ABC):
    name: str = "base"

    @abstractmethod
    def chat(self, messages: list[ChatMessage], model: str,
             temperature: float = 0.7, max_tokens: int = 4096) -> ChatResponse: ...

    def is_available(self) -> bool:
        return True
```

`ChatMessage` is `(role, content)` with roles `system | user | assistant`. `ChatResponse` carries `content`, `model`, `provider`, and a provider-specific `usage` dict. Failures raise `ProviderError`, which the API surfaces as HTTP 502.

Providers live in a registry (`backend/app/core/ai/registry.py`): `register(name, factory)` at import time, `get_provider(name)` at call time. Nothing in the chat or agents modules knows which provider it is talking to.

## Built-in providers

| Name | Backend | Config (env, `LVPP_` prefix) | Reports "available" when |
|---|---|---|---|
| `ollama` | Local Ollama (**default**) | `LVPP_OLLAMA_URL` (default `http://127.0.0.1:11434`) | `GET /api/tags` on the Ollama server responds |
| `lmstudio` | Local LM Studio (OpenAI-compatible) | `LVPP_LMSTUDIO_URL` (default `http://127.0.0.1:1234/v1`) | Always (no health probe; a chat call fails if the server is down) |
| `openai` | OpenAI `/v1/chat/completions` | `LVPP_OPENAI_API_KEY` | Always (a chat call fails with 401 if the key is missing/invalid) |
| `openrouter` | OpenRouter `/api/v1/chat/completions` | `LVPP_OPENROUTER_API_KEY` | Always (same caveat as `openai`) |
| `anthropic` | Anthropic Messages API | `LVPP_ANTHROPIC_API_KEY` | The key is set |
| `gemini` | Google `generateContent` REST API | `LVPP_GEMINI_API_KEY` | The key is set |

`openai`, `openrouter`, and `lmstudio` share one implementation, `OpenAICompatProvider` — any server that speaks `/chat/completions` works with it.

Check live availability from the API or the Settings page in the UI:

```bash
curl http://127.0.0.1:8321/api/settings/providers
# [{"name": "anthropic", "available": false}, ..., {"name": "ollama", "available": true}]
```

## How chat and agents pick a provider

Resolution order, most specific wins:

1. **Per-conversation / per-agent override** — chat conversations have `provider` and `model` fields; agent profiles have the same (empty string means "use the app default").
2. **App default** — `LVPP_DEFAULT_CHAT_PROVIDER` (default `ollama`) and `LVPP_DEFAULT_CHAT_MODEL` (default `llama3.1`).

So a fresh install with Ollama running needs zero configuration; a single agent (say, the Script Writer) can be pointed at `anthropic` while everything else stays local.

## Adding a provider

Implement `ChatProvider`, register it — no core changes:

```python
# e.g. in a plugin, or app/core/ai/myprovider.py
import httpx
from app.core.ai.base import ChatProvider, ChatResponse, ProviderError
from app.core.ai.registry import register


class MyProvider(ChatProvider):
    name = "myprovider"

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        try:
            resp = httpx.post("http://127.0.0.1:9999/chat", json={
                "model": model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
            }, timeout=300)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise ProviderError(f"myprovider: {e}") from e
        return ChatResponse(content=resp.json()["text"], model=model, provider=self.name)


register("myprovider", MyProvider)
```

Once the module is imported (plugins are imported at startup), `"myprovider"` is selectable everywhere a provider name is accepted. If your service is OpenAI-compatible, skip the class entirely and register an `OpenAICompatProvider` with your base URL, as `lmstudio` does.

## Privacy

LVPP is local-first: the default provider is Ollama, which needs no API key and sends nothing off your machine. All cloud keys are optional and empty by default. Keys are read from environment variables or `backend/.env` (prefix `LVPP_`) — keep them out of version control; `.env` is gitignored.
