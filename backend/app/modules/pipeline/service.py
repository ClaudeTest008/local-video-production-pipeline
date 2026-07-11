"""The autonomous production orchestrator.

Each stage handler: gather context (brand + prior artifacts) → run the right
agent role → persist artifacts into the owning feature module → advance the
project's pipeline status. Handlers are ordered; a run steps through them.

Media stages are best-effort: they run when ComfyUI is reachable and are
logged as skipped otherwise — a run never fails because optional local
tooling is absent. Voice and lip-sync come from ComfyUI workflows only.
"""

import logging
import threading

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
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
    ("video", "video"),
    ("captions", "captions"),
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
    brand = db.get(Brand, project.brand_id) if project.brand_id else None
    _, content, _, _ = agent_service.run_agent(
        db,
        agent,
        user_input,
        project_id=project.id,
        context=context,
        provider_override=brand.preferred_provider if brand else "",
        model_override=brand.preferred_model if brand else "",
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


def _quality_review(
    db: Session, project: Project, context: str, kind: str, content: str, reviser_role: str
) -> tuple[str, dict]:
    """Generate → critique → improve. Creative Director issues a verdict; on
    REVISE the producing agent gets one revision pass. Never raises past the
    stage handler — a failed review keeps the original artifact."""
    from app.core.config import settings

    if not settings.pipeline_review:
        return content, {}
    critique = _run_role(
        db,
        "creative_director",
        f"Critique this {kind} against the brand goals in context: hook strength, structure, "
        f"pacing, clarity. Concrete, ranked improvements. End with exactly "
        f"'VERDICT: APPROVE' or 'VERDICT: REVISE'.\n\n{content[:6000]}",
        project,
        context,
    )
    review = {"critique": critique, "revised": False}
    if "VERDICT: REVISE" in critique.upper():
        content = _run_role(
            db,
            reviser_role,
            f"Revise the {kind} below applying this critique. Output ONLY the revised {kind}, "
            f"no commentary.\nCritique:\n{critique[:3000]}\n\n{kind.capitalize()}:\n"
            f"{content[:6000]}",
            project,
            context,
        )
        review["revised"] = True
    return content, review


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
    content, review = _quality_review(db, project, context, "script", content, "script_writer")
    Repository(Script, db).create(
        project_id=project.id, title=f"{project.name} v1", content=content, meta=review
    )
    verdict = "revised after review" if review.get("revised") else "approved on review"
    if not review:
        verdict = "review disabled"
    return f"script saved ({len(content.split())} words, {verdict})"


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


def _stage_video(db: Session, project: Project, context: str) -> str:
    """Render every scene through the best enabled ComfyUI workflow (video +
    integrated voice/lip-sync preferred), wait, auto-import the outputs into
    project assets, and assemble the timeline."""
    import time

    from app.core import files
    from app.core.config import settings
    from app.modules.assets.models import Asset
    from app.modules.comfyui import service as comfy_service
    from app.modules.comfyui.client import ComfyUIClient
    from app.modules.comfyui.models import ComfyJob
    from app.modules.timeline.models import Timeline
    from app.modules.workflows.models import WorkflowDef
    from app.modules.workflows.service import select_workflow

    client = ComfyUIClient()
    if not client.is_available():
        return "skipped: ComfyUI not running"
    object_info = client.object_info()  # drives dependency-aware workflow selection
    brand = db.get(Brand, project.brand_id) if project.brand_id else None
    scenes = [s for s in _scenes(db, project.id) if s.prompt]
    if not scenes:
        return "skipped: no scenes with prompts to render"

    jobs_repo = Repository(ComfyJob, db)
    workflows_repo = Repository(WorkflowDef, db)
    tried: set[int] = set()
    workflow = None
    note = ""
    jobs = []
    # A workflow ComfyUI rejects (missing input, bad widget mapping) is flagged
    # and the next candidate tried. Keep falling back until one enqueues — giving
    # up after a few tries stranded known-good workflows behind ones with
    # converter issues. select_workflow returns None once candidates are
    # exhausted; the cap is just a runaway guard.
    for _attempt in range(12):
        workflow, note = select_workflow(
            db,
            preferred_id=(
                brand.preferred_workflow_id
                if brand and brand.preferred_workflow_id not in tried
                else None
            ),
            want=("video_lipsync", "avatar", "video"),
            exclude=tuple(tried),
            object_info=object_info,
        )
        if workflow is None:
            return f"skipped: {note}"
        tried.add(workflow.id)
        jobs = []
        failed_validation = False
        for scene in scenes:
            # lip-sync/video workflows speak the scene text: prompt carries visuals + dialogue
            prompt = scene.prompt
            if scene.description and workflow.wf_type in ("video_lipsync", "avatar"):
                prompt = f"{scene.prompt}. Spoken dialogue: {scene.description}"
            graph = comfy_service.inject_prompt(workflow.graph, prompt)
            try:
                prompt_id = client.queue_prompt(graph)
            except Exception as e:
                logger.warning("queue failed for scene %s via '%s': %s", scene.id, workflow.name, e)
                workflows_repo.update(
                    workflow.id,
                    meta={
                        **workflow.meta,
                        "conversion_status": "failed",
                        "last_error": str(e)[:800],
                    },
                )
                failed_validation = True
                break
            job = jobs_repo.create(
                project_id=project.id,
                prompt_id=prompt_id,
                workflow=graph,
                workflow_def_id=workflow.id,
                meta={"scene_id": scene.id, "duration_s": scene.duration_s},
            )
            comfy_service.record_queued(job)
            jobs.append(job)
        if not failed_validation:
            break
    if not jobs:
        return (
            "skipped: every candidate workflow was rejected by ComfyUI — open the "
            "Workflows page ('check' badges show details) or upload an API-format export"
        )

    # wait for renders, then auto-import outputs into the project tree
    deadline = time.time() + settings.render_timeout_s * len(jobs)
    clips: list[dict] = []
    imported = 0
    assets_repo = Repository(Asset, db)
    for job in jobs:
        while job.status == "queued" and time.time() < deadline:
            time.sleep(5)
            job = comfy_service.refresh_job(db, client, job)
        for output in job.outputs or []:
            kind = (
                "video"
                if output.get("kind") in ("videos", "gifs")
                else ("audio" if output.get("kind") == "audio" else "image")
            )
            dest_dir = (
                files.project_dir(project.id)
                / "assets"
                / ("video" if kind == "video" else "audio" if kind == "audio" else "images")
            )
            try:
                path = comfy_service.download_output(client, output, dest_dir)
            except Exception as e:
                logger.warning("auto-import failed for %s: %s", output.get("filename"), e)
                continue
            assets_repo.create(project_id=project.id, kind=kind, path=path, source="comfyui")
            imported += 1
            if kind in ("video", "image"):
                clips.append({"path": path, "duration": (job.meta or {}).get("duration_s")})

    if clips:
        Repository(Timeline, db).create(
            project_id=project.id,
            name="Auto assembly",
            tracks=[{"kind": "video", "clips": clips}],
        )
    unfinished = sum(1 for j in jobs if j.status == "queued")
    detail = (
        f"{len(jobs)} scenes rendered via {note}; {imported} outputs auto-imported; "
        f"timeline assembled with {len(clips)} clips"
    )
    if unfinished:
        detail += f"; {unfinished} still rendering (retry the stage to collect them)"
    if workflow.wf_type == "image":
        detail += ". NOTE: only image workflows available — no native voice/lip-sync"
    return detail


def _stage_captions(db: Session, project: Project, context: str) -> str:
    """Caption track from the script, timed across the storyboard; SRT written
    into the project tree. Burn happens on timeline export (burn_subtitles)."""
    import re

    from app.core import files
    from app.modules.subtitles.models import SubtitleTrack
    from app.modules.subtitles.service import to_srt

    script = _latest_script(db, project.id)
    if script is None:
        return "skipped: no script"
    scenes = _scenes(db, project.id)
    total = sum(s.duration_s for s in scenes) or 60.0
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", re.sub(r"[#*\[\]()]", "", script.content))
        if 15 < len(s.strip()) < 220
    ][:40]
    if not sentences:
        return "skipped: script has no caption-able sentences"
    per = total / len(sentences)
    segments = [
        {"start": round(i * per, 2), "end": round((i + 1) * per, 2), "text": s}
        for i, s in enumerate(sentences)
    ]
    track = Repository(SubtitleTrack, db).create(project_id=project.id, segments=segments)
    srt_path = files.project_dir(project.id) / "captions" / "captions.srt"
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.write_text(to_srt(segments), encoding="utf-8")
    return f"{len(segments)} caption segments (track {track.id}) -> {srt_path}"


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
    content, review = _quality_review(db, project, context, "seo pack", content, "seo_specialist")
    parsed = parsers.parse_seo(content)
    Repository(SeoPack, db).create(project_id=project.id, meta={"raw": content, **review}, **parsed)
    return f"seo pack: {parsed['title'][:60]}"


def _stage_thumbnail(db: Session, project: Project, context: str) -> str:
    content = _run_role(
        db,
        "thumbnail_designer",
        f"3 thumbnail concepts for '{project.name}' with an image prompt each.",
        project,
        context,
    )
    content, review = _quality_review(
        db, project, context, "thumbnail concepts", content, "thumbnail_designer"
    )
    Repository(Thumbnail, db).create(
        project_id=project.id, title_text=project.name[:200], meta={"concepts": content, **review}
    )
    return "thumbnail concepts saved"


HANDLERS = {
    "research": _stage_research,
    "script": _stage_script,
    "storyboard": _stage_storyboard,
    "prompts": _stage_prompts,
    "video": _stage_video,
    "captions": _stage_captions,
    "seo": _stage_seo,
    "thumbnail": _stage_thumbnail,
}


def run_remaining(db: Session, run_id: int) -> None:
    """Execute every remaining stage; stop on error or completion."""
    for _ in range(len(STAGE_NAMES)):
        run = db.get(PipelineRun, run_id)
        project = db.get(Project, run.project_id) if run else None
        if run is None or project is None or next_stage(run) is None:
            return
        if execute_stage(db, run, project)["status"] == "error":
            return


def start_background(db: Session, run: PipelineRun) -> None:
    """Producer run in a background thread; poll GET /pipeline/runs/{id}."""
    Repository(PipelineRun, db).update(
        run.id, status="running", meta={**run.meta, "background": True}
    )

    def worker(run_id: int = run.id) -> None:
        with SessionLocal() as thread_db:
            try:
                run_remaining(thread_db, run_id)
            except Exception:
                logger.exception("background run %s crashed", run_id)
                Repository(PipelineRun, thread_db).update(run_id, status="error")

    threading.Thread(target=worker, daemon=True, name=f"pipeline-run-{run.id}").start()


def _recover_interrupted(topic: str, payload: dict) -> None:
    """Runs left 'running' by a previous process died with it — surface that."""
    with SessionLocal() as db:
        stale = db.scalars(select(PipelineRun).where(PipelineRun.status == "running")).all()
        for run in stale:
            Repository(PipelineRun, db).update(
                run.id,
                status="error",
                log=[
                    *run.log,
                    {
                        "stage": run.current_stage or "?",
                        "status": "error",
                        "detail": "interrupted by restart — use /step or /run-all to resume",
                    },
                ],
            )
        if stale:
            logger.warning("marked %d interrupted pipeline runs as error", len(stale))


bus.subscribe("app.started", _recover_interrupted)


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
    # background runs stay "running" between stages so pollers see one state
    between = "running" if run.meta.get("background") else "idle"
    runs.update(
        run.id,
        status="done" if finished else between,
        current_stage="" if finished else stage,
        log=new_log,
    )
    bus.emit("pipeline.stage.finished", {"run_id": run.id, "stage": stage, "status": status})
    return entry
