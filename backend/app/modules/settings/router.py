from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ai.registry import get_provider, list_providers
from app.core.db import get_db
from app.modules.settings.models import Setting

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingIn(BaseModel):
    value: Any


@router.get("")
def all_settings(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    return {s.key: s.value.get("v") for s in db.scalars(select(Setting))}


@router.get("/providers")
def providers() -> list[dict]:
    result = []
    for name in list_providers():
        try:
            available = get_provider(name).is_available()
        except Exception:
            available = False
        result.append({"name": name, "available": available})
    return result


@router.get("/{key}")
def get_setting(key: str, db: Annotated[Session, Depends(get_db)]) -> Any:
    setting = db.scalar(select(Setting).where(Setting.key == key))
    if setting is None:
        raise HTTPException(404, f"setting '{key}' not found")
    return setting.value.get("v")


@router.put("/{key}")
def put_setting(key: str, payload: SettingIn, db: Annotated[Session, Depends(get_db)]) -> Any:
    setting = db.scalar(select(Setting).where(Setting.key == key))
    if setting is None:
        setting = Setting(key=key, value={"v": payload.value})
        db.add(setting)
    else:
        setting.value = {"v": payload.value}
    db.commit()
    return payload.value


@router.delete("/{key}", status_code=204)
def delete_setting(key: str, db: Annotated[Session, Depends(get_db)]) -> None:
    setting = db.scalar(select(Setting).where(Setting.key == key))
    if setting is None:
        raise HTTPException(404, f"setting '{key}' not found")
    db.delete(setting)
    db.commit()
