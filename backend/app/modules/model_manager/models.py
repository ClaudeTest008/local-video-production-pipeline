from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class ManagedModel(Base, TimestampMixin):
    __tablename__ = "managed_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(50), default="ollama")
    kind: Mapped[str] = mapped_column(String(30), default="llm")
    location: Mapped[str] = mapped_column(String(500), default="")
    enabled: Mapped[bool] = mapped_column(default=True)
    meta: Mapped[dict] = mapped_column(default=dict)
