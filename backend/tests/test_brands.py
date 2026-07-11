from app.modules.brands.models import Brand, brand_context


def test_brand_crud_and_project_link(client):
    brand = client.post(
        "/api/brands",
        json={
            "name": "History Deep Dives",
            "voice": "calm, authoritative",
            "style": "cinematic, desaturated",
            "audience": "25-45 documentary fans",
            "platforms": ["youtube"],
            "goals": "100k subscribers",
        },
    )
    assert brand.status_code == 201
    bid = brand.json()["id"]

    project = client.post(
        "/api/projects", json={"name": "Rome Falls", "brand_id": bid, "idea": "why Rome fell"}
    ).json()
    assert project["brand_id"] == bid

    listed = client.get("/api/projects", params={"brand_id": bid}).json()
    assert any(p["id"] == project["id"] for p in listed)

    updated = client.patch(f"/api/brands/{bid}", json={"memory": {"best_hook": "cold open"}})
    assert updated.json()["memory"] == {"best_hook": "cold open"}

    client.delete(f"/api/projects/{project['id']}")
    assert client.delete(f"/api/brands/{bid}").status_code == 204


def test_brand_context_block():
    brand = Brand(name="X", voice="dry humor", platforms=["tiktok"], memory={"k": "v"})
    text = brand_context(brand)
    assert "Brand: X" in text and "dry humor" in text and "tiktok" in text and "k" in text
    assert brand_context(None) == ""
