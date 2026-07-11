from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.events import bus
from app.core.repository import Repository
from app.modules.agents import service as agent_service
from app.modules.brands.models import Brand, brand_context
from app.modules.pipeline.parsers import parse_opportunities
from app.modules.pipeline.service import get_agent
from app.modules.projects.models import Project
from app.modules.strategy.models import Opportunity

router = APIRouter(prefix="/strategy", tags=["strategy"])

DB = Annotated[Session, Depends(get_db)]


def _repo(db: DB) -> Repository[Opportunity]:
    return Repository(Opportunity, db)


Opportunities = Annotated[Repository, Depends(_repo)]


class GenerateRequest(BaseModel):
    brand_id: int | None = None
    seed_topic: str = ""  # optional focus area
    count: int = 5


def _research_snippets(seed_topic: str) -> list[dict]:
    """Optional web evidence via Brave (key required); empty without it —
    the strategist then works from model knowledge and says so."""
    if not (settings.brave_api_key and seed_topic):
        return []
    import httpx

    try:
        resp = httpx.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": f"{seed_topic} trends {2026}", "count": 8},
            headers={"X-Subscription-Token": settings.brave_api_key},
            timeout=20,
        )
        resp.raise_for_status()
        return [
            {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("description")}
            for r in resp.json().get("web", {}).get("results", [])
        ]
    except httpx.HTTPError:
        return []


@router.get("/opportunities")
def list_opportunities(
    opportunities: Opportunities, brand_id: int | None = None, status: str | None = None
):
    return opportunities.list(limit=200, brand_id=brand_id, status=status)


@router.post("/generate", status_code=201)
def generate(payload: GenerateRequest, db: DB, opportunities: Opportunities):
    """Ask the Strategy Director for scored opportunities. Uses live web
    research when a Brave key is configured; degrades to model knowledge offline."""
    brand = db.get(Brand, payload.brand_id) if payload.brand_id else None
    snippets = _research_snippets(payload.seed_topic)
    evidence = (
        "\n".join(f"- {s['title']}: {s['snippet']} ({s['url']})" for s in snippets)
        or "(no live research available — reason from general knowledge and say so in WHY)"
    )
    agent = get_agent(db, "strategy_director")
    _, content, _, _ = agent_service.run_agent(
        db,
        agent,
        f"Propose {payload.count} content opportunities"
        + (f" around '{payload.seed_topic}'" if payload.seed_topic else "")
        + f".\nResearch evidence:\n{evidence}",
        context=brand_context(brand),
    )
    parsed = parse_opportunities(content)
    if not parsed:
        raise HTTPException(
            502, "strategy agent returned no parseable opportunities; check the provider/model"
        )
    created = [
        opportunities.create(
            brand_id=payload.brand_id,
            sources=[s["url"] for s in snippets],
            meta={"raw": content},
            **item,
        )
        for item in parsed
    ]
    bus.emit("strategy.generated", {"count": len(created), "brand_id": payload.brand_id})
    return created


@router.post("/opportunities/{opportunity_id}/approve")
def approve(opportunity_id: int, db: DB, opportunities: Opportunities) -> dict:
    """Approve → a project is born and enters the pipeline."""
    opportunity = opportunities.get(opportunity_id)
    if opportunity is None:
        raise HTTPException(404, f"opportunity {opportunity_id} not found")
    from app.core import files

    project = Repository(Project, db).create(
        name=opportunity.topic[:200],
        brand_id=opportunity.brand_id,
        idea=f"{opportunity.topic}. Angle: {opportunity.angle}",
        meta={"opportunity_id": opportunity.id, "scores": opportunity.scores},
    )
    files.create_project_tree(project.id)
    opportunities.update(
        opportunity_id, status="approved", meta={**opportunity.meta, "project_id": project.id}
    )
    bus.emit("strategy.approved", {"opportunity_id": opportunity_id, "project_id": project.id})
    return {"project_id": project.id, "opportunity_id": opportunity_id}


@router.post("/opportunities/{opportunity_id}/reject")
def reject(opportunity_id: int, opportunities: Opportunities):
    opportunity = opportunities.update(opportunity_id, status="rejected")
    if opportunity is None:
        raise HTTPException(404, f"opportunity {opportunity_id} not found")
    return opportunity


@router.delete("/opportunities/{opportunity_id}", status_code=204)
def delete_opportunity(opportunity_id: int, opportunities: Opportunities):
    if not opportunities.delete(opportunity_id):
        raise HTTPException(404, f"opportunity {opportunity_id} not found")
