from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class VoiceJob(Base, TimestampMixin):
    __tablename__ = "voice_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    engine: Mapped[str] = mapped_column(String(30), default="piper")
    text: Mapped[str] = mapped_column(Text)
    voice: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|done|error
    output_path: Mapped[str] = mapped_column(String(500), default="")
    meta: Mapped[dict] = mapped_column(default=dict)
