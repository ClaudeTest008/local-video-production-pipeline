"""Seed the database with a sample project, agents, MCP catalog, and templates.

Usage: python seed.py  (idempotent — safe to re-run)
"""

from sqlalchemy import select

from app.core.db import SessionLocal, init_db
from app.modules.agents.models import AgentProfile
from app.modules.agents.presets import PRESETS
from app.modules.brands.models import Brand
from app.modules.mcp.catalog import CATALOG
from app.modules.mcp.models import McpServer
from app.modules.projects.models import Project
from app.modules.prompts.models import Prompt
from app.modules.scripts.models import Script
from app.modules.seo.models import SeoPack
from app.modules.storyboard.models import Scene
from app.modules.templates.models import Template

SAMPLE_SCRIPT = """\
# Why Vertical Farms Are Failing

[HOOK — cold open]
Three billion dollars. That's how much investors poured into vertical farming —
and most of it is gone. [B-ROLL: abandoned warehouse farm]

## The promise
Stacked greens, no pesticides, 95% less water. [ON-SCREEN: water usage chart]

## The physics problem
The sun is free. LEDs are not. Every leaf of lettuce carries a electricity bill…

## What actually survives
Herbs, microgreens, pharma-grade crops — high price per gram beats the light bill.

[CTA] Subscribe for the economics nobody puts in the pitch deck.
"""

SCENES = [
    ("Abandoned warehouse farm", "Drone shot gliding through empty grow racks", 6.0),
    ("Water usage chart", "Animated bar chart, 95% reduction highlight", 8.0),
    ("LED close-up", "Macro of purple grow lights flickering off", 5.0),
    ("Microgreens harvest", "Hands cutting microgreens, shallow depth of field", 7.0),
]


def seed() -> None:
    init_db()
    with SessionLocal() as db:
        if db.scalar(select(Project).where(Project.name == "Vertical Farming Deep-Dive")):
            print("already seeded — nothing to do")
            return

        brand = Brand(
            name="Systems Explained",
            description="Sample brand seeded for exploration",
            voice="calm, evidence-first, lightly wry",
            style="cinematic documentary, desaturated palette, 35mm grain",
            audience="curious 25-45 viewers who like economics and engineering deep-dives",
            platforms=["youtube"],
            goals="Reach 100k subscribers with weekly long-form deep-dives",
        )
        db.add(brand)
        db.flush()

        project = Project(
            name="Vertical Farming Deep-Dive",
            brand_id=brand.id,
            idea="Why did vertical farming startups burn $3B? The physics of light.",
            description="Sample project seeded for exploration",
            status="storyboard",
            tags=["economics", "agriculture", "deep-dive"],
        )
        db.add(project)
        db.flush()

        db.add(
            Script(
                project_id=project.id,
                title="Main script v1",
                content=SAMPLE_SCRIPT,
            )
        )
        for i, (title, description, duration) in enumerate(SCENES):
            db.add(
                Scene(
                    project_id=project.id,
                    order_index=i,
                    title=title,
                    description=description,
                    duration_s=duration,
                    prompt=f"cinematic {description.lower()}, documentary style, 35mm",
                )
            )
        db.add(
            Prompt(
                project_id=project.id,
                name="hero-thumbnail",
                kind="image",
                text=(
                    "abandoned vertical farm warehouse, rows of empty purple LED grow racks, "
                    "volumetric haze, cinematic wide shot, high contrast — negative: people, text"
                ),
            )
        )
        db.add(
            SeoPack(
                project_id=project.id,
                title="Why Vertical Farms Are Failing (The $3B Mistake)",
                description="The physics and economics behind the vertical farming crash.",
                tags=["vertical farming", "agtech", "economics"],
                keywords=["vertical farming failure", "agtech crash"],
            )
        )

        existing_roles = {a.role for a in db.scalars(select(AgentProfile))}
        for preset in PRESETS:
            if preset["role"] not in existing_roles:
                db.add(AgentProfile(**preset))

        existing_servers = {s.name for s in db.scalars(select(McpServer))}
        for entry in CATALOG:
            if entry["name"] not in existing_servers:
                db.add(McpServer(source="catalog", **entry))

        db.add(
            Template(
                name="Listicle script skeleton",
                kind="script",
                content="# {title}\n\n[HOOK]\n\n## Item 1\n\n## Item 2\n\n[CTA]",
                tags=["starter"],
            )
        )
        db.commit()
        print(f"seeded project #{project.id}, {len(PRESETS)} agents, {len(CATALOG)} MCP servers")


if __name__ == "__main__":
    seed()
