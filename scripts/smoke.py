"""End-to-end release smoke test.

Boots a fresh backend (temp database + temp workspace), runs the full
production pipeline with the offline `echo` provider, and verifies every
artifact. No AI tools, GPU, or network required — optional engines degrade
exactly as they do for real users.

Run:    python scripts/smoke.py            (from the repo root, backend venv)
CI:     the backend job runs it after the unit suite.
Exit:   0 = PASS, 1 = FAIL (first failure printed).
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

PORT = int(os.environ.get("LVPP_SMOKE_PORT", "8397"))
BASE = f"http://127.0.0.1:{PORT}/api"
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"

checks: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        print(f"FAIL: {name} {detail}")
        raise SystemExit(1)
    checks.append(name)
    print(f"  ok: {name}")


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="lvpp-smoke-"))
    env = {
        **os.environ,
        "LVPP_DATABASE_URL": f"sqlite:///{(tmp / 'smoke.db').as_posix()}",
        "LVPP_PROJECTS_ROOT": str(tmp / "projects"),
        "LVPP_LOG_DIR": str(tmp / "logs"),
    }
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        client = httpx.Client(base_url=BASE, timeout=60)
        for _ in range(60):
            try:
                if client.get("/health").status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.5)
        else:
            print("FAIL: backend never became healthy")
            raise SystemExit(1)
        check("backend healthy", True)

        detect = client.get("/system/detect").json()
        check("dependency detection", detect["python"]["found"])

        done = client.post(
            "/setup/complete".replace("/setup", "/system/setup"),
            json={"default_chat_provider": "echo", "default_chat_model": "smoke"},
        ).json()
        check("setup wizard completes", done["complete"])

        brand = client.post(
            "/brands", json={"name": "Smoke Brand", "goals": "verify the release"}
        ).json()
        project = client.post(
            "/projects",
            json={"name": "Smoke Video", "brand_id": brand["id"], "idea": "release smoke test"},
        ).json()
        check("brand + project created", project["brand_id"] == brand["id"])

        run = client.post(
            "/pipeline/runs", json={"project_id": project["id"], "mode": "producer"}
        ).json()
        result = client.post(f"/pipeline/runs/{run['id']}/run-all").json()
        statuses = {e["stage"]: e["status"] for e in result["entries"]}
        check("pipeline completed", result["run"]["status"] == "done", str(statuses))
        for stage in ("research", "script", "storyboard", "prompts", "seo", "thumbnail"):
            check(f"stage {stage}", statuses.get(stage) == "done", str(statuses))
        for stage in ("images", "voice"):
            check(f"stage {stage} graceful", statuses.get(stage) in ("done", "skipped"))

        scripts = client.get("/scripts", params={"project_id": project["id"]}).json()
        check("script artifact", len(scripts) == 1 and len(scripts[0]["content"]) > 0)
        scenes = client.get("/storyboard", params={"project_id": project["id"]}).json()
        check("storyboard artifact", len(scenes) == 3 and all(s["prompt"] for s in scenes))
        seo = client.get("/seo", params={"project_id": project["id"]}).json()
        check("seo artifact", seo[0]["title"].startswith("[echo]"))

        track = client.post(
            "/subtitles",
            json={
                "project_id": project["id"],
                "segments": [{"start": 0, "end": 2, "text": "smoke"}],
            },
        ).json()
        srt = client.get(f"/subtitles/{track['id']}/export", params={"fmt": "srt"})
        check("srt export", "-->" in srt.text)

        archive = client.post(f"/projects/{project['id']}/archive").json()
        check("project archive export", Path(archive["archive"]).exists())

        health = client.get("/system/health").json()
        check("system health", health["backend"] == "ok")

        print(f"\nPASS — {len(checks)} checks")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
