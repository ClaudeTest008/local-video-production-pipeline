"""Deterministic offline provider — no network, no model. Used by the smoke
test and demos so the full pipeline can run on a machine with no AI installed.
Output is shaped so every pipeline parser produces meaningful artifacts."""

from app.core.ai.base import ChatMessage, ChatProvider, ChatResponse


class EchoProvider(ChatProvider):
    name = "echo"

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResponse:
        ask = messages[-1].content
        if "visual scenes" in ask:
            content = (
                "SCENE: Opening hook | 5 | establishing wide shot\n"
                "SCENE: Main point | 10 | detail close-up\n"
                "SCENE: Close | 5 | pull-back reveal"
            )
        elif "SEO pack" in ask:
            content = (
                "TITLE: [echo] Placeholder title\n"
                "DESCRIPTION: Deterministic offline output from the echo provider.\n"
                "TAGS: echo, offline, sample"
            )
        elif ask.startswith("Critique this"):
            content = "Deterministic pass.\nVERDICT: APPROVE"
        else:
            content = f"[echo:{model}] {ask[:400]}"
        return ChatResponse(content=content, model=model, provider=self.name)
