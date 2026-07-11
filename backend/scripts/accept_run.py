"""Backend acceptance driver: run every pipeline stage for one project against
the real providers, logging stage status/timing and produced assets. Not the
installed GUI (tooling limit) — the same service the GUI calls."""
import time

from app.core.db import init_db, SessionLocal
from app.core.repository import Repository
from app.modules.projects.models import Project
from app.modules.pipeline.models import PipelineRun
from app.modules.pipeline import service
from app.modules.assets.models import Asset
from sqlalchemy import select

init_db()
db = SessionLocal()
proj = Repository(Project, db).create(
    name="Acceptance E2E",
    idea="A 15-second cinematic clip: two characters greet each other on a rooftop at sunset",
)
run = Repository(PipelineRun, db).create(project_id=proj.id)
print(f"project={proj.id} run={run.id}", flush=True)

for _ in range(len(service.STAGE_NAMES) + 2):
    if service.next_stage(run) is None:
        print("PIPELINE COMPLETE", flush=True)
        break
    t0 = time.time()
    entry = service.execute_stage(db, run, proj)
    msg = str(entry.get("output") or entry.get("detail") or "")[:160]
    print(f"[{entry.get('stage')}] {entry.get('status')} {time.time()-t0:.0f}s :: {msg}", flush=True)
    run = Repository(PipelineRun, db).get(run.id)
    if entry.get("status") == "error":
        print("STOPPED ON ERROR", flush=True)
        break

assets = db.scalars(select(Asset).where(Asset.project_id == proj.id)).all()
print(f"=== {len(assets)} assets ===", flush=True)
for a in assets:
    print(f"  {a.kind:<10} {a.path}", flush=True)
db.close()
