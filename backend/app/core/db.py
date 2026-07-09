"""Database session management. SQLite by default, PostgreSQL via LVPP_DATABASE_URL."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import JSON, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    type_annotation_map = {dict: JSON, list: JSON}


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


def _make_engine(url: str):
    kwargs = {}
    if url.startswith("sqlite"):
        db_path = url.removeprefix("sqlite:///")
        if db_path and not db_path.startswith(":memory:"):
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables for dev/test. Production migrations go through Alembic."""
    import app.core.registry as registry

    registry.import_all_models()
    Base.metadata.create_all(bind=engine)
