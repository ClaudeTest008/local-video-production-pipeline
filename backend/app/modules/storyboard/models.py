from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Scene(Base, TimestampMixin):
    __tablename__ = "storyboard_scenes"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    order_index: Mapped[int] = mapped_column(default=0)
    title: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    prompt: Mapped[str] = mapped_column(Text, default="")
    duration_s: Mapped[float] = mapped_column(default=5.0)
    image_asset_id: Mapped[int | None] = mapped_column(nullable=True)
    meta: Mapped[dict] = mapped_column(default=dict)
