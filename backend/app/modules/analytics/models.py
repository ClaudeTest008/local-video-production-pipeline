from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class MetricSnapshot(Base, TimestampMixin):
    __tablename__ = "metric_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    platform: Mapped[str] = mapped_column(String(50), default="youtube")
    views: Mapped[int] = mapped_column(default=0)
    likes: Mapped[int] = mapped_column(default=0)
    comments: Mapped[int] = mapped_column(default=0)
    watch_time_h: Mapped[float] = mapped_column(default=0.0)
    captured_at: Mapped[str] = mapped_column(String(50), default="")
    meta: Mapped[dict] = mapped_column(default=dict)
