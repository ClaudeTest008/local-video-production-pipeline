"""Provider-agnostic chat interface. Every AI service is replaceable:
implement ChatProvider, call register() — no core changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)


class ChatProvider(ABC):
    name: str = "base"

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResponse: ...

    def is_available(self) -> bool:
        return True


class ProviderError(RuntimeError):
    pass
