def test_assets_crud(client, project):
    pid = project["id"]
    resp = client.post(
        "/api/assets",
        json={"project_id": pid, "path": "assets/images/a.png", "kind": "image"},
    )
    assert resp.status_code == 201
    asset = resp.json()

    listed = client.get("/api/assets", params={"project_id": pid}).json()
    assert [a["id"] for a in listed] == [asset["id"]]

    resp = client.patch(f"/api/assets/{asset['id']}", json={"source": "comfyui"})
    assert resp.status_code == 200
    assert resp.json()["source"] == "comfyui"

    assert client.delete(f"/api/assets/{asset['id']}").status_code == 204
    assert client.get(f"/api/assets/{asset['id']}").status_code == 404
