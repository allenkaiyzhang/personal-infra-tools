#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export SERVICE_REGISTRY_PATH="$ROOT_DIR/config/services.example.yaml"
export SERVICE_NAME="smoke_test"
export PRIVATE_INFO_DB_TOKEN="${PRIVATE_INFO_DB_TOKEN:-smoke-token}"
export API_TOKEN="${API_TOKEN:-smoke-token}"

python - <<'PY'
from fastapi import FastAPI
from fastapi.testclient import TestClient

import fastapi_message
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

print("PASS")
PY
