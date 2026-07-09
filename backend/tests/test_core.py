import pytest

from app.core.ai.base import ProviderError
from app.core.ai.registry import get_provider, list_providers
from app.core.events import EventBus


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_openapi_has_module_routes(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/projects" in paths
    assert "/api/settings/{key}" in paths


def test_event_bus_exact_and_wildcard():
    bus = EventBus()
    seen = []
    bus.subscribe("asset.created", lambda t, p: seen.append(("exact", t)))
    bus.subscribe("asset.*", lambda t, p: seen.append(("wild", t)))
    bus.subscribe("*", lambda t, p: seen.append(("all", t)))
    bus.emit("asset.created", {"id": 1})
    bus.emit("project.created")
    assert ("exact", "asset.created") in seen
    assert ("wild", "asset.created") in seen
    assert ("all", "project.created") in seen
    assert ("wild", "project.created") not in seen


def test_event_bus_handler_error_isolated():
    bus = EventBus()
    seen = []
    bus.subscribe("x", lambda t, p: 1 / 0)
    bus.subscribe("x", lambda t, p: seen.append(t))
    bus.emit("x")
    assert seen == ["x"]


def test_provider_registry():
    assert {"ollama", "openai", "anthropic", "gemini", "openrouter", "lmstudio"} <= set(
        list_providers()
    )
    assert get_provider("ollama").name == "ollama"
    with pytest.raises(ProviderError):
        get_provider("nope")
