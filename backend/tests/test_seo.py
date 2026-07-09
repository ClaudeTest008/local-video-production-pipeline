def test_seo_crud(client, project):
    pid = project["id"]
    resp = client.post(
        "/api/seo",
        json={"project_id": pid, "title": "My Video", "tags": ["a", "b"]},
    )
    assert resp.status_code == 201
    pack = resp.json()

    listed = client.get("/api/seo", params={"project_id": pid}).json()
    assert [p["id"] for p in listed] == [pack["id"]]

    resp = client.patch(f"/api/seo/{pack['id']}", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"

    assert client.delete(f"/api/seo/{pack['id']}").status_code == 204
    assert client.get(f"/api/seo/{pack['id']}").status_code == 404
