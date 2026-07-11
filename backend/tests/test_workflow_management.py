from app.modules.comfyui.convert import ui_to_api
from app.modules.workflows.classify import classify

OBJECT_INFO = {
    "KSampler": {
        "input": {
            "required": {
                "model": ["MODEL"],
                "seed": ["INT", {"default": 0}],
                "steps": ["INT", {"default": 20}],
                "sampler_name": [["euler", "ddim"]],
                "positive": ["CONDITIONING"],
            }
        }
    },
    "CLIPTextEncode": {
        "input": {"required": {"text": ["STRING", {"multiline": True}], "clip": ["CLIP"]}}
    },
    "CheckpointLoaderSimple": {
        "input": {"required": {"ckpt_name": [["model-a.safetensors", "model-b.safetensors"]]}}
    },
}

UI_GRAPH = {
    "nodes": [
        {
            "id": 1,
            "type": "CheckpointLoaderSimple",
            "inputs": [],
            "outputs": [{"links": [10, 11]}],
            "widgets_values": ["model-a.safetensors"],
        },
        {
            "id": 2,
            "type": "CLIPTextEncode",
            "inputs": [{"name": "clip", "link": 11}],
            "widgets_values": ["a castle at dawn"],
        },
        {"id": 3, "type": "Reroute", "inputs": [{"name": "", "link": 12}], "outputs": []},
        {
            "id": 4,
            "type": "KSampler",
            "inputs": [{"name": "model", "link": 10}, {"name": "positive", "link": 13}],
            # seed + control_after_generate ghost + steps + sampler combo
            "widgets_values": [42, "randomize", 25, "euler"],
        },
        {"id": 5, "type": "Note", "widgets_values": ["ignore me"]},
    ],
    "links": [
        [10, 1, 0, 4, 0, "MODEL"],
        [11, 1, 1, 2, 0, "CLIP"],
        [12, 2, 0, 3, 0, "CONDITIONING"],
        [13, 3, 0, 4, 1, "CONDITIONING"],
    ],
}


def test_ui_to_api_conversion():
    result = ui_to_api(UI_GRAPH, OBJECT_INFO)
    graph, issues = result["graph"], result["issues"]
    assert issues == []
    assert "5" not in graph and "3" not in graph  # notes + reroutes dropped
    assert graph["2"]["inputs"]["text"] == "a castle at dawn"
    assert graph["2"]["inputs"]["clip"] == ["1", 1]
    ks = graph["4"]["inputs"]
    assert ks["model"] == ["1", 0]
    assert ks["positive"] == ["2", 0]  # reroute chain resolved to the producer
    assert ks["seed"] == 42 and ks["steps"] == 25 and ks["sampler_name"] == "euler"
    assert graph["1"]["inputs"]["ckpt_name"] == "model-a.safetensors"


def test_ui_to_api_reports_unknown_nodes():
    ui = {
        "nodes": [{"id": 9, "type": "MysteryNode", "inputs": [], "widgets_values": []}],
        "links": [],
    }
    result = ui_to_api(ui, OBJECT_INFO)
    assert "9" in result["graph"]
    assert any("unknown class" in issue for issue in result["issues"])


def test_classify():
    lipsync = classify(
        "LTX 2.3 Dual Character Lip Sync",
        {
            "1": {
                "class_type": "LTXVideoSampler",
                "inputs": {"model": "ltx-2.3-22b-dev-fp8.safetensors"},
            }
        },
    )
    assert lipsync["wf_type"] == "video_lipsync"
    assert lipsync["models"] == ["ltx-2.3-22b-dev-fp8.safetensors"]
    assert lipsync["vram_estimate_mb"] == 24_000

    image = classify("ernie turbo", {"1": {"class_type": "SaveImage", "inputs": {}}})
    assert image["wf_type"] == "image"

    avatar = classify("LongCat Video Avatar", {"1": {"class_type": "SaveVideo", "inputs": {}}})
    assert avatar["wf_type"] == "avatar"

    # a utility/LLM graph that only LOADS media (no sampler/save/decode) is not a
    # video candidate, even though LoadVideo/LoadAudio match the media hints
    util = classify(
        "llm text gen",
        {
            "1": {"class_type": "TextGenerate", "inputs": {}},
            "2": {"class_type": "LoadVideo", "inputs": {}},
            "3": {"class_type": "LoadAudio", "inputs": {}},
            "4": {"class_type": "PreviewAny", "inputs": {}},
        },
    )
    assert util["wf_type"] == "other"


def test_upload_and_selection(client):
    # image workflow uploaded (API format)
    image = client.post(
        "/api/workflows/upload",
        json={"name": "sel-image", "workflow": {"1": {"class_type": "SaveImage", "inputs": {}}}},
    ).json()
    assert image["wf_type"] == "image" and image["source"] == "uploaded"

    pick = client.get("/api/workflows/selection").json()
    assert pick["workflow_id"] is not None
    # with only image workflows, automatic mode says so
    if pick["wf_type"] == "image":
        assert "only image workflows" in pick["note"]

    video = client.post(
        "/api/workflows/upload",
        json={
            "name": "sel-lipsync video",
            "workflow": {
                "1": {"class_type": "LTXVideoSampler", "inputs": {}},
                "2": {"class_type": "SaveVideo", "inputs": {}},
            },
        },
    ).json()
    assert video["wf_type"] in ("video", "video_lipsync")

    pick = client.get("/api/workflows/selection").json()
    assert pick["workflow_id"] == video["id"]  # video beats image

    # disabled workflows are never selected
    client.patch(f"/api/workflows/{video['id']}", json={"enabled": False})
    pick = client.get("/api/workflows/selection").json()
    assert pick["workflow_id"] != video["id"]

    # capability trumps favorite: a favorited image wf never beats a video wf
    client.patch(f"/api/workflows/{video['id']}", json={"enabled": True})
    client.patch(f"/api/workflows/{image['id']}", json={"favorite": True})
    pick = client.get("/api/workflows/selection").json()
    assert pick["workflow_id"] == video["id"]

    # but favorites win within the capable pool
    video2 = client.post(
        "/api/workflows/upload",
        json={"name": "sel-video-2", "workflow": {"1": {"class_type": "SaveVideo", "inputs": {}}}},
    ).json()
    client.patch(f"/api/workflows/{video['id']}", json={"favorite": True})
    pick = client.get("/api/workflows/selection").json()
    assert pick["workflow_id"] == video["id"] != video2["id"]


def test_ui_format_upload_converts(client, monkeypatch):
    from app.modules.comfyui.client import ComfyUIClient

    monkeypatch.setattr(ComfyUIClient, "is_available", lambda self: True)
    monkeypatch.setattr(ComfyUIClient, "object_info", lambda self, *a: OBJECT_INFO)
    uploaded = client.post(
        "/api/workflows/upload", json={"name": "ui-upload", "workflow": UI_GRAPH}
    ).json()
    assert uploaded["graph"]["2"]["inputs"]["text"] == "a castle at dawn"
    assert uploaded["meta"]["conversion_status"] == "ok"


def test_selection_prefers_renderable_over_newer_unready(client, monkeypatch):
    from app.modules.comfyui import client as comfy_client_mod

    # isolate from workflows left by earlier tests in this session-scoped client
    for wf in client.get("/api/workflows").json():
        client.delete(f"/api/workflows/{wf['id']}")

    # object_info registers KSampler+SaveVideo but NOT MissingVideoNode
    fake_oi = {
        "KSampler": {"input": {"required": {}}},
        "SaveVideo": {"input": {"required": {}}},
    }
    monkeypatch.setattr(comfy_client_mod.ComfyUIClient, "is_available", lambda self: True)
    monkeypatch.setattr(comfy_client_mod.ComfyUIClient, "object_info", lambda self, *a, **k: fake_oi)

    ready = client.post(
        "/api/workflows/upload",
        json={"name": "ready-video", "workflow": {
            "1": {"class_type": "KSampler", "inputs": {}},
            "2": {"class_type": "SaveVideo", "inputs": {}},
        }},
    ).json()
    # newer AND favorited, but references an unregistered node -> not renderable
    broken = client.post(
        "/api/workflows/upload",
        json={"name": "broken-video", "workflow": {
            "1": {"class_type": "MissingVideoNode", "inputs": {}},
            "2": {"class_type": "SaveVideo", "inputs": {}},
        }},
    ).json()
    client.patch(f"/api/workflows/{broken['id']}", json={"favorite": True})

    pick = client.get("/api/workflows/selection").json()
    assert pick["workflow_id"] == ready["id"]  # ready beats newer+favorited-but-broken

    # when the only candidate is unrenderable, it is still returned WITH the missing list
    client.patch(f"/api/workflows/{ready['id']}", json={"enabled": False})
    pick = client.get("/api/workflows/selection").json()
    assert pick["workflow_id"] == broken["id"]
    assert "MissingVideoNode" in pick["note"]
