from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Brand(Base, TimestampMixin):
    """A brand/channel identity. Every agent call runs inside a brand context."""

    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    voice: Mapped[str] = mapped_column(Text, default="")  # tone of voice guidelines
    style: Mapped[str] = mapped_column(Text, default="")  # visual style guidelines
    audience: Mapped[str] = mapped_column(Text, default="")  # target audience
    guidelines: Mapped[str] = mapped_column(Text, default="")  # anything else (dos/don'ts)
    platforms: Mapped[list] = mapped_column(default=list)  # ["youtube", "tiktok", ...]
    schedule: Mapped[dict] = mapped_column(default=dict)  # publishing cadence
    goals: Mapped[str] = mapped_column(Text, default="")  # business goals ("100k subs")
    # Preferred engines — used when an agent profile doesn't pin its own
    preferred_provider: Mapped[str] = mapped_column(String(50), default="")
    preferred_model: Mapped[str] = mapped_column(String(100), default="")
    preferred_workflow_id: Mapped[int | None] = mapped_column(nullable=True)  # ComfyUI graph
    memory: Mapped[dict] = mapped_column(default=dict)  # accumulated brand memory
    meta: Mapped[dict] = mapped_column(default=dict)


def brand_context(brand: Brand | None) -> str:
    """Compact text block injected into agent system prompts."""
    if brand is None:
        return ""
    parts = [f"Brand: {brand.name}"]
    for label, value in (
        ("Voice", brand.voice),
        ("Visual style", brand.style),
        ("Audience", brand.audience),
        ("Guidelines", brand.guidelines),
        ("Goals", brand.goals),
    ):
        if value:
            parts.append(f"{label}: {value}")
    if brand.platforms:
        parts.append(f"Platforms: {', '.join(brand.platforms)}")
    if brand.memory:
        parts.append(f"Brand memory: {brand.memory}")
    return "\n".join(parts)
