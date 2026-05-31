#!/bin/sh
set -eu

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export SERVICE_REGISTRY_PATH="$ROOT_DIR/config/services.example.yaml"
export SERVICE_NAME="smoke_test"
export PRIVATE_INFO_DB_TOKEN="${PRIVATE_INFO_DB_TOKEN:-smoke-token}"
export API_TOKEN="${API_TOKEN:-smoke-token}"
PYTHON="${PYTHON:-python}"

"$PYTHON" - <<'PY'
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

import fastapi_message
from fastapi_message import send_action
from fastapi_message.registry import validate_registry

validate_registry()

app = FastAPI()
fastapi_message.setup_message_pipeline(
    app,
    service_name="smoke_test",
    version="smoke",
    auth_mode="bearer",
)

client = TestClient(app)
health = client.get("/health")
assert health.status_code == 200, health.text
assert health.json()["status"] == "ok"

unauthorized = client.get("/pipeline/hello")
assert unauthorized.status_code == 401, unauthorized.text

hello = client.get(
    "/pipeline/hello",
    headers={
        "Authorization": "Bearer smoke-token",
        "X-Source-Service": "smoke-client",
        "X-Request-ID": "smoke-request",
    },
)
assert hello.status_code == 200, hello.text
assert hello.json()["request_id"] == "smoke-request"

calls = []
transport = httpx.MockTransport(
    lambda request: (
        calls.append(request),
        httpx.Response(200, json={"ok": True}, headers={"X-Request-ID": request.headers["X-Request-ID"]}),
    )[1]
)
original_client = httpx.Client

class Client(httpx.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, transport=transport, **kwargs)

httpx.Client = Client
try:
    result = send_action("personal_ai_searcher", "search", {"query": "hello"}, request_id="smoke-outbound")
finally:
    httpx.Client = original_client

assert result == {"ok": True}
assert calls
outbound = calls[0]
assert outbound.headers["X-Request-ID"] == "smoke-outbound"
assert outbound.headers["X-Source-Service"] == "smoke_test"
assert outbound.headers["X-Target-Service"] == "personal_ai_searcher"

print("PASS")
PY
