def test_scripts_crud(client, project):
    pid = project["id"]
    resp = client.post("/api/scripts", json={"project_id": pid, "title": "Intro"})
    assert resp.status_code == 201
    sid = resp.json()["id"]

    listed = client.get("/api/scripts", params={"project_id": pid}).json()
    assert [s["id"] for s in listed] == [sid]

    resp = client.patch(f"/api/scripts/{sid}", json={"title": "Intro v2"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Intro v2"

    assert client.delete(f"/api/scripts/{sid}").status_code == 204
    assert client.get(f"/api/scripts/{sid}").status_code == 404
