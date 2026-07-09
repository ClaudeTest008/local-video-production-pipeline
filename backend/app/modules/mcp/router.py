from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.events import bus
from app.core.repository import Repository
from app.modules.mcp.catalog import CATALOG
from app.modules.mcp.models import McpServer

router = APIRouter(prefix="/mcp", tags=["mcp"])

DB = Annotated[Session, Depends(get_db)]


def _repo(db: DB) -> Repository[McpServer]:
    return Repository(McpServer, db)


Servers = Annotated[Repository, Depends(_repo)]


class ServerCreate(BaseModel):
    name: str
    description: str = ""
    command: str
    args: list[str] = []
    env: dict[str, str] = {}
    enabled: bool = False


class ServerUpdate(BaseModel):
    description: str | None = None
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    enabled: bool | None = None


@router.get("/catalog")
def catalog() -> list[dict]:
    return CATALOG


@router.post("/discover")
def discover(db: DB, servers: Servers) -> dict:
    """Import every catalog server not yet registered (disabled by default)."""
    existing = {s.name for s in db.scalars(select(McpServer))}
    added = [
        servers.create(source="catalog", **entry).name
        for entry in CATALOG
        if entry["name"] not in existing
    ]
    if added:
        bus.emit("mcp.discovered", {"added": added})
    return {"added": added, "total": len(existing) + len(added)}


@router.get("/servers")
def list_servers(servers: Servers):
    return servers.list(limit=500)


@router.post("/servers", status_code=201)
def create_server(payload: ServerCreate, db: DB, servers: Servers):
    if db.scalar(select(McpServer).where(McpServer.name == payload.name)):
        raise HTTPException(409, f"server '{payload.name}' already exists")
    return servers.create(source="custom", **payload.model_dump())


@router.patch("/servers/{server_id}")
def update_server(server_id: int, payload: ServerUpdate, servers: Servers):
    server = servers.update(server_id, **payload.model_dump(exclude_unset=True))
    if server is None:
        raise HTTPException(404, f"server {server_id} not found")
    return server


@router.delete("/servers/{server_id}", status_code=204)
def delete_server(server_id: int, servers: Servers):
    if not servers.delete(server_id):
        raise HTTPException(404, f"server {server_id} not found")


@router.post("/servers/{server_id}/toggle")
def toggle(server_id: int, servers: Servers):
    server = servers.get(server_id)
    if server is None:
        raise HTTPException(404, f"server {server_id} not found")
    server = servers.update(server_id, enabled=not server.enabled)
    bus.emit("mcp.toggled", {"id": server_id, "enabled": server.enabled})
    return server


@router.get("/export")
def export_config(db: DB) -> dict:
    """mcpServers JSON consumable by Claude Desktop / Cursor / the desktop app."""
    enabled = db.scalars(select(McpServer).where(McpServer.enabled)).all()
    return {
        "mcpServers": {
            s.name: {"command": s.command, "args": s.args, "env": s.env} for s in enabled
        }
    }
