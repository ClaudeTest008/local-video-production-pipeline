from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="idea")  # pipeline stage
    idea: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(default=list)
    meta: Mapped[dict] = mapped_column(default=dict)


class ProjectSnapshot(Base, TimestampMixin):
    __tablename__ = "project_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(200), default="")
    data: Mapped[dict] = mapped_column(default=dict)  # full project state dump
