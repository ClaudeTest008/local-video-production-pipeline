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
    """Bring the schema to head via Alembic on every startup.

    Alembic owns the schema (verified: `upgrade head` on a fresh DB yields the
    same tables/columns as ``create_all``). Running it at boot means existing
    installs self-heal when a migration is added — users never run alembic by
    hand. No-op when the DB is already at head.
    """
    from alembic import command
    from alembic.config import Config

    # backend root holds alembic.ini and the alembic/ script dir; resolve
    # absolutely so this works regardless of the process cwd (e.g. Tauri bundle).
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    command.upgrade(cfg, "head")
