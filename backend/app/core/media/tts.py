"""Text-to-speech engine adapters. Each engine is replaceable; availability probed, never assumed.

- piper: local CLI (https://github.com/rhasspy/piper)
- xtts / kokoro: local HTTP servers (openedai-speech style /v1/audio/speech)
"""

import shutil
import subprocess
from pathlib import Path

import httpx

ENGINES = ("piper", "xtts", "kokoro")

# Default local endpoints for HTTP engines; override per-call via endpoint arg.
HTTP_ENGINE_URLS = {
    "xtts": "http://127.0.0.1:8020/v1/audio/speech",
    "kokoro": "http://127.0.0.1:8880/v1/audio/speech",
}


def engine_available(engine: str) -> bool:
    if engine == "piper":
        return shutil.which("piper") is not None
    url = HTTP_ENGINE_URLS.get(engine)
    if not url:
        return False
    try:
        base = url.split("/v1/")[0]
        return httpx.get(base + "/health", timeout=2).status_code < 500
    except httpx.HTTPError:
        return False


def synthesize(
    engine: str, text: str, output_path: str, voice: str = "", endpoint: str = ""
) -> None:
    """Write speech audio to output_path. Raises RuntimeError with a clear message on failure."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if engine == "piper":
        model_args = ["--model", voice] if voice else []
        proc = subprocess.run(
            ["piper", *model_args, "--output_file", output_path],
            input=text,
            text=True,
            capture_output=True,
            timeout=600,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"piper failed: {proc.stderr[:500]}")
        return
    url = endpoint or HTTP_ENGINE_URLS.get(engine)
    if not url:
        raise RuntimeError(f"unknown TTS engine '{engine}'; known: {ENGINES}")
    resp = httpx.post(
        url, json={"input": text, "voice": voice or "default", "model": engine}, timeout=600
    )
    resp.raise_for_status()
    Path(output_path).write_bytes(resp.content)
