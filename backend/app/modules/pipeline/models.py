from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class PipelineRun(Base, TimestampMixin):
    """One autonomous production run over a project.

    Modes (advisory — the user is the Creative Director):
      manual   — user drives every module by hand, run just tracks state
      assisted — user triggers one stage at a time (/step), reviews between stages
      producer — AI runs all runnable stages back-to-back (/run-all)
    """

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    mode: Mapped[str] = mapped_column(String(20), default="assisted")
    status: Mapped[str] = mapped_column(String(20), default="idle")  # idle|running|done|error
    current_stage: Mapped[str] = mapped_column(String(30), default="")
    log: Mapped[list] = mapped_column(default=list)  # [{stage, status, detail}]
    meta: Mapped[dict] = mapped_column(default=dict)
