"""The autonomous production orchestrator.

Each stage handler: gather context (brand + prior artifacts) → run the right
agent role → persist artifacts into the owning feature module → advance the
project's pipeline status. Handlers are ordered; a run steps through them.

Media stages (images, voice) are best-effort: they run when the local engine
(ComfyUI / TTS) is available and are logged as skipped otherwise — a run never
fails because optional local tooling is absent.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.events import bus
from app.core.repository import Repository
from app.modules.agents import service as agent_service
from app.modules.agents.models import AgentProfile
from app.modules.agents.presets import PRESETS
from app.modules.brands.models import Brand, brand_context
from app.modules.pipeline import parsers
from app.modules.pipeline.models import PipelineRun
from app.modules.projects.models import Project
from app.modules.prompts.models import Prompt
from app.modules.research.models import ResearchNote
from app.modules.scripts.models import Script
from app.modules.seo.models import SeoPack
from app.modules.storyboard.models import Scene
from app.modules.thumbnail.models import Thumbnail

logger = logging.getLogger(__name__)

# stage name -> project.status it advances to
STAGES: list[tuple[str, str]] = [
    ("research", "research"),
    ("script", "script"),
    ("storyboard", "storyboard"),
    ("prompts", "prompts"),
    ("images", "images"),
    ("voice", "voice"),
    ("seo", "seo"),
    ("thumbnail", "thumbnail"),
]
STAGE_NAMES = [name for name, _ in STAGES]


def get_agent(db: Session, role: str) -> AgentProfile:
    """Profile by role, auto-created from its preset on first use."""
    agent = db.scalar(select(AgentProfile).where(AgentProfile.role == role))
    if agent is None:
        preset = next(p for p in PRESETS if p["role"] == role)
        agent = Repository(AgentProfile, db).create(**preset)
    return agent


def _run_role(db: Session, role: str, user_input: str, project: Project, context: str) -> str:
    agent = get_agent(db, role)
    _, content, _, _ = agent_service.run_agent(
        db, agent, user_input, project_id=project.id, context=context
    )
    return content


def _base_context(db: Session, project: Project) -> str:
    brand = db.get(Brand, project.brand_id) if project.brand_id else None
    parts = [brand_context(brand), f"Project: {project.name}", f"Idea: {project.idea}"]
    try:  # knowledge digest is optional context, never a dependency
        from app.modules.knowledge import service as knowledge_service

        digest = knowledge_service.digest(db, brand_id=project.brand_id)
        if digest:
            parts.append(f"Learnings from past work:\n{digest}")
    except ImportError:
        pass
    return "\n\n".join(p for p in parts if p)


def _latest_script(db: Session, project_id: int) -> Script | None:
    return db.scalars(
        select(Script).where(Script.project_id == project_id).order_by(Script.id.desc())
    ).first()


def _scenes(db: Session, project_id: int) -> list[Scene]:
    return list(
        db.scalars(select(Scene).where(Scene.project_id == project_id).order_by(Scene.order_index))
    )


# ── stage handlers ──────────────────────────────────────────────────────────


def _stage_research(db: Session, project: Project, context: str) -> str:
    content = _run_role(
        db,
        "researcher",
        f"Research this video idea. Facts, statistics, named sources, angles:\n{project.idea}",
        project,
        context,
    )
    Repository(ResearchNote, db).create(
        project_id=project.id, query=project.idea[:500], content=content
    )
    return f"research note saved ({len(content)} chars)"


def _stage_script(db: Session, project: Project, context: str) -> str:
    note = db.scalars(
        select(ResearchNote)
        .where(ResearchNote.project_id == project.id)
        .order_by(ResearchNote.id.desc())
    ).first()
    research = note.content if note else "(no research available)"
    content = _run_role(
        db,
        "script_writer",
        f"Write the full script for '{project.name}'.\nResearch notes:\n{research}",
        project,
        context,
    )
    Repository(Script, db).create(
        project_id=project.id, title=f"{project.name} v1", content=content
    )
    return f"script saved ({len(content.split())} words)"


def _stage_storyboard(db: Session, project: Project, context: str) -> str:
    script = _latest_script(db, project.id)
    content = _run_role(
        db,
        "storyboard_artist",
        "Break this script into visual scenes. Output ONLY lines in the exact format\n"
        "SCENE: <title> | <duration seconds> | <shot description>\n\n"
        f"Script:\n{script.content if script else project.idea}",
        project,
        context,
    )
    scenes = parsers.parse_scenes(content)
    repo = Repository(Scene, db)
    for i, scene in enumerate(scenes):
        repo.create(project_id=project.id, order_index=i, **scene)
    return f"{len(scenes)} scenes created"


def _stage_prompts(db: Session, project: Project, context: str) -> str:
    scenes = _scenes(db, project.id)
    if not scenes:
        return "skipped: no scenes"
    prompt_repo = Repository(Prompt, db)
    scene_repo = Repository(Scene, db)
    for scene in scenes:
        content = _run_role(
            db,
            "prompt_engineer",
            "One image-generation prompt (single paragraph, no preamble) for this scene:\n"
            f"{scene.title}: {scene.description}",
            project,
            context,
        ).strip()
        scene_repo.update(scene.id, prompt=content)
        prompt_repo.create(
            project_id=project.id, name=f"scene-{scene.order_index}", kind="image", text=content
        )
    return f"{len(scenes)} scene prompts generated"


def _stage_images(db: Session, project: Project, context: str) -> str:
    """Queue one ComfyUI job per scene using the recommended workflow, if possible."""
    from app.modules.comfyui.client import ComfyUIClient
    from app.modules.workflows.models import WorkflowDef

    client = ComfyUIClient()
    if not client.is_available():
        return "skipped: ComfyUI not running"
    workflow = db.scalars(
        select(WorkflowDef).where(WorkflowDef.kind == "comfyui").order_by(WorkflowDef.id.desc())
    ).first()
    if workflow is None or not workflow.graph:
        return "skipped: no ComfyUI workflow saved in Workflow Manager"

    from app.modules.comfyui.models import ComfyJob
    from app.modules.comfyui.service import inject_prompt, record_queued

    queued = 0
    for scene in _scenes(db, project.id):
        if not scene.prompt:
            continue
        graph = inject_prompt(workflow.graph, scene.prompt)
        try:
            prompt_id = client.queue_prompt(graph)
        except Exception as e:  # comfy died mid-run — log, keep going
            logger.warning("queue failed for scene %s: %s", scene.id, e)
            continue
        job = Repository(ComfyJob, db).create(
            project_id=project.id,
            prompt_id=prompt_id,
            workflow=graph,
            workflow_def_id=workflow.id,
            meta={"scene_id": scene.id},
        )
        record_queued(job)
        queued += 1
    return f"{queued} render jobs queued (workflow '{workflow.name}' v{workflow.version})"


def _stage_voice(db: Session, project: Project, context: str) -> str:
    from app.core import files
    from app.core.media import tts
    from app.modules.voice.models import VoiceJob

    engine = next((e for e in tts.ENGINES if tts.engine_available(e)), None)
    if engine is None:
        return "skipped: no TTS engine available (piper/xtts/kokoro)"
    script = _latest_script(db, project.id)
    if script is None:
        return "skipped: no script"
    job = Repository(VoiceJob, db).create(project_id=project.id, engine=engine, text=script.content)
    output = files.project_dir(project.id) / "assets" / "audio" / f"voice-{job.id}.wav"
    try:
        tts.synthesize(engine, script.content, str(output))
    except Exception as e:
        Repository(VoiceJob, db).update(job.id, status="error", meta={"error": str(e)[:500]})
        return f"voice failed: {str(e)[:200]}"
    Repository(VoiceJob, db).update(job.id, status="done", output_path=str(output))
    return f"voice-over rendered with {engine}"


def _stage_seo(db: Session, project: Project, context: str) -> str:
    script = _latest_script(db, project.id)
    content = _run_role(
        db,
        "seo_specialist",
        "SEO pack for this video. Output with markers TITLE:, DESCRIPTION:, TAGS: "
        f"(comma-separated).\nScript:\n{(script.content if script else project.idea)[:6000]}",
        project,
        context,
    )
    parsed = parsers.parse_seo(content)
    Repository(SeoPack, db).create(project_id=project.id, meta={"raw": content}, **parsed)
    return f"seo pack: {parsed['title'][:60]}"


def _stage_thumbnail(db: Session, project: Project, context: str) -> str:
    content = _run_role(
        db,
        "thumbnail_designer",
        f"3 thumbnail concepts for '{project.name}' with an image prompt each.",
        project,
        context,
    )
    Repository(Thumbnail, db).create(
        project_id=project.id, title_text=project.name[:200], meta={"concepts": content}
    )
    return "thumbnail concepts saved"


HANDLERS = {
    "research": _stage_research,
    "script": _stage_script,
    "storyboard": _stage_storyboard,
    "prompts": _stage_prompts,
    "images": _stage_images,
    "voice": _stage_voice,
    "seo": _stage_seo,
    "thumbnail": _stage_thumbnail,
}


def next_stage(run: PipelineRun) -> str | None:
    done = {entry["stage"] for entry in run.log if entry.get("status") in ("done", "skipped")}
    for name in STAGE_NAMES:
        if name not in done:
            return name
    return None


def execute_stage(db: Session, run: PipelineRun, project: Project) -> dict:
    stage = next_stage(run)
    runs = Repository(PipelineRun, db)
    if stage is None:
        runs.update(run.id, status="done", current_stage="")
        return {"stage": None, "status": "done", "detail": "all stages complete"}

    runs.update(run.id, status="running", current_stage=stage)
    context = _base_context(db, project)
    try:
        detail = HANDLERS[stage](db, project, context)
    except Exception as e:
        logger.exception("pipeline stage %s failed", stage)
        entry = {"stage": stage, "status": "error", "detail": str(e)[:500]}
        runs.update(run.id, status="error", log=[*run.log, entry])
        bus.emit("pipeline.stage.failed", {"run_id": run.id, "stage": stage})
        return entry

    status = "skipped" if detail.startswith("skipped") else "done"
    entry = {"stage": stage, "status": status, "detail": detail}
    new_log = [*run.log, entry]
    stage_status = dict(STAGES)[stage]
    if status == "done":
        Repository(Project, db).update(project.id, status=stage_status)
    finished = all(s in {e["stage"] for e in new_log} for s in STAGE_NAMES)
    runs.update(
        run.id,
        status="done" if finished else "idle",
        current_stage="" if finished else stage,
        log=new_log,
    )
    bus.emit("pipeline.stage.finished", {"run_id": run.id, "stage": stage, "status": status})
    return entry
