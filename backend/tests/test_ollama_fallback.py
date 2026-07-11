"""Ollama resilience: a configured model that isn't pulled must not break the
pipeline — resolve to an installed model instead."""

import httpx
import pytest

from app.core.ai import ollama as ollama_mod
from app.core.ai.base import ChatMessage, ProviderError


def test_resolve_model_prefers_exact_then_base_then_first(monkeypatch):
    p = ollama_mod.OllamaProvider(base_url="http://x")
    monkeypatch.setattr(p, "list_models", lambda: ["gemma4:latest", "llama3.1:latest"])
    assert p._resolve_model("gemma4:latest") == "gemma4:latest"  # exact
    assert p._resolve_model("llama3.1") == "llama3.1:latest"  # tag-insensitive
    assert p._resolve_model("qwen") == "gemma4:latest"  # absent -> first installed

    monkeypatch.setattr(p, "list_models", lambda: [])
    assert p._resolve_model("llama3.1") == "llama3.1"  # nothing installed -> unchanged


def _resp(status, json_body):
    return httpx.Response(status, json=json_body, request=httpx.Request("POST", "http://x/api/chat"))


def test_chat_falls_back_when_configured_model_missing(monkeypatch):
    p = ollama_mod.OllamaProvider(base_url="http://x")
    monkeypatch.setattr(p, "list_models", lambda: ["gemma4:latest"])
    calls = []

    def fake_post(url, json, timeout):
        calls.append(json["model"])
        if json["model"] == "llama3.1":
            return _resp(404, {"error": "model 'llama3.1' not found"})
        return _resp(200, {"message": {"content": "hi from " + json["model"]}, "eval_count": 3})

    monkeypatch.setattr(ollama_mod.httpx, "post", fake_post)
    out = p.chat([ChatMessage("user", "hello")], model="llama3.1")
    assert out.content == "hi from gemma4:latest"
    assert out.model == "gemma4:latest"
    assert calls == ["llama3.1", "gemma4:latest"]  # tried configured, then fell back


def test_chat_clear_error_when_nothing_installed(monkeypatch):
    p = ollama_mod.OllamaProvider(base_url="http://x")
    monkeypatch.setattr(p, "list_models", lambda: [])
    monkeypatch.setattr(
        ollama_mod.httpx, "post", lambda url, json, timeout: _resp(404, {"error": "not found"})
    )
    with pytest.raises(ProviderError, match="ollama pull"):
        p.chat([ChatMessage("user", "hi")], model="llama3.1")
