from sqlalchemy import Boolean, String
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
    # v1.2 workflow management: users toggle flags, never edit nodes
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual|imported|uploaded
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    wf_type: Mapped[str] = mapped_column(
        String(30), default="other"
    )  # video_lipsync|avatar|video|image|audio|other
    models: Mapped[list] = mapped_column(default=list)  # model files the graph references
    vram_estimate_mb: Mapped[int | None] = mapped_column(nullable=True)
    content_types: Mapped[list] = mapped_column(default=list)  # preferred-for tags
    meta: Mapped[dict] = mapped_column(default=dict)  # incl. conversion issues/status
