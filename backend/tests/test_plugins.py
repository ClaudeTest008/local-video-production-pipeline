def test_plugins_crud(client):
    resp = client.post("/api/plugins", json={"name": "uploader", "manifest": {"v": 1}})
    assert resp.status_code == 201
    plugin = resp.json()
    assert plugin["name"] == "uploader"
    assert plugin["enabled"] is False

    listed = client.get("/api/plugins").json()
    assert any(p["id"] == plugin["id"] for p in listed)

    resp = client.patch(f"/api/plugins/{plugin['id']}", json={"enabled": True})
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True

    assert client.delete(f"/api/plugins/{plugin['id']}").status_code == 204
    assert client.get(f"/api/plugins/{plugin['id']}").status_code == 404
