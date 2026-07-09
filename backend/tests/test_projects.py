from pathlib import Path

from app.core import files


def test_create_project_builds_file_tree(project):
    root = files.project_dir(project["id"])
    assert (root / "assets" / "images").is_dir()
    assert (root / "exports").is_dir()


def test_crud_roundtrip(client, project):
    pid = project["id"]
    assert client.get(f"/api/projects/{pid}").json()["name"] == "Test Video"

    resp = client.patch(f"/api/projects/{pid}", json={"status": "script"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "script"

    assert client.patch(f"/api/projects/{pid}", json={"status": "bogus"}).status_code == 422

    assert client.delete(f"/api/projects/{pid}").status_code == 204
    assert client.get(f"/api/projects/{pid}").status_code == 404


def test_snapshot_restore(client, project):
    pid = project["id"]
    client.patch(f"/api/projects/{pid}", json={"description": "v1"})
    snap = client.post(f"/api/projects/{pid}/snapshots", params={"label": "before"}).json()
    client.patch(f"/api/projects/{pid}", json={"description": "v2"})

    restored = client.post(f"/api/projects/{pid}/snapshots/{snap['id']}/restore").json()
    assert restored["description"] == "v1"


def test_archive_export(client, project):
    pid = project["id"]
    resp = client.post(f"/api/projects/{pid}/archive")
    assert resp.status_code == 200
    assert Path(resp.json()["archive"]).exists()


def test_stages(client):
    stages = client.get("/api/projects/stages").json()
    assert stages[0] == "idea" and "seo" in stages
