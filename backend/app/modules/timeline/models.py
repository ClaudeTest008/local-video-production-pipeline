from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Timeline(Base, TimestampMixin):
    __tablename__ = "timelines"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), default="Main")
    # tracks: [{kind: "video"|"audio"|"caption", clips: [{path, start, duration, ...}]}]
    tracks: Mapped[list] = mapped_column(default=list)
    fps: Mapped[float] = mapped_column(Float, default=30.0)
    resolution: Mapped[str] = mapped_column(String(20), default="1920x1080")
    meta: Mapped[dict] = mapped_column(default=dict)
