def test_prompts_crud(client, project):
    pid = project["id"]
    resp = client.post(
        "/api/prompts",
        json={"project_id": pid, "name": "Scene 1", "text": "a castle", "kind": "image"},
    )
    assert resp.status_code == 201
    prompt = resp.json()

    listed = client.get("/api/prompts", params={"project_id": pid}).json()
    assert any(p["id"] == prompt["id"] for p in listed)

    resp = client.patch(f"/api/prompts/{prompt['id']}", json={"text": "a dark castle"})
    assert resp.status_code == 200
    assert resp.json()["text"] == "a dark castle"

    assert client.delete(f"/api/prompts/{prompt['id']}").status_code == 204
    assert client.get(f"/api/prompts/{prompt['id']}").status_code == 404
