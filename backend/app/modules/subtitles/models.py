from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class SubtitleTrack(Base, TimestampMixin):
    __tablename__ = "subtitle_tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    language: Mapped[str] = mapped_column(String(10), default="en")
    segments: Mapped[list] = mapped_column(default=list)  # [{start, end, text}]
    meta: Mapped[dict] = mapped_column(default=dict)
