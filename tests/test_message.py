from __future__ import annotations

import httpx
import pytest

from fastapi_message import send_action
from fastapi_message.errors import DecodeError, UnauthorizedError, UpstreamError


def _patch_client(monkeypatch: pytest.MonkeyPatch, handler):
    transport = httpx.MockTransport(handler)

    class Client(httpx.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "Client", Client)


def test_send_action_decodes_json_and_adds_headers(registry_file, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://demo.local/echo"
        assert request.headers["X-Request-ID"] == "rid-1"
        assert request.headers["X-Source-Service"] == "source"
        assert request.headers["X-Target-Service"] == "demo"
        assert "Authorization" not in request.headers
        return httpx.Response(200, json={"ok": True})

    _patch_client(monkeypatch, handler)
    assert send_action("demo", "echo", {"hello": "world"}, request_id="rid-1") == {"ok": True}


def test_decode_error_for_non_json_success(registry_file, monkeypatch):
    _patch_client(monkeypatch, lambda request: httpx.Response(200, text="not-json"))
    with pytest.raises(DecodeError):
        send_action("demo", "echo", {})


@pytest.mark.parametrize(
    ("status_code", "exc_type"),
    [(401, UnauthorizedError), (500, UpstreamError), (503, UpstreamError)],
)
def test_status_code_error_mapping(registry_file, monkeypatch, status_code, exc_type):
    _patch_client(monkeypatch, lambda request: httpx.Response(status_code, json={"error": {"code": "x", "message": "bad"}}))
    with pytest.raises(exc_type):
        send_action("demo", "echo", {})
