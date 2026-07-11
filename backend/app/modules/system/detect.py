"""Dependency detection for the setup wizard. Every check degrades to a clear
status + fix hint — never a crash, never silence."""

import platform
import shutil
import subprocess
import sys

import httpx

from app.core.config import settings
from app.core.media import transcribe, tts
from app.modules.comfyui.client import ComfyUIClient


def _cli(name: str, version_args: list[str] | None = None) -> dict:
    path = shutil.which(name)
    result: dict = {"found": path is not None, "path": path}
    if path and version_args:
        try:
            proc = subprocess.run(
                [name, *version_args], capture_output=True, text=True, timeout=10
            )
            result["version"] = (proc.stdout or proc.stderr).strip().splitlines()[0][:120]
        except (subprocess.SubprocessError, OSError, IndexError):
            pass
    return result


def _gpus() -> list[dict]:
    """NVIDIA via nvidia-smi; fall back to ComfyUI's device report. AMD/ROCm
    detection is roadmap — reported as unknown, not absent."""
    if shutil.which("nvidia-smi"):
        try:
            proc = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,memory.free,driver_version",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            gpus = []
            for line in proc.stdout.strip().splitlines():
                name, total, free, driver = [part.strip() for part in line.split(",")]
                gpus.append(
                    {
                        "vendor": "nvidia",
                        "name": name,
                        "vram_total_mb": int(total),
                        "vram_free_mb": int(free),
                        "driver": driver,
                        "cuda": True,
                    }
                )
            if gpus:
                return gpus
        except (subprocess.SubprocessError, OSError, ValueError):
            pass
    client = ComfyUIClient()
    if client.is_available():
        try:
            return [
                {
                    "vendor": "unknown",
                    "name": d.get("name", "GPU"),
                    "vram_total_mb": round(d.get("vram_total", 0) / 1024**2),
                    "vram_free_mb": round(d.get("vram_free", 0) / 1024**2),
                    "cuda": "cuda" in str(d.get("name", "")).lower(),
                }
                for d in client.system_stats().get("devices", [])
            ]
        except httpx.HTTPError:
            pass
    return []


def _ollama() -> dict:
    try:
        resp = httpx.get(f"{settings.ollama_url}/api/tags", timeout=3)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        return {"found": True, "url": settings.ollama_url, "models": models}
    except httpx.HTTPError:
        return {
            "found": False,
            "url": settings.ollama_url,
            "fix": "Install from https://ollama.com and run `ollama pull llama3.1`.",
        }


def _comfyui() -> dict:
    client = ComfyUIClient()
    if not client.is_available():
        return {
            "found": False,
            "url": client.base_url,
            "fix": "Start ComfyUI (https://github.com/comfyanonymous/ComfyUI) or set "
            "LVPP_COMFYUI_URL if it runs elsewhere.",
        }
    result: dict = {"found": True, "url": client.base_url}
    try:
        models = client.list_models()
        result["models"] = {kind: len(names) for kind, names in models.items()}
        result["checkpoints"] = models.get("checkpoints", [])[:20]
    except httpx.HTTPError:
        result["models"] = {}
    return result


def detect_all() -> dict:
    gpus = _gpus()
    vram = max((g["vram_total_mb"] for g in gpus), default=0)
    return {
        "os": f"{platform.system()} {platform.release()}",
        "python": {"found": True, "version": sys.version.split()[0]},
        "ffmpeg": {
            **_cli("ffmpeg", ["-version"]),
            **(
                {}
                if shutil.which("ffmpeg")
                else {"fix": "winget install Gyan.FFmpeg (or apt/brew install ffmpeg)"}
            ),
        },
        "git": _cli("git", ["--version"]),
        "whisper": {
            "found": transcribe.whisper_available(),
            **(
                {}
                if transcribe.whisper_available()
                else {"fix": 'pip install -e ".[transcribe]" inside backend/'}
            ),
        },
        "tts": [{"name": e, "found": tts.engine_available(e)} for e in tts.ENGINES],
        "ollama": _ollama(),
        "comfyui": _comfyui(),
        "gpus": gpus,
        "vram_total_mb": vram,
        # intelligent default: heavier workflows only make sense with >=16 GB VRAM
        "workflow_hint": "heavy" if vram >= 16_000 else "light" if vram > 0 else "cpu",
    }
