def test_research_crud(client, project):
    pid = project["id"]
    resp = client.post(
        "/api/research",
        json={"project_id": pid, "query": "topic trends", "sources": ["https://example.com"]},
    )
    assert resp.status_code == 201
    note = resp.json()

    listed = client.get("/api/research", params={"project_id": pid}).json()
    assert [n["id"] for n in listed] == [note["id"]]

    resp = client.patch(f"/api/research/{note['id']}", json={"content": "findings"})
    assert resp.status_code == 200
    assert resp.json()["content"] == "findings"

    assert client.delete(f"/api/research/{note['id']}").status_code == 204
    assert client.get(f"/api/research/{note['id']}").status_code == 404
