from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPS_CORE_ALLOW_NO_AUTH", "1")
    monkeypatch.setenv("AI_AGENT_TOKEN", "agent-secret")
    monkeypatch.setenv("AI_SEARCHER_TOKEN", "searcher-secret")
    monkeypatch.setenv("PRIVATE_DB_TOKEN", "db-secret")
    from ops_core.main import app

    return TestClient(app)


def command_event(name: str = "start") -> dict:
    return {
        "channel": "telegram",
        "event_type": "command",
        "user": {"id": "123456789", "username": "kevin"},
        "chat": {"id": "123456789", "type": "private"},
        "message": {"id": 1001, "text": f"/{name}"},
        "command": {"name": name, "args": []},
    }


def callback_event(action: str) -> dict:
    return {
        "channel": "telegram",
        "event_type": "callback",
        "user": {"id": "123456789"},
        "chat": {"id": "123456789", "type": "private"},
        "callback": {"id": "callback-id", "action": action, "message_id": 1001},
    }


def test_health_returns_control_plane(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ops-core", "role": "control-plane"}


def test_protected_endpoint_rejects_missing_token(monkeypatch):
    monkeypatch.delenv("OPS_CORE_ALLOW_NO_AUTH", raising=False)
    monkeypatch.setenv("OPS_CORE_TOKEN", "secret")
    from ops_core.main import app

    response = TestClient(app).get("/api/services")
    assert response.status_code == 401


def test_start_returns_home_ui(client):
    response = client.post("/api/interactions/telegram", json=command_event("start"))
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["response"]["type"] == "screen"
    assert "ops-core" in body["response"]["text"]


def test_services_list_contains_initial_services(client):
    response = client.post("/api/interactions/telegram", json=callback_event("services:list"))
    text = response.json()["response"]["text"]
    assert "AI Agent" in text
    assert "AI Searcher" in text
    assert "Private DB" in text


@pytest.mark.parametrize("service_id", ["ai_agent", "ai_searcher", "private_db"])
def test_services_view_works_for_all_three(client, service_id):
    response = client.post("/api/interactions/telegram", json=callback_event(f"services:view:{service_id}"))
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_unknown_service_returns_error_ui(client):
    response = client.post("/api/interactions/telegram", json=callback_event("services:view:missing"))
    assert response.status_code == 200
    assert "Unknown service" in response.json()["response"]["text"]


def test_health_action_builds_url_from_registry(client, monkeypatch):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"status": "ok"})

    _patch_httpx(monkeypatch, handler)
    response = client.post("/api/services/ai_agent/actions/health", json={})
    assert response.status_code == 200
    assert seen["url"] == "http://127.0.0.1:8001/health"


def test_demo_action_uses_registry_payload(client, monkeypatch):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["json"] = request.read().decode()
        return httpx.Response(200, json={"ok": True})

    _patch_httpx(monkeypatch, handler)
    response = client.post("/api/services/ai_searcher/actions/demo", json={})
    assert response.status_code == 200
    assert '"query":"demo"' in seen["json"].replace(" ", "")


def test_ai_searcher_demo_executes_immediately(client, monkeypatch):
    _patch_httpx(monkeypatch, lambda request: httpx.Response(200, json={"result": "ok"}))
    response = client.post("/api/interactions/telegram", json=callback_event("services:demo:ai_searcher"))
    assert response.status_code == 200
    assert "Action result" in response.json()["response"]["text"]


@pytest.mark.parametrize("service_id", ["ai_agent", "private_db"])
def test_unsafe_demo_requires_confirmation(client, service_id):
    response = client.post("/api/interactions/telegram", json=callback_event(f"services:demo:{service_id}"))
    assert response.status_code == 200
    assert "Confirm demo" in response.json()["response"]["text"]


def test_confirm_demo_executes_registry_action(client, monkeypatch):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"done": True})

    _patch_httpx(monkeypatch, handler)
    response = client.post("/api/interactions/telegram", json=callback_event("services:confirm_demo:ai_agent"))
    assert response.status_code == 200
    assert seen["url"] == "http://127.0.0.1:8001/pipeline/run"


def test_arbitrary_url_path_method_rejected(client):
    response = client.post(
        "/api/services/ai_searcher/actions/demo",
        json={"confirmed": True, "url": "http://evil.local", "path": "/x", "method": "POST"},
    )
    assert response.status_code == 400


def test_unavailable_downstream_returns_clear_failure(client, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    _patch_httpx(monkeypatch, handler)
    response = client.post("/api/interactions/telegram", json=callback_event("services:demo:ai_searcher"))
    assert response.status_code == 200
    assert "Action failed" in response.json()["response"]["text"]
    assert "connection refused" in response.json()["response"]["text"]


def test_tokens_are_not_leaked_in_ui(client, monkeypatch):
    monkeypatch.setenv("AI_SEARCHER_TOKEN", "super-secret-token")
    _patch_httpx(monkeypatch, lambda request: httpx.Response(200, json={"ok": True}))
    response = client.post("/api/interactions/telegram", json=callback_event("services:demo:ai_searcher"))
    assert "super-secret-token" not in response.text


def _patch_httpx(monkeypatch: pytest.MonkeyPatch, handler):
    transport = httpx.MockTransport(handler)

    class Client(httpx.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "Client", Client)
