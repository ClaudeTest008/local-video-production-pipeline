import httpx

from app.main import app
from app.modules.comfyui.client import ComfyUIClient
from app.modules.comfyui.router import get_client
from app.modules.comfyui.service import inject_prompt


def test_inject_prompt_covers_string_primitives():
    graph = {
        "113": {"class_type": "PrimitiveStringMultiline", "inputs": {"value": "old prompt"}},
        "108": {"class_type": "CLIPTextEncode", "inputs": {"text": ["116", 0]}},  # linked
    }
    out = inject_prompt(graph, "new prompt")
    assert out["113"]["inputs"]["value"] == "new prompt"
    assert out["108"]["inputs"]["text"] == ["116", 0]  # links untouched


def test_inject_prompt_replaces_positive_only():
    graph = {
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "old positive"}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "watermark, blurry"}},
        "3": {"class_type": "KSampler", "inputs": {}},
    }
    out = inject_prompt(graph, "new scene prompt")
    assert out["6"]["inputs"]["text"] == "new scene prompt"
    assert out["7"]["inputs"]["text"] == "watermark, blurry"  # negative untouched
    assert graph["6"]["inputs"]["text"] == "old positive"  # original not mutated


def test_workflow_stats(client):
    workflow = client.post(
        "/api/workflows", json={"name": "stat-wf", "graph": {"1": {"class_type": "KSampler"}}}
    ).json()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/prompt":
            return httpx.Response(200, json={"prompt_id": "stat1"})
        if request.url.path == "/history/stat1":
            return httpx.Response(
                200,
                json={
                    "stat1": {
                        "status": {"completed": True},
                        "outputs": {
                            "9": {
                                "images": [{"filename": "a.png", "subfolder": "", "type": "output"}]
                            }
                        },
                    }
                },
            )
        return httpx.Response(200, json={})

    app.dependency_overrides[get_client] = lambda: ComfyUIClient(
        base_url="http://comfy.test", transport=httpx.MockTransport(handler)
    )
    try:
        queued = client.post(
            "/api/comfyui/queue",
            json={"workflow": {"1": {}}, "workflow_def_id": workflow["id"]},
        ).json()
        client.get(f"/api/comfyui/jobs/{queued['job_id']}")  # refresh -> done

        stats = client.get("/api/comfyui/workflow-stats").json()
        entry = next(s for s in stats if s["workflow_def_id"] == workflow["id"])
        assert entry["jobs"] == 1
        assert entry["success_rate"] == 1.0
        assert entry["name"] == "stat-wf"
    finally:
        app.dependency_overrides.pop(get_client, None)


# --- dependency analysis (pure) -------------------------------------------

from app.modules.workflows.service import analyze_dependencies  # noqa: E402

# object_info: KSampler + a checkpoint loader offering one installed model
_OBJECT_INFO = {
    "KSampler": {"input": {"required": {"seed": ["INT", {}]}}},
    "CheckpointLoaderSimple": {
        "input": {"required": {"ckpt_name": [["model_a.safetensors"], {}]}}
    },
}


def test_analyze_dependencies_flags_missing_node_and_model():
    graph = {
        "1": {"class_type": "KSampler", "inputs": {}},
        "2": {"class_type": "FooCustomNode", "inputs": {}},  # not registered
        "3": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "gone.safetensors"}},
    }
    deps = analyze_dependencies(graph, _OBJECT_INFO)
    assert deps["missing_nodes"] == ["FooCustomNode"]
    assert deps["missing_models"] == ["gone.safetensors"]
    assert deps["renderable"] is False


def test_analyze_dependencies_basename_match_avoids_false_positive():
    # workflow references the model via a subfolder path; server lists the bare
    # filename — must count as present, not missing.
    graph = {
        "1": {"class_type": "KSampler", "inputs": {}},
        "3": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "sd15/model_a.safetensors"},
        },
    }
    deps = analyze_dependencies(graph, _OBJECT_INFO)
    assert deps["missing_models"] == []
    assert deps["missing_nodes"] == []
    assert deps["renderable"] is True
