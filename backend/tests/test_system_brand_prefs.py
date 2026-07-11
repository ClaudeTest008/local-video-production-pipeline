from app.modules.comfyui.client import ComfyUIClient
from tests.test_pipeline import _scripted_agents


def test_system_health_shape(client):
    health = client.get("/api/system/health").json()
    assert health["backend"] == "ok"
    assert health["database"] == "sqlite"
    assert "available" in health["comfyui"]
    assert {p["name"] for p in health["providers"]} >= {"ollama", "openai", "scripted"}
    assert health["engines"]["ffmpeg"] in (True, False)
    assert "tts" not in health["engines"] and "whisper" not in health["engines"]
    assert set(health["pipeline"]) == {"running", "errored"}
    assert "queued_jobs" in health["render_queue"]


def test_brand_preferred_provider_drives_pipeline(client):
    """Researcher profile has no provider pinned; the brand's preference wins
    (default ollama would fail — the stage succeeding proves the override)."""
    _scripted_agents(client)
    researcher = next(a for a in client.get("/api/agents").json() if a["role"] == "researcher")
    client.patch(f"/api/agents/{researcher['id']}", json={"provider": "", "model": ""})
    try:
        brand = client.post(
            "/api/brands",
            json={"name": "PrefBrand", "preferred_provider": "scripted", "preferred_model": "m"},
        ).json()
        # brand create schema ignores preferred fields on create — set via update
        client.patch(
            f"/api/brands/{brand['id']}",
            json={"preferred_provider": "scripted", "preferred_model": "m"},
        )
        project = client.post(
            "/api/projects", json={"name": "PrefRun", "brand_id": brand["id"], "idea": "x"}
        ).json()
        run = client.post(
            "/api/pipeline/runs", json={"project_id": project["id"], "mode": "assisted"}
        ).json()
        result = client.post(f"/api/pipeline/runs/{run['id']}/step").json()
        assert result["entry"]["status"] == "done", result["entry"]
    finally:
        client.patch(f"/api/agents/{researcher['id']}", json={"provider": "scripted", "model": "m"})


def test_brand_preferred_workflow_selected(client, monkeypatch):
    _scripted_agents(client)
    preferred = client.post(
        "/api/workflows", json={"name": "brand-wf", "graph": {"1": {"class_type": "KSampler"}}}
    ).json()
    client.post(  # newer workflow exists — preference must still win
        "/api/workflows", json={"name": "newer-wf", "graph": {"2": {"class_type": "KSampler"}}}
    )
    brand = client.post("/api/brands", json={"name": "WfBrand"}).json()
    client.patch(f"/api/brands/{brand['id']}", json={"preferred_workflow_id": preferred["id"]})
    project = client.post(
        "/api/projects", json={"name": "WfRun", "brand_id": brand["id"], "idea": "x"}
    ).json()

    monkeypatch.setattr(ComfyUIClient, "is_available", lambda self: True)
    monkeypatch.setattr(ComfyUIClient, "queue_prompt", lambda self, wf: "brandwf1")
    # renders "finish" instantly with no outputs — the wait loop must exit cleanly
    monkeypatch.setattr(
        ComfyUIClient,
        "get_history",
        lambda self, pid: {"status": {"completed": True}, "outputs": {}},
    )

    run = client.post(
        "/api/pipeline/runs", json={"project_id": project["id"], "mode": "producer"}
    ).json()
    result = client.post(f"/api/pipeline/runs/{run['id']}/run-all").json()
    video = next(e for e in result["entries"] if e["stage"] == "video")
    assert "brand-wf" in video["detail"]

    jobs = client.get("/api/comfyui/jobs", params={"project_id": project["id"]}).json()
    assert jobs and all(j["workflow_def_id"] == preferred["id"] for j in jobs)
