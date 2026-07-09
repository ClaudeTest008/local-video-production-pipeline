def test_thumbnail_crud(client, project):
    r = client.post(
        "/api/thumbnails",
        json={"project_id": project["id"], "title_text": "Big Title"},
    )
    assert r.status_code == 201
    thumb = r.json()
    assert thumb["title_text"] == "Big Title"
    assert thumb["status"] == "draft"

    listed = client.get("/api/thumbnails", params={"project_id": project["id"]}).json()
    assert any(t["id"] == thumb["id"] for t in listed)

    r = client.patch(f"/api/thumbnails/{thumb['id']}", json={"status": "final"})
    assert r.status_code == 200
    assert r.json()["status"] == "final"

    assert client.delete(f"/api/thumbnails/{thumb['id']}").status_code == 204
    assert client.get(f"/api/thumbnails/{thumb['id']}").status_code == 404
