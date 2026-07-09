from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class McpServer(Base, TimestampMixin):
    __tablename__ = "mcp_servers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    command: Mapped[str] = mapped_column(String(200))
    args: Mapped[list] = mapped_column(default=list)
    env: Mapped[dict] = mapped_column(default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(30), default="catalog")  # catalog|custom|imported
    meta: Mapped[dict] = mapped_column(default=dict)
