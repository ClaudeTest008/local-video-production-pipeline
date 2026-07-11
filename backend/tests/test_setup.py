from app.core.ai import registry as ai_registry
from app.core.ai.base import ChatProvider, ChatResponse


class WizardProvider(ChatProvider):
    name = "wizard"

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        return ChatResponse(content=f"wizard[{model}]", model=model, provider=self.name)


ai_registry.register("wizard", WizardProvider)


def test_detect_shape(client):
    d = client.get("/api/system/detect").json()
    assert d["python"]["found"] is True
    assert "found" in d["ffmpeg"] and "found" in d["git"]
    assert "tts" not in d and "whisper" not in d  # v1.2: pure-ComfyUI
    assert "found" in d["ollama"] and "found" in d["comfyui"]
    assert d["workflow_hint"] in ("heavy", "light", "cpu")
    assert isinstance(d["gpus"], list)


def test_setup_flow_sets_runtime_defaults(client):
    assert client.get("/api/system/setup/status").json()["complete"] is False

    done = client.post(
        "/api/system/setup/complete",
        json={"default_chat_provider": "wizard", "default_chat_model": "w-1"},
    ).json()
    assert done["complete"] is True
    assert client.get("/api/system/setup/status").json()["complete"] is True
    assert client.get("/api/settings/default_chat_provider").json() == "wizard"

    # agent with no pinned provider now uses the wizard-set default
    agent = client.post("/api/agents", json={"role": "wizard_test", "name": "W"}).json()
    run = client.post(f"/api/agents/{agent['id']}/run", json={"input": "hi"}).json()
    assert run["provider"] == "wizard" and run["model"] == "w-1"
    assert run["content"] == "wizard[w-1]"
