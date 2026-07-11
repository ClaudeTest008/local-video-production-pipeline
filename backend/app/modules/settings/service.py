"""Runtime settings: DB-stored values override env defaults (the setup wizard
writes here so users never edit .env)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.settings.models import Setting


def get_value(db: Session, key: str, default=None):
    setting = db.scalar(select(Setting).where(Setting.key == key))
    return setting.value.get("v") if setting is not None else default


def set_value(db: Session, key: str, value) -> None:
    setting = db.scalar(select(Setting).where(Setting.key == key))
    if setting is None:
        db.add(Setting(key=key, value={"v": value}))
    else:
        setting.value = {"v": value}
    db.commit()
