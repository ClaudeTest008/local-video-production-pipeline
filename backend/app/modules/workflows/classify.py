"""Workflow classification + capability metadata, from graph node classes and
the workflow's name. Drives automatic selection: video-with-voice first."""

MODEL_EXTS = (".safetensors", ".gguf", ".ckpt", ".pt", ".sft")

AUDIO_HINTS = ("audio", "lipsync", "lip_sync", "tts", "speech", "voice", "sonic", "wav")
VIDEO_HINTS = ("video", "ltxv", "ltx", "wan", "svd", "animatediff", "cogvideo", "vhs_", "hunyuan")
NAME_LIPSYNC = ("lip sync", "lipsync", "lip-sync", "talking", "avatar", "character voice")
NAME_VIDEO = ("video", "director", "cinematic", "i2v", "img2vid", "animation", "movie", "scene")


def classify(name: str, graph: dict) -> dict:
    """Returns {wf_type, models, vram_estimate_mb}."""
    lname = name.lower()
    classes = " ".join(n.get("class_type", "").lower() for n in graph.values())

    has_audio = any(h in classes for h in AUDIO_HINTS) or any(h in lname for h in NAME_LIPSYNC)
    has_video = any(h in classes for h in VIDEO_HINTS) or any(h in lname for h in NAME_VIDEO)
    has_image_out = "saveimage" in classes

    if has_video and (has_audio or any(h in lname for h in NAME_LIPSYNC)):
        wf_type = "avatar" if ("avatar" in lname or "talking" in lname) else "video_lipsync"
    elif has_video:
        wf_type = "video"
    elif "saveaudio" in classes or "audio" in classes:
        wf_type = "audio"
    elif has_image_out:
        wf_type = "image"
    else:
        wf_type = "other"

    models = sorted(
        {
            value
            for node in graph.values()
            for value in (node.get("inputs") or {}).values()
            if isinstance(value, str) and value.lower().endswith(MODEL_EXTS)
        }
    )

    vram = None
    joined = " ".join(models).lower()
    for marker, mb in (
        ("22b", 24_000),
        ("13b", 20_000),
        ("9b", 16_000),
        ("7b", 12_000),
        ("xl", 10_000),
        ("turbo", 8_000),
    ):
        if marker in joined:
            vram = mb
            break

    return {"wf_type": wf_type, "models": models, "vram_estimate_mb": vram}


# selection preference: integrated voice first, then plain video, then image
TYPE_PRIORITY = {"video_lipsync": 0, "avatar": 1, "video": 2, "image": 3, "other": 4, "audio": 5}
