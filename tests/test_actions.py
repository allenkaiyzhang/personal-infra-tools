from __future__ import annotations

import httpx

from fastapi_message import ping


def test_ping_uses_health_path(registry_file, monkeypatch):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"status": "ok"}))

    class Client(httpx.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "Client", Client)
    assert ping("demo") == {"status": "ok"}
