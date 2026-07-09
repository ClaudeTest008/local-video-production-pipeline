from typing import Literal

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.crud_router import crud_router
from app.modules.research.models import ResearchNote
from app.modules.research.schemas import ResearchNoteCreate, ResearchNoteRead, ResearchNoteUpdate

router = crud_router(
    model=ResearchNote,
    create_schema=ResearchNoteCreate,
    read_schema=ResearchNoteRead,
    update_schema=ResearchNoteUpdate,
    prefix="/research",
    tag="research",
    entity="research_note",
)


class SearchRequest(BaseModel):
    query: str
    provider: Literal["brave", "tavily"] = "brave"
    count: int = 10


@router.post("/search")
def web_search(payload: SearchRequest) -> list[dict]:
    """Web search via Brave or Tavily. Results are [{title, url, snippet}]."""
    if payload.provider == "brave":
        if not settings.brave_api_key:
            raise HTTPException(501, "LVPP_BRAVE_API_KEY not configured")
        resp = httpx.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": payload.query, "count": payload.count},
            headers={"X-Subscription-Token": settings.brave_api_key},
            timeout=30,
        )
        resp.raise_for_status()
        return [
            {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("description")}
            for r in resp.json().get("web", {}).get("results", [])
        ]
    if not settings.tavily_api_key:
        raise HTTPException(501, "LVPP_TAVILY_API_KEY not configured")
    resp = httpx.post(
        "https://api.tavily.com/search",
        json={
            "api_key": settings.tavily_api_key,
            "query": payload.query,
            "max_results": payload.count,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return [
        {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content")}
        for r in resp.json().get("results", [])
    ]
