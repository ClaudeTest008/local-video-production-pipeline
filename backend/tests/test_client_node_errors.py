"""queue_prompt must reject 200 responses carrying node_errors — ComfyUI
partially accepts prompts, silently dropping invalid outputs (false success)."""

import httpx
import pytest

from app.modules.comfyui.client import ComfyUIClient


def _client(handler):
    return ComfyUIClient(base_url="http://comfy.test", transport=httpx.MockTransport(handler))


def test_queue_prompt_raises_on_200_with_node_errors():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "prompt_id": "p1",
                "node_errors": {
                    "6088": {
                        "class_type": "LatentUpscaleModelLoader",
                        "errors": [{"message": "Value not in list"}],
                    }
                },
            },
        )

    with pytest.raises(httpx.HTTPStatusError, match="LatentUpscaleModelLoader"):
        _client(handler).queue_prompt({"1": {"class_type": "KSampler", "inputs": {}}})


def test_queue_prompt_ok_on_clean_200():
    def handler(request):
        return httpx.Response(200, json={"prompt_id": "p2", "node_errors": {}})

    assert _client(handler).queue_prompt({}) == "p2"
