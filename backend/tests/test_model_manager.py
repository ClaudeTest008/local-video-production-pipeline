def test_model_manager_crud(client):
    r = client.post(
        "/api/models",
        json={"name": "llama3", "kind": "llm", "location": "C:/models/llama3"},
    )
    assert r.status_code == 201
    mid = r.json()["id"]
    assert r.json()["provider"] == "ollama"

    items = client.get("/api/models").json()
    assert any(m["id"] == mid for m in items)

    r = client.patch(f"/api/models/{mid}", json={"enabled": False})
    assert r.status_code == 200
    assert r.json()["enabled"] is False

    assert client.delete(f"/api/models/{mid}").status_code == 204
    assert client.get(f"/api/models/{mid}").status_code == 404
