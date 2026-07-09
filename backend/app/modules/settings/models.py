from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Setting(Base, TimestampMixin):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    value: Mapped[dict] = mapped_column(default=dict)  # {"v": <anything json>}
