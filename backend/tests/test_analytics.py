def test_analytics_crud(client, project):
    pid = project["id"]
    resp = client.post(
        "/api/analytics",
        json={"project_id": pid, "views": 100, "captured_at": "2026-07-09"},
    )
    assert resp.status_code == 201
    snap = resp.json()
    assert snap["platform"] == "youtube"

    listed = client.get("/api/analytics", params={"project_id": pid}).json()
    assert any(s["id"] == snap["id"] for s in listed)

    resp = client.patch(f"/api/analytics/{snap['id']}", json={"likes": 42})
    assert resp.status_code == 200
    assert resp.json()["likes"] == 42

    assert client.delete(f"/api/analytics/{snap['id']}").status_code == 204
    assert client.get(f"/api/analytics/{snap['id']}").status_code == 404
