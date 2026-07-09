from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class WorkflowDef(Base, TimestampMixin):
    __tablename__ = "workflow_defs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(30), default="comfyui")  # comfyui|agent|pipeline
    graph: Mapped[dict] = mapped_column(default=dict)
    version: Mapped[int] = mapped_column(default=1)
    parent_id: Mapped[int | None] = mapped_column(nullable=True)  # previous version
    meta: Mapped[dict] = mapped_column(default=dict)
