from app.core.ai import registry as ai_registry
from app.core.ai.base import ChatProvider, ChatResponse
from app.modules.pipeline import parsers


class ScriptedProvider(ChatProvider):
    """Role-aware canned outputs so every parser path is exercised."""

    name = "scripted"

    def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
        ask = messages[-1].content
        if "visual scenes" in ask:
            content = (
                "SCENE: Opening | 5 | drone over ruins\n"
                "SCENE: The fall | 8.5 | close-up of crumbling column"
            )
        elif "SEO pack" in ask:
            content = "TITLE: Why Rome Fell\nDESCRIPTION: The real story.\nTAGS: rome, history"
        elif "Critique this script" in ask:
            content = "1. Hook is weak — open on the sack of the city.\nVERDICT: REVISE"
        elif "Revise the script" in ask:
            content = "revised script: opens on the sack of the city"
        elif ask.startswith("Critique this"):
            content = "Solid work.\nVERDICT: APPROVE"
        else:
            content = f"generated: {ask[:60]}"
        return ChatResponse(content=content, model=model, provider=self.name)


ai_registry.register("scripted", ScriptedProvider)

ROLES = (
    "researcher",
    "script_writer",
    "storyboard_artist",
    "prompt_engineer",
    "seo_specialist",
    "thumbnail_designer",
    "creative_director",
)


def _scripted_agents(client):
    """Point each role's profile at the scripted provider (upsert — other tests
    may have seeded default profiles first)."""
    existing: dict[str, int] = {}
    for a in client.get("/api/agents").json():  # get_agent uses the first per role
        existing.setdefault(a["role"], a["id"])
    for role in ROLES:
        if role in existing:
            client.patch(
                f"/api/agents/{existing[role]}", json={"provider": "scripted", "model": "m"}
            )
        else:
            client.post(
                "/api/agents",
                json={"role": role, "name": role, "provider": "scripted", "model": "m"},
            )


def test_producer_run_full_pipeline(client):
    _scripted_agents(client)
    brand = client.post(
        "/api/brands", json={"name": "TestBrand", "voice": "epic", "goals": "growth"}
    ).json()
    project = client.post(
        "/api/projects",
        json={"name": "Rome Falls", "brand_id": brand["id"], "idea": "why rome fell"},
    ).json()
    pid = project["id"]

    run = client.post("/api/pipeline/runs", json={"project_id": pid, "mode": "producer"})
    assert run.status_code == 201
    run_id = run.json()["id"]

    result = client.post(f"/api/pipeline/runs/{run_id}/run-all").json()
    statuses = {e["stage"]: e["status"] for e in result["entries"]}

    assert statuses["research"] == "done"
    assert statuses["script"] == "done"
    assert statuses["storyboard"] == "done"
    assert statuses["prompts"] == "done"
    assert statuses["video"] == "skipped"  # no ComfyUI in tests
    assert "voice" not in statuses  # v1.2: voice/lip-sync comes from ComfyUI workflows
    assert statuses["captions"] == "done"
    assert statuses["seo"] == "done"
    assert statuses["thumbnail"] == "done"
    assert result["run"]["status"] == "done"

    scenes = client.get("/api/storyboard", params={"project_id": pid}).json()
    assert len(scenes) == 2
    assert scenes[0]["title"] == "Opening" and scenes[1]["duration_s"] == 8.5
    assert all(s["prompt"].startswith("generated:") for s in scenes)

    seo = client.get("/api/seo", params={"project_id": pid}).json()
    assert seo[0]["title"] == "Why Rome Fell" and "rome" in seo[0]["tags"]

    tracks = client.get("/api/subtitles", params={"project_id": pid}).json()
    assert tracks and len(tracks[0]["segments"]) >= 1  # captions from the script

    # quality review loop: Creative Director demanded a revision; script was rewritten
    scripts = client.get("/api/scripts", params={"project_id": pid}).json()
    assert scripts[0]["content"].startswith("revised script:")
    assert scripts[0]["meta"]["revised"] is True
    assert "VERDICT: REVISE" in scripts[0]["meta"]["critique"]

    assert client.get(f"/api/projects/{pid}").json()["status"] == "thumbnail"


def test_assisted_step(client):
    _scripted_agents(client)
    project = client.post("/api/projects", json={"name": "StepWise", "idea": "x"}).json()
    run = client.post(
        "/api/pipeline/runs", json={"project_id": project["id"], "mode": "assisted"}
    ).json()
    first = client.post(f"/api/pipeline/runs/{run['id']}/step").json()
    assert first["entry"]["stage"] == "research"
    second = client.post(f"/api/pipeline/runs/{run['id']}/step").json()
    assert second["entry"]["stage"] == "script"
    assert client.get(f"/api/projects/{project['id']}").json()["status"] == "script"


def test_background_run_and_recovery(client):
    import time

    _scripted_agents(client)
    project = client.post("/api/projects", json={"name": "BG Run", "idea": "x"}).json()
    run = client.post(
        "/api/pipeline/runs", json={"project_id": project["id"], "mode": "producer"}
    ).json()

    started = client.post(
        f"/api/pipeline/runs/{run['id']}/run-all", params={"background": "true"}
    ).json()
    assert started == {"started": True, "run_id": run["id"]}

    status = "running"
    for _ in range(100):
        status = client.get(f"/api/pipeline/runs/{run['id']}").json()["status"]
        if status in ("done", "error"):
            break
        time.sleep(0.1)
    assert status == "done"

    finished = client.get(f"/api/pipeline/runs/{run['id']}").json()
    assert {e["stage"] for e in finished["log"]} == set(client.get("/api/pipeline/stages").json())


def test_step_retries_failed_stage(client):
    calls = {"n": 0}

    class FlakyProvider(ChatProvider):
        name = "flaky"

        def chat(self, messages, model, temperature=0.7, max_tokens=4096) -> ChatResponse:
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("model crashed")
            return ChatResponse(content="recovered research", model=model, provider=self.name)

    ai_registry.register("flaky", FlakyProvider)
    _scripted_agents(client)
    researcher = next(a for a in client.get("/api/agents").json() if a["role"] == "researcher")
    client.patch(f"/api/agents/{researcher['id']}", json={"provider": "flaky"})
    try:
        project = client.post("/api/projects", json={"name": "Flaky", "idea": "x"}).json()
        run = client.post(
            "/api/pipeline/runs", json={"project_id": project["id"], "mode": "assisted"}
        ).json()

        first = client.post(f"/api/pipeline/runs/{run['id']}/step").json()
        assert first["entry"] == {
            "stage": "research",
            "status": "error",
            "detail": "model crashed",
        }
        assert first["run"]["status"] == "error"

        retry = client.post(f"/api/pipeline/runs/{run['id']}/step").json()
        assert retry["entry"]["stage"] == "research"
        assert retry["entry"]["status"] == "done"
    finally:
        client.patch(f"/api/agents/{researcher['id']}", json={"provider": "scripted"})


def test_parsers_fallbacks():
    assert parsers.parse_scenes("no markers at all")[0]["title"] == "Full piece"
    scenes = parsers.parse_scenes("SCENE: A | not-a-number | desc")
    assert scenes[0]["duration_s"] == 5.0

    seo = parsers.parse_seo("just a headline\nand body")
    assert seo["title"] == "just a headline"

    opportunities = parsers.parse_opportunities(
        "TOPIC: Roman coins\nANGLE: hidden economy\nSCORES: growth=8 virality=6.5\n"
        "WHY: search up\n---\nnoise"
    )
    assert opportunities[0]["scores"]["growth"] == 8.0
    assert opportunities[0]["angle"] == "hidden economy"
    assert len(opportunities) == 1
