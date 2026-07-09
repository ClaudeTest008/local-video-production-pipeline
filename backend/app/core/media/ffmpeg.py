"""FFmpeg helpers. Commands are built pure (testable) and executed only if ffmpeg exists."""

import shutil
import subprocess
from pathlib import Path


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def build_concat_command(
    clips: list[str], output: str, fps: float = 30, resolution: str = "1920x1080"
) -> list[str]:
    """Concat clips re-encoded to a uniform format. Supports .mp4/.mov output."""
    if not clips:
        raise ValueError("no clips to export")
    width, height = resolution.split("x")
    cmd: list[str] = ["ffmpeg", "-y"]
    for clip in clips:
        cmd += ["-i", clip]
    n = len(clips)
    scale = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}"
    )
    filters = "".join(f"[{i}:v]{scale}[v{i}];" for i in range(n))
    concat_in = "".join(f"[v{i}]" for i in range(n))
    cmd += [
        "-filter_complex",
        f"{filters}{concat_in}concat=n={n}:v=1:a=0[out]",
        "-map",
        "[out]",
        output,
    ]
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
