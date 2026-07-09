"""CRUD router factory. Thin modules are: models.py + schemas.py + 5-line router.py.

Every generated router emits `<entity>.created|updated|deleted` events on the bus,
so cross-module reactions (auto-import, indexing, ...) hook in without coupling.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import Base, get_db
from app.core.events import bus
from app.core.repository import Repository


def crud_router(
    *,
    model: type[Base],
    create_schema: type[BaseModel],
    read_schema: type[BaseModel],
    update_schema: type[BaseModel],
    prefix: str,
    tag: str,
    entity: str,
    filter_fields: tuple[str, ...] = ("project_id",),
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    def repo(db: Annotated[Session, Depends(get_db)]) -> Repository:
        return Repository(model, db)

    @router.get("", response_model=list[read_schema])
    def list_items(
        r: Annotated[Repository, Depends(repo)],
        offset: int = 0,
        limit: Annotated[int, Query(le=500)] = 100,
        project_id: int | None = None,
    ):
        filters = {"project_id": project_id} if "project_id" in filter_fields else {}
        return r.list(offset=offset, limit=limit, **filters)

    @router.post("", response_model=read_schema, status_code=201)
    def create_item(payload: create_schema, r: Annotated[Repository, Depends(repo)]):  # type: ignore[valid-type]
        obj = r.create(**payload.model_dump())
        bus.emit(f"{entity}.created", {"id": obj.id})
        return obj

    @router.get("/{item_id}", response_model=read_schema)
    def get_item(item_id: int, r: Annotated[Repository, Depends(repo)]):
        obj = r.get(item_id)
        if obj is None:
            raise HTTPException(404, f"{entity} {item_id} not found")
        return obj

    @router.patch("/{item_id}", response_model=read_schema)
    def update_item(
        item_id: int, payload: update_schema, r: Annotated[Repository, Depends(repo)]  # type: ignore[valid-type]
    ):
        obj = r.update(item_id, **payload.model_dump(exclude_unset=True))
        if obj is None:
            raise HTTPException(404, f"{entity} {item_id} not found")
        bus.emit(f"{entity}.updated", {"id": obj.id})
        return obj

    @router.delete("/{item_id}", status_code=204)
    def delete_item(item_id: int, r: Annotated[Repository, Depends(repo)]):
        if not r.delete(item_id):
            raise HTTPException(404, f"{entity} {item_id} not found")
        bus.emit(f"{entity}.deleted", {"id": item_id})

    return router
