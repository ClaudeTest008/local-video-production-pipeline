import json

import httpx

from app.main import app
from app.modules.comfyui.client import ComfyUIClient
from app.modules.comfyui.router import get_client

HISTORY = {
    "abc123": {
        "status": {"completed": True},
        "outputs": {"9": {"images": [{"filename": "out.png", "subfolder": "", "type": "output"}]}},
    }
}


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/system_stats":
        return httpx.Response(200, json={"system": {"os": "test"}})
    if path == "/prompt":
        assert json.loads(request.content)["prompt"]
        return httpx.Response(200, json={"prompt_id": "abc123"})
    if path == "/queue":
        return httpx.Response(200, json={"queue_running": [1], "queue_pending": []})
    if path == "/history/abc123":
        return httpx.Response(200, json=HISTORY)
    if path.startswith("/object_info/CheckpointLoaderSimple"):
        return httpx.Response(
            200,
            json={
                "CheckpointLoaderSimple": {
                    "input": {"required": {"ckpt_name": [["sdxl.safetensors"], {}]}}
                }
            },
        )
    if path.startswith("/object_info"):
        return httpx.Response(200, json={"KSampler": {"category": "sampling"}})
    return httpx.Response(404)


def _mock_client() -> ComfyUIClient:
    return ComfyUIClient(base_url="http://comfy.test", transport=httpx.MockTransport(_handler))


def test_client_queue_and_history():
    c = _mock_client()
    assert c.is_available()
    assert c.queue_prompt({"1": {"class_type": "KSampler"}}) == "abc123"
    assert c.get_queue() == {"running": 1, "pending": 0}
    outputs = ComfyUIClient.extract_outputs(c.get_history("abc123"))
    assert outputs == [{"filename": "out.png", "subfolder": "", "type": "output", "kind": "images"}]
    assert c.list_models()["checkpoints"] == ["sdxl.safetensors"]


def test_router_queue_job_and_refresh(client, project):
    app.dependency_overrides[get_client] = _mock_client
    try:
        resp = client.post(
            "/api/comfyui/queue",
            json={"workflow": {"1": {"class_type": "KSampler"}}, "project_id": project["id"]},
        )
        assert resp.status_code == 201
        job_id = resp.json()["job_id"]

        job = client.get(f"/api/comfyui/jobs/{job_id}").json()
        assert job["status"] == "done"
        assert job["outputs"][0]["filename"] == "out.png"

        status = client.get("/api/comfyui/status").json()
        assert status["available"] is True
    finally:
        app.dependency_overrides.pop(get_client, None)


def test_router_unavailable_without_comfy(client):
    def down() -> ComfyUIClient:
        return ComfyUIClient(
            base_url="http://comfy.test",
            transport=httpx.MockTransport(lambda r: httpx.Response(503)),
        )

    app.dependency_overrides[get_client] = down
    try:
        assert client.get("/api/comfyui/status").json()["available"] is False
        assert client.get("/api/comfyui/models").status_code == 503
    finally:
        app.dependency_overrides.pop(get_client, None)
