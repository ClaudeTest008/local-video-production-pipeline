def test_voice_engines_listed(client):
    engines = client.get("/api/voice/engines").json()
    assert {e["name"] for e in engines} == {"piper", "xtts", "kokoro"}


def test_voice_unknown_engine(client, project):
    resp = client.post(
        "/api/voice/synthesize",
        json={"project_id": project["id"], "text": "hi", "engine": "bogus"},
    )
    assert resp.status_code == 422


def test_voice_job_graceful_without_engine(client, project):
    resp = client.post("/api/voice/synthesize", json={"project_id": project["id"], "text": "hello"})
    assert resp.status_code == 201
    job = resp.json()
    assert job["status"] in ("done", "error")  # error acceptable: engine not installed
    listed = client.get("/api/voice/jobs", params={"project_id": project["id"]}).json()
    assert any(j["id"] == job["id"] for j in listed)
