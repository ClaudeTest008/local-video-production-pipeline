from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.repository import Repository
from app.modules.knowledge import service
from app.modules.knowledge.models import Learning

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

DB = Annotated[Session, Depends(get_db)]


class LearningCreate(BaseModel):
    kind: str = "manual"
    key: str = ""
    insight: str
    data: dict = {}
    score: float = 0.0
    brand_id: int | None = None
    project_id: int | None = None


@router.get("")
def list_learnings(db: DB, kind: str | None = None, brand_id: int | None = None, limit: int = 100):
    return Repository(Learning, db).list(limit=limit, kind=kind, brand_id=brand_id)


@router.post("", status_code=201)
def create_learning(payload: LearningCreate, db: DB):
    return service.record(db, **payload.model_dump())


@router.get("/digest")
def get_digest(db: DB, brand_id: int | None = None) -> dict:
    return {"digest": service.digest(db, brand_id=brand_id)}


@router.delete("/{learning_id}", status_code=204)
def delete_learning(learning_id: int, db: DB):
    if not Repository(Learning, db).delete(learning_id):
        raise HTTPException(404, f"learning {learning_id} not found")
