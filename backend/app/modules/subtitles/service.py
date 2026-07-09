"""Subtitle format serializers (SRT / VTT)."""


def _ts(seconds: float, sep: str) -> str:
    ms = round(seconds * 1000)
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def to_srt(segments: list[dict]) -> str:
    blocks = [
        f"{i}\n{_ts(seg['start'], ',')} --> {_ts(seg['end'], ',')}\n{seg['text']}"
        for i, seg in enumerate(segments, 1)
    ]
    return "\n\n".join(blocks) + "\n"


def to_vtt(segments: list[dict]) -> str:
    blocks = [
        f"{_ts(seg['start'], '.')} --> {_ts(seg['end'], '.')}\n{seg['text']}" for seg in segments
    ]
    return "WEBVTT\n\n" + "\n\n".join(blocks) + "\n"
