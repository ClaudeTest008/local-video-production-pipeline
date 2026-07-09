"""Speech-to-text via faster-whisper (optional extra: pip install -e ".[transcribe]")."""


def whisper_available() -> bool:
    try:
        import faster_whisper  # noqa: F401

        return True
    except ImportError:
        return False


def transcribe(
    audio_path: str, model_size: str = "base", language: str | None = None
) -> list[dict]:
    """Return subtitle segments [{start, end, text}]. Raises ImportError if extra missing."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="auto", compute_type="auto")
    segments, _info = model.transcribe(audio_path, language=language)
    return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
