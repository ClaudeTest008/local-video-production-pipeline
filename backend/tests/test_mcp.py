def test_mcp_discover_toggle_export(client):
    catalog = client.get("/api/mcp/catalog").json()
    names = {entry["name"] for entry in catalog}
    assert {"filesystem", "git", "github", "comfyui", "ffmpeg", "whisper", "local-rag"} <= names

    discovered = client.post("/api/mcp/discover").json()
    assert set(discovered["added"]) == names
    assert client.post("/api/mcp/discover").json()["added"] == []  # idempotent

    servers = client.get("/api/mcp/servers").json()
    fs = next(s for s in servers if s["name"] == "filesystem")
    assert fs["enabled"] is False

    toggled = client.post(f"/api/mcp/servers/{fs['id']}/toggle").json()
    assert toggled["enabled"] is True

    export = client.get("/api/mcp/export").json()
    assert "filesystem" in export["mcpServers"]
    assert export["mcpServers"]["filesystem"]["command"] == "npx"

    # custom server without touching core
    created = client.post(
        "/api/mcp/servers",
        json={"name": "my-server", "command": "uvx", "args": ["my-mcp"], "enabled": True},
    )
    assert created.status_code == 201
    assert (
        client.post("/api/mcp/servers", json={"name": "my-server", "command": "x"}).status_code
        == 409
    )
    assert "my-server" in client.get("/api/mcp/export").json()["mcpServers"]
