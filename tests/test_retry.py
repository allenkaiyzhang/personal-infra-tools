from __future__ import annotations

import httpx

from fastapi_message import send_action


def test_retry_on_503_then_success(registry_file, monkeypatch):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"error": {"message": "busy"}})
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)

    class Client(httpx.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "Client", Client)
    assert send_action("demo", "echo", {}) == {"ok": True}
    assert calls == 2
