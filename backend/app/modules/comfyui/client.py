"""Thin ComfyUI HTTP client. Transport injectable for tests (httpx.MockTransport)."""

import uuid

import httpx

from app.core.config import settings

# Node classes whose first widget lists installed model files, keyed by model kind.
MODEL_LOADER_NODES = {
    "checkpoints": ("CheckpointLoaderSimple", "ckpt_name"),
    "loras": ("LoraLoader", "lora_name"),
    "vae": ("VAELoader", "vae_name"),
    "controlnet": ("ControlNetLoader", "control_net_name"),
    "upscale_models": ("UpscaleModelLoader", "model_name"),
}


class ComfyUIClient:
    def __init__(self, base_url: str | None = None, transport: httpx.BaseTransport | None = None):
        self.base_url = (base_url or settings.comfyui_url).rstrip("/")
        self.client_id = uuid.uuid4().hex
        self._http = httpx.Client(base_url=self.base_url, timeout=30, transport=transport)

    def is_available(self) -> bool:
        try:
            return self._http.get("/system_stats", timeout=3).status_code == 200
        except httpx.HTTPError:
            return False

    def system_stats(self) -> dict:
        resp = self._http.get("/system_stats")
        resp.raise_for_status()
        return resp.json()

    def object_info(self, node_class: str | None = None) -> dict:
        path = f"/object_info/{node_class}" if node_class else "/object_info"
        resp = self._http.get(path, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def list_nodes(self) -> list[dict]:
        info = self.object_info()
        return [
            {
                "name": name,
                "category": spec.get("category", ""),
                "display_name": spec.get("display_name", name),
                "output_node": spec.get("output_node", False),
            }
            for name, spec in info.items()
        ]

    def list_models(self) -> dict[str, list[str]]:
        """Installed checkpoints/LoRAs/VAEs/ControlNets, read from loader node inputs."""
        models: dict[str, list[str]] = {}
        for kind, (node_class, input_name) in MODEL_LOADER_NODES.items():
            try:
                spec = self.object_info(node_class)[node_class]
                options = spec["input"]["required"][input_name][0]
                models[kind] = options if isinstance(options, list) else []
            except (httpx.HTTPError, KeyError, IndexError):
                models[kind] = []
        return models

    def queue_prompt(self, workflow: dict) -> str:
        """Submit an API-format workflow; returns ComfyUI prompt_id."""
        resp = self._http.post("/prompt", json={"prompt": workflow, "client_id": self.client_id})
        resp.raise_for_status()
        return resp.json()["prompt_id"]

    def get_queue(self) -> dict:
        resp = self._http.get("/queue")
        resp.raise_for_status()
        data = resp.json()
        return {
            "running": len(data.get("queue_running", [])),
            "pending": len(data.get("queue_pending", [])),
        }

    def get_history(self, prompt_id: str) -> dict | None:
        resp = self._http.get(f"/history/{prompt_id}")
        resp.raise_for_status()
        return resp.json().get(prompt_id)

    def interrupt(self) -> None:
        self._http.post("/interrupt").raise_for_status()

    @staticmethod
    def extract_outputs(history_entry: dict) -> list[dict]:
        """Flatten history outputs to [{filename, subfolder, type, kind}]."""
        outputs = []
        for node_output in history_entry.get("outputs", {}).values():
            for kind in ("images", "gifs", "videos", "audio"):
                for item in node_output.get(kind, []):
                    outputs.append({**item, "kind": kind})
        return outputs

    def output_url(self, filename: str, subfolder: str = "", type_: str = "output") -> str:
        return f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={type_}"
