"""Generic repository — one CRUD implementation shared by every module."""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import Base

M = TypeVar("M", bound=Base)


class Repository(Generic[M]):
    def __init__(self, model: type[M], db: Session) -> None:
        self.model = model
        self.db = db

    def get(self, id_: int) -> M | None:
        return self.db.get(self.model, id_)

    def list(self, offset: int = 0, limit: int = 100, **filters: Any) -> list[M]:
        stmt = select(self.model).offset(offset).limit(limit)
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        return list(self.db.scalars(stmt))

    def create(self, **data: Any) -> M:
        obj = self.model(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, id_: int, **data: Any) -> M | None:
        obj = self.get(id_)
        if obj is None:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id_: int) -> bool:
        obj = self.get(id_)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
