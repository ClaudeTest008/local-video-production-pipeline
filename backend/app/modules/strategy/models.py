from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Opportunity(Base, TimestampMixin):
    """A scored content opportunity — answers "what should I create next?"."""

    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    topic: Mapped[str] = mapped_column(String(500))
    angle: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    # growth, competition, virality, evergreen, shortform, longform, audience_fit, urgency (0-10)
    scores: Mapped[dict] = mapped_column(default=dict)
    status: Mapped[str] = mapped_column(
        String(20), default="suggested"
    )  # suggested|approved|rejected|produced
    sources: Mapped[list] = mapped_column(default=list)
    meta: Mapped[dict] = mapped_column(default=dict)
