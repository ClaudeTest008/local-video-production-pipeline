"""FFmpeg helpers. Commands are built pure (testable) and executed only if ffmpeg exists."""

import shutil
import subprocess
from pathlib import Path


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _subtitles_filter_path(path: str) -> str:
    """Escape a path for ffmpeg's subtitles filter (Windows drive colon)."""
    return path.replace("\\", "/").replace(":", r"\:")


def build_concat_command(
    clips: list[str],
    output: str,
    fps: float = 30,
    resolution: str = "1920x1080",
    subtitles_path: str | None = None,
) -> list[str]:
    """Concat clips re-encoded to a uniform format. Supports .mp4/.mov output.

    Clips are paths (str) or {"path", "duration"} dicts. Still images (png/jpg/
    webp) are looped for their duration (default 5s) — a storyboard of rendered
    frames becomes a real video, not a 3-frame flicker.
    """
    if not clips:
        raise ValueError("no clips to export")
    IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    width, height = resolution.split("x")
    cmd: list[str] = ["ffmpeg", "-y"]
    for clip in clips:
        path = clip["path"] if isinstance(clip, dict) else clip
        duration = (clip.get("duration") if isinstance(clip, dict) else None) or 5.0
        if path.lower().endswith(IMAGE_EXTS):
            cmd += ["-loop", "1", "-t", str(duration), "-i", path]
        else:
            cmd += ["-i", path]
    n = len(clips)
    scale = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}"
    )
    filters = "".join(f"[{i}:v]{scale}[v{i}];" for i in range(n))
    # Carry audio through when every clip is a video (AV workflows put the
    # voice/lip-sync track inside each rendered clip — dropping it silenced the
    # final export). ponytail: a mix of stills and videos still exports silent;
    # per-lane synthesized silence if that combination ever matters.
    paths = [c["path"] if isinstance(c, dict) else c for c in clips]
    with_audio = not any(p.lower().endswith(IMAGE_EXTS) for p in paths)
    if with_audio:
        filters += "".join(
            f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}];" for i in range(n)
        )
        concat_in = "".join(f"[v{i}][a{i}]" for i in range(n))
        chain = f"{filters}{concat_in}concat=n={n}:v=1:a=1[cat][acat]"
    else:
        concat_in = "".join(f"[v{i}]" for i in range(n))
        chain = f"{filters}{concat_in}concat=n={n}:v=1:a=0[cat]"
    if subtitles_path:
        chain += f";[cat]subtitles='{_subtitles_filter_path(subtitles_path)}'[out]"
    else:
        chain = chain.replace("[cat]", "[out]")
    cmd += ["-filter_complex", chain, "-map", "[out]"]
    if with_audio:
        cmd += ["-map", "[acat]", "-c:a", "aac"]
    cmd += [output]
    return cmd


def build_audio_mix_command(video: str, audio_tracks: list[str], output: str) -> list[str]:
    cmd = ["ffmpeg", "-y", "-i", video]
    for track in audio_tracks:
        cmd += ["-i", track]
    if audio_tracks:
        inputs = "".join(f"[{i + 1}:a]" for i in range(len(audio_tracks)))
        cmd += [
            "-filter_complex",
            f"{inputs}amix=inputs={len(audio_tracks)}[a]",
            "-map",
            "0:v",
            "-map",
            "[a]",
        ]
    cmd += ["-c:v", "copy", output]
    return cmd


def run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
