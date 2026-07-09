from app.core.media.ffmpeg import build_concat_command


def test_concat_command_shape():
    cmd = build_concat_command(["a.mp4", "b.mp4"], "out.mp4", fps=24, resolution="1280x720")
    assert cmd[0] == "ffmpeg" and cmd[-1] == "out.mp4"
    assert cmd.count("-i") == 2
    joined = " ".join(cmd)
    assert "concat=n=2" in joined and "1280:720" in joined and "fps=24" in joined


def test_timeline_crud_and_dry_run_export(client, project):
    timeline = client.post(
        "/api/timelines",
        json={
            "project_id": project["id"],
            "tracks": [{"kind": "video", "clips": [{"path": "clip1.mp4"}, {"path": "clip2.mp4"}]}],
        },
    ).json()
    tid = timeline["id"]

    resp = client.post(f"/api/timelines/{tid}/export", json={"format": "mp4", "run": False})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "dry_run"
    assert body["command"][0] == "ffmpeg"
    assert body["command"][-1].endswith("Main.mp4")

    empty = client.post(
        "/api/timelines", json={"project_id": project["id"], "name": "Empty"}
    ).json()
    assert (
        client.post(f"/api/timelines/{empty['id']}/export", json={"run": False}).status_code == 422
    )


def test_workflow_versioning(client):
    wf = client.post(
        "/api/workflows", json={"name": "txt2img", "graph": {"1": {"class_type": "KSampler"}}}
    ).json()
    v2 = client.post(f"/api/workflows/{wf['id']}/new-version", json={"graph": {"2": {}}}).json()
    assert v2["version"] == 2 and v2["parent_id"] == wf["id"]
    assert v2["name"] == "txt2img"


def test_rag_degrades_gracefully(client):
    status = client.get("/api/rag/status").json()
    if not status["available"]:
        assert client.post("/api/rag/query", json={"text": "x"}).status_code == 501
