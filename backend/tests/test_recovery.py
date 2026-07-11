from app.core.ai import registry as ai_registry
from app.core.ai.base import ChatProvider, ChatResponse, ProviderError


class AlwaysFails(ChatProvider):
    name = "always-fails"

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        raise ProviderError("always-fails: down")


class Rescue(ChatProvider):
    name = "rescue"

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        return ChatResponse(content="rescued", model=model, provider=self.name)


ai_registry.register("always-fails", AlwaysFails)
ai_registry.register("rescue", Rescue)


def test_provider_failover(client):
    client.put("/api/settings/fallback_chat_provider", json={"value": "rescue"})
    client.put("/api/settings/fallback_chat_model", json={"value": "r-1"})
    try:
        agent = client.post(
            "/api/agents", json={"role": "failover_test", "name": "F", "provider": "always-fails"}
        ).json()
        run = client.post(f"/api/agents/{agent['id']}/run", json={"input": "hi"})
        assert run.status_code == 200
        assert run.json()["provider"] == "rescue"
        assert run.json()["content"] == "rescued"
    finally:
        client.delete("/api/settings/fallback_chat_provider")
        client.delete("/api/settings/fallback_chat_model")


def test_no_failover_without_config(client):
    agent = client.post(
        "/api/agents", json={"role": "failover_test2", "name": "F2", "provider": "always-fails"}
    ).json()
    assert client.post(f"/api/agents/{agent['id']}/run", json={"input": "hi"}).status_code == 502


def test_logs_endpoint(client):
    result = client.get("/api/system/logs", params={"lines": 50}).json()
    assert "lines" in result and "file" in result
