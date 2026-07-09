def test_storyboard_crud(client, project):
    pid = project["id"]
    resp = client.post(
        "/api/storyboard",
        json={"project_id": pid, "title": "Opening", "prompt": "wide shot", "duration_s": 3.5},
    )
    assert resp.status_code == 201
    scene = resp.json()
    sid = scene["id"]
    assert scene["title"] == "Opening"

    listed = client.get("/api/storyboard", params={"project_id": pid}).json()
    assert [s["id"] for s in listed] == [sid]

    resp = client.patch(f"/api/storyboard/{sid}", json={"order_index": 2})
    assert resp.status_code == 200
    assert resp.json()["order_index"] == 2

    assert client.delete(f"/api/storyboard/{sid}").status_code == 204
    assert client.get(f"/api/storyboard/{sid}").status_code == 404
