from app.core.ai import registry as ai_registry
from app.core.ai.base import ChatProvider, ChatResponse


class FakeProvider(ChatProvider):
    name = "fake"

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        assert messages[0].role == "system"
        return ChatResponse(content=f"echo:{messages[-1].content}", model=model, provider=self.name)


ai_registry.register("fake", FakeProvider)


def test_presets_and_seed(client):
    presets = client.get("/api/agents/presets").json()
    assert len(presets) == 14
    assert {p["role"] for p in presets} >= {"script_writer", "producer", "fact_checker"}

    seeded = client.post("/api/agents/seed-defaults").json()
    assert len(seeded) == 14
    assert client.post("/api/agents/seed-defaults").json() == []  # idempotent


def test_agent_run_with_memory_and_history(client, project):
    agent = client.post(
        "/api/agents",
        json={
            "role": "script_writer",
            "name": "Writer",
            "system_prompt": "You write scripts.",
            "provider": "fake",
            "model": "fake-1",
        },
    ).json()

    run1 = client.post(
        f"/api/agents/{agent['id']}/run",
        json={"input": "hook ideas", "project_id": project["id"]},
    )
    assert run1.status_code == 200
    body = run1.json()
    assert body["content"] == "echo:hook ideas"
    assert body["provider"] == "fake"

    # same conversation continues
    run2 = client.post(
        f"/api/agents/{agent['id']}/run",
        json={"input": "more", "conversation_id": body["conversation_id"]},
    ).json()
    assert run2["conversation_id"] == body["conversation_id"]

    msgs = client.get(f"/api/agents/conversations/{body['conversation_id']}/messages").json()
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]

    # configurable settings + memory persist
    updated = client.patch(
        f"/api/agents/{agent['id']}", json={"memory": {"style": "fast-paced"}}
    ).json()
    assert updated["memory"] == {"style": "fast-paced"}


def test_agent_run_unknown_provider(client):
    agent = client.post(
        "/api/agents", json={"role": "x", "name": "X", "provider": "missing-provider"}
    ).json()
    resp = client.post(f"/api/agents/{agent['id']}/run", json={"input": "hi"})
    assert resp.status_code == 502
