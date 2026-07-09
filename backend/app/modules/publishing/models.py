from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class PublishJob(Base, TimestampMixin):
    __tablename__ = "publish_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    platform: Mapped[str] = mapped_column(String(50), default="youtube")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    scheduled_at: Mapped[str] = mapped_column(String(50), default="")
    video_asset_id: Mapped[int | None] = mapped_column(nullable=True)
    meta: Mapped[dict] = mapped_column(default=dict)
