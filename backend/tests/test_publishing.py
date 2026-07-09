def test_publishing_crud(client, project):
    created = client.post(
        "/api/publishing",
        json={"project_id": project["id"], "platform": "tiktok"},
    )
    assert created.status_code == 201
    job = created.json()
    assert job["platform"] == "tiktok"
    assert job["status"] == "draft"

    listed = client.get("/api/publishing", params={"project_id": project["id"]}).json()
    assert [j["id"] for j in listed] == [job["id"]]

    patched = client.patch(f"/api/publishing/{job['id']}", json={"status": "scheduled"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "scheduled"

    assert client.delete(f"/api/publishing/{job['id']}").status_code == 204
    assert client.get(f"/api/publishing/{job['id']}").status_code == 404
