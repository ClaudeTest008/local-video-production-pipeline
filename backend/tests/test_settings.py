def test_settings_roundtrip(client):
    assert client.put("/api/settings/theme", json={"value": {"mode": "dark"}}).status_code == 200
    assert client.get("/api/settings/theme").json() == {"mode": "dark"}
    assert client.get("/api/settings").json()["theme"] == {"mode": "dark"}

    client.put("/api/settings/theme", json={"value": "midnight"})
    assert client.get("/api/settings/theme").json() == "midnight"

    assert client.delete("/api/settings/theme").status_code == 204
    assert client.get("/api/settings/theme").status_code == 404


def test_providers_listed(client):
    names = {p["name"] for p in client.get("/api/settings/providers").json()}
    assert "ollama" in names and "openai" in names
