from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Learning(Base, TimestampMixin):
    """One accumulated fact the studio learned from its own work."""

    __tablename__ = "learnings"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    project_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(50), index=True)  # render|prompt|analytics|manual|...
    key: Mapped[str] = mapped_column(String(200), default="")
    insight: Mapped[str] = mapped_column(Text, default="")
    data: Mapped[dict] = mapped_column(default=dict)
    score: Mapped[float] = mapped_column(Float, default=0.0)  # signed signal strength
