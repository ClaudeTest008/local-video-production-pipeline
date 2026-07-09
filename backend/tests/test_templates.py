def test_templates_crud(client):
    resp = client.post(
        "/api/templates",
        json={"name": "Intro hook", "kind": "prompt", "tags": ["hook"], "meta": {"lang": "en"}},
    )
    assert resp.status_code == 201
    tpl = resp.json()
    tid = tpl["id"]
    assert tpl["kind"] == "prompt"
    assert tpl["content"] == ""

    items = client.get("/api/templates").json()
    assert any(t["id"] == tid for t in items)

    resp = client.patch(f"/api/templates/{tid}", json={"content": "Hello {name}"})
    assert resp.status_code == 200
    assert resp.json()["content"] == "Hello {name}"

    assert client.delete(f"/api/templates/{tid}").status_code == 204
    assert client.get(f"/api/templates/{tid}").status_code == 404
