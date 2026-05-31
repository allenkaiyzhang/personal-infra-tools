# personal-infra-tools

`personal-infra-tools` provides the `fastapi_message` Python package: a small registry-driven helper for calling one FastAPI service from another with:

```python
from fastapi_message import send_action

result = send_action("api_report_agent", "run", {"topic": "market"})
```

Business code should not hard-code URL, port, HTTP method, API path, auth mode, token, headers, request id, `httpx` details, `response.json()`, or status-code handling. Those details live in `services.yaml` and inside `fastapi_message`.

## What This Solves

- Cross-service FastAPI calls through `send_action(service, action, payload)`.
- Multipart file calls through `send_file_action(service, action, file_path, fields=...)`.
- Standard outbound headers: `X-Request-ID`, `X-Source-Service`, `X-Target-Service`, `User-Agent`, and optional `X-Idempotency-Key`.
- Registry-based auth and route lookup.
- Consistent exceptions for config, network, decode, auth, and upstream failures.
- A minimal inbound FastAPI pipeline with `/health`, `/pipeline/hello`, request id propagation, access logs, and bearer hello check.
- CLI commands for validation and troubleshooting.

## What This Does Not Solve

This package does not implement Telegram bots, private-info-db ingest logic, embeddings, indexing, search business logic, report generation, databases, Nginx, HTTPS certificates, domains, cloud security group mutation, VPN, service mesh, dynamic service discovery, central gateways, or local dynamic IP support.

## Directory Structure

```text
personal-infra-tools/
  pyproject.toml
  README.md
  .env.example
  config/services.example.yaml
  fastapi_message/
  tests/
  scripts/deploy.sh
  scripts/smoke_test.sh
```

## Install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Configuration

Real service communication config belongs in YAML:

```bash
sudo mkdir -p /opt/personal-infra
sudo cp config/services.example.yaml /opt/personal-infra/services.yaml
export SERVICE_REGISTRY_PATH=/opt/personal-infra/services.yaml
```

Use `services.yaml` for non-secret communication config:

- `base_url`
- `auth`
- `health_path`
- `hello_path`
- `action` names
- HTTP `method`
- API `path`
- `timeout_seconds`
- `retries`

Use `.env` or systemd environment only for secrets and minimal runtime identity:

- `SERVICE_NAME`
- `SERVICE_REGISTRY_PATH`
- `PRIVATE_INFO_DB_TOKEN`
- `API_TOKEN`
- API keys, passwords, secret database URLs

Do not put token values in `services.yaml`. `token_env` is allowed because it is only an environment variable name.

## Security Baseline

v0.1 assumes fixed public IP plus fixed port plus cloud security group/firewall allowlist.

- Service ports must not be open to `0.0.0.0/0`.
- Each service port should allow only known ECS/VPS peer public IPs.
- `private-info-db` must use `auth: "bearer"`.
- HTTP is acceptable for v0.1 only under the fixed peer IP allowlist model.

## Use In A FastAPI Service

```python
from fastapi import FastAPI
from fastapi_message import setup_message_pipeline

app = FastAPI()

setup_message_pipeline(
    app,
    service_name="api_report_agent",
    auth_mode="none",
)
```

This registers:

- `GET /health`
- `GET /pipeline/hello`
- request id middleware
- access log middleware
- `MessageError` JSON handler

For bearer-protected service hello checks:

```python
setup_message_pipeline(app, service_name="private_info_db", auth_mode="bearer")
```

`/health` is never authenticated and has no side effects. `/pipeline/hello` validates bearer auth in bearer mode.

Business routes that need bearer protection can use:

```python
from fastapi import Depends
from fastapi_message import require_bearer_auth

@app.post("/api/v1/ingest/text", dependencies=[Depends(require_bearer_auth)])
def ingest_text(payload: dict):
    return {"status": "queued"}
```

## Call Services

```python
from fastapi_message import send_action, send_file_action

send_action("personal_ai_searcher", "search", {"query": "hello"})
send_action("api_report_agent", "run", {"topic": "market"})
send_action("private_info_db", "ingest_text", {"text": "hello"})

send_file_action(
    "private_info_db",
    "ingest_file",
    "/tmp/file.txt",
    fields={"source": "telegram"},
    idempotency_key="telegram:file:unique:sha256",
)
```

## CLI Troubleshooting

```bash
fastapi-message validate-registry
fastapi-message ping private_info_db
fastapi-message smoke private_info_db
fastapi-message list-actions private_info_db
fastapi-message action personal_ai_searcher search '{"query":"hello"}'
fastapi-message post-json api_report_agent /api/v1/report/run '{"topic":"market"}'
fastapi-message file-action private_info_db ingest_file /tmp/a.txt --field source=telegram --idempotency-key abc
fastapi-message post-file private_info_db /api/v1/ingest/file /tmp/a.txt --field source=telegram --idempotency-key abc
```

## Test

```bash
pytest
scripts/smoke_test.sh
```

`scripts/smoke_test.sh` validates the example registry, imports `fastapi_message`, creates a test FastAPI app, verifies `/health`, verifies bearer rejection, and verifies authenticated `/pipeline/hello`.

## ECS/EC2/VPS Deploy

This package is normally installed into each business service venv. It is not a long-running daemon.

Default package deployment:

```bash
export APP_DIR=/opt/personal-infra-tools
export SERVICE_REGISTRY_PATH=/opt/personal-infra/services.yaml
scripts/deploy.sh
```

`scripts/deploy.sh`:

- enters the project directory
- optionally runs `git pull --ff-only` when `GIT_PULL=1`
- creates `data/` and `logs/`
- creates or reuses a venv
- installs dependencies
- runs tests
- validates the registry
- runs smoke tests
- exits

It does not start foreground services. Long-running business services should be managed by their own systemd units.

Example systemd environment for a business service:

```ini
[Service]
Environment=SERVICE_NAME=api_report_agent
Environment=SERVICE_REGISTRY_PATH=/opt/personal-infra/services.yaml
Environment=PRIVATE_INFO_DB_TOKEN=replace-me
```

Systemd commands:

```bash
sudo systemctl status api-report-agent
sudo systemctl restart api-report-agent
journalctl -u api-report-agent -f
```

## Error Troubleshooting

- `RegistryError`: registry path is missing, YAML is invalid, service is missing, or registry structure is wrong.
- `ActionNotFoundError`: action is not registered under that service.
- `ConfigError`: required token env var is missing.
- `NetworkError`: IP/port is unreachable; check security group, firewall, listen address, and service status.
- `TimeoutError`: target did not respond before timeout.
- `UnauthorizedError`: bearer token is missing or wrong.
- `DecodeError`: target returned non-JSON or non-object JSON for a successful response.
- `UpstreamError`: target returned 500/502/503/504.

## Extension Path

Keep v0.1 simple. Add schema validation, richer auth, service discovery, HTTPS automation, or workflow orchestration only when a real service needs it.
