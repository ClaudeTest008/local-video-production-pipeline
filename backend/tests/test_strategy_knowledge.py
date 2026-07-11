from app.core.ai import registry as ai_registry
from app.core.ai.base import ChatProvider, ChatResponse
from app.core.events import bus


class StrategistProvider(ChatProvider):
    name = "strategist"

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        content = (
            "TOPIC: Lost Roman inventions\nANGLE: engineering mysteries\n"
            "SCORES: growth=8 competition=4 virality=7 evergreen=9 shortform=6 longform=9 "
            "audience_fit=8 urgency=3\nWHY: strong search demand\n---\n"
            "TOPIC: Gladiator economics\nANGLE: follow the money\n"
            "SCORES: growth=6 competition=5 virality=5 evergreen=8 shortform=7 longform=7 "
            "audience_fit=7 urgency=2\nWHY: content gap\n"
        )
        return ChatResponse(content=content, model=model, provider=self.name)


ai_registry.register("strategist", StrategistProvider)


def test_strategy_generate_and_approve(client):
    existing = next(  # first per role — matches get_agent's pick
        (a for a in client.get("/api/agents").json() if a["role"] == "strategy_director"), None
    )
    if existing:
        client.patch(f"/api/agents/{existing['id']}", json={"provider": "strategist", "model": "m"})
    else:
        client.post(
            "/api/agents",
            json={
                "role": "strategy_director",
                "name": "SD",
                "provider": "strategist",
                "model": "m",
            },
        )
    brand = client.post("/api/brands", json={"name": "HistBrand"}).json()

    generated = client.post(
        "/api/strategy/generate", json={"brand_id": brand["id"], "seed_topic": "roman history"}
    )
    assert generated.status_code == 201
    items = generated.json()
    assert len(items) == 2
    assert items[0]["topic"] == "Lost Roman inventions"
    assert items[0]["scores"]["evergreen"] == 9.0

    listed = client.get("/api/strategy/opportunities", params={"brand_id": brand["id"]}).json()
    assert len(listed) >= 2

    approved = client.post(f"/api/strategy/opportunities/{items[0]['id']}/approve").json()
    project = client.get(f"/api/projects/{approved['project_id']}").json()
    assert project["brand_id"] == brand["id"]
    assert "Lost Roman inventions" in project["name"]

    rejected = client.post(f"/api/strategy/opportunities/{items[1]['id']}/reject").json()
    assert rejected["status"] == "rejected"


def test_knowledge_manual_and_digest(client):
    client.post(
        "/api/knowledge",
        json={"kind": "prompt", "insight": "cinematic 35mm prompts outperform", "score": 5},
    )
    client.post("/api/knowledge", json={"kind": "prompt", "insight": "weak insight", "score": 0.1})
    digest = client.get("/api/knowledge/digest").json()["digest"]
    assert "cinematic 35mm" in digest
    listed = client.get("/api/knowledge", params={"kind": "prompt"}).json()
    assert len(listed) >= 2


def test_knowledge_learns_from_analytics_event(client, project):
    snapshot = client.post(
        "/api/analytics",
        json={"project_id": project["id"], "platform": "youtube", "views": 5000, "likes": 200},
    ).json()
    assert snapshot["views"] == 5000
    learnings = client.get("/api/knowledge", params={"kind": "analytics"}).json()
    assert any(str(project["id"]) in learning["key"] for learning in learnings)


def test_knowledge_learns_from_pipeline_failure(client):
    bus.emit("pipeline.stage.failed", {"run_id": 999, "stage": "script"})
    learnings = client.get("/api/knowledge", params={"kind": "pipeline"}).json()
    assert any("script" in learning["key"] for learning in learnings)
