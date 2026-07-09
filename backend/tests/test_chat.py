from app.core.ai import registry as ai_registry
from app.core.ai.base import ChatProvider, ChatResponse


class EchoProvider(ChatProvider):
    name = "echo"

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        return ChatResponse(content=f"re:{messages[-1].content}", model=model, provider="echo")


ai_registry.register("echo", EchoProvider)


def test_chat_roundtrip(client, project):
    conversation = client.post(
        "/api/chat/conversations",
        json={"project_id": project["id"], "provider": "echo", "model": "m"},
    ).json()
    cid = conversation["id"]

    reply = client.post(f"/api/chat/conversations/{cid}/messages", json={"content": "hello"})
    assert reply.status_code == 200
    assert reply.json()["content"] == "re:hello"

    msgs = client.get(f"/api/chat/conversations/{cid}/messages").json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user" and msgs[1]["role"] == "assistant"

    # title auto-set from first message
    listed = client.get("/api/chat/conversations", params={"project_id": project["id"]}).json()
    assert any(c["title"] == "hello" for c in listed)

    assert client.delete(f"/api/chat/conversations/{cid}").status_code == 204
