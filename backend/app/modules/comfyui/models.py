from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class ComfyJob(Base, TimestampMixin):
    __tablename__ = "comfy_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    prompt_id: Mapped[str] = mapped_column(String(64), index=True)
    workflow: Mapped[dict] = mapped_column(default=dict)
    status: Mapped[str] = mapped_column(String(30), default="queued")  # queued|done|error
    outputs: Mapped[list] = mapped_column(default=list)
    meta: Mapped[dict] = mapped_column(default=dict)
