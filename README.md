# ops-core

`personal-infra-tools` is now `ops-core`: the central control plane for personal business services.

It is not a generic toolbox anymore. The intended topology is:

```text
Telegram adapter / future UI
  -> ops-core
  -> downstream business services
```

Business services must not call each other directly. All controlled cross-service operations go through `ops-core`.

Initial downstream services:

- `ai_agent`
- `ai_searcher`
- `private_db`

## v0.1 Scope

Implemented:

- `GET /health`
- central service registry in `config/services.example.yaml`
- service list and service detail APIs
- registry-defined service health and demo action execution
- minimal Telegram interaction endpoint returning UI response objects
- minimal service action API for smoke tests
- venv + systemd deployment files
- audit logging for service actions
- tests

Not implemented:

- Web frontend
- Telegram bot
- SSH
- shell execution
- arbitrary URL caller
- arbitrary user payload forwarding
- scheduler or reminders
- AI natural language router
- cross-service orchestration
- business-service-to-business-service communication

## Configuration

`.env` is for secrets only:

```bash
OPS_CORE_TOKEN=
ADMIN_USER_IDS=
OPS_CORE_CONFIG_PATH=
SERVICE_REGISTRY_PATH=
AI_AGENT_TOKEN=
AI_SEARCHER_TOKEN=
PRIVATE_DB_TOKEN=
```

YAML contains non-sensitive config:

- `config/ops-core.example.yaml`: local service bind address, paths, security flags, deploy defaults.
- `config/services.example.yaml`: central registry for `ai_agent`, `ai_searcher`, and `private_db`.

Real token values must never be committed. `token_env` names are allowed in YAML because they are not secrets.

## Local Run

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export OPS_CORE_ALLOW_NO_AUTH=1
uvicorn ops_core.main:app --host 127.0.0.1 --port 8080
```

Health check:

```bash
curl http://127.0.0.1:8080/health
```

Expected:

```json
{"status":"ok","service":"ops-core","role":"control-plane"}
```

## Telegram Adapter Contract

The Telegram adapter, such as a future `schedule-reminder` integration, should normalize Telegram events and forward them to:

```text
POST /api/interactions/telegram
Authorization: Bearer <OPS_CORE_TOKEN>
```

Example `/start` event:

```json
{
  "channel": "telegram",
  "event_type": "command",
  "user": {"id": "123456789", "username": "kevin"},
  "chat": {"id": "123456789", "type": "private"},
  "message": {"id": 1001, "text": "/start"},
  "command": {"name": "start", "args": []}
}
```

`ops-core` returns UI responses:

```json
{
  "ok": true,
  "response": {
    "type": "screen",
    "text": "ops-core\n\nCentral control plane",
    "parse_mode": "HTML",
    "buttons": [],
    "delivery": {"mode": "reply"}
  }
}
```

## Service Registry

`services.yaml` is the central registry. Actions are declared per service. `ops-core` builds URLs only from:

```text
registry base_url + registry action.path
```

The request body for service action API calls may contain only:

```json
{"confirmed": true}
```

No arbitrary user payload forwarding exists in v0.1. Demo payloads come only from registry `demo_payload`.

Unsafe demo actions require confirmation:

- `ai_agent` demo: confirmation required
- `ai_searcher` demo: executes immediately
- `private_db` demo: confirmation required

## Auth

Protected endpoints require:

```text
Authorization: Bearer <OPS_CORE_TOKEN>
```

For local development only, if `OPS_CORE_TOKEN` is missing or empty, set:

```bash
export OPS_CORE_ALLOW_NO_AUTH=1
```

If `ADMIN_USER_IDS` is set, `/api/interactions/telegram` rejects Telegram users whose `user.id` is not listed.

## API

```bash
GET /health
POST /api/interactions/telegram
GET /api/services
GET /api/services/{service_id}
POST /api/services/{service_id}/actions/{action_id}
```

## Test

```bash
python -m compileall .
pytest -q
```

## Deploy With venv + systemd

On the server:

```bash
cd /opt/personal-infra-tools
cp .env.example .env
# edit .env with real secrets
scripts/deploy.sh
```

`scripts/deploy.sh`:

- uses `set -eu`
- creates `.venv` if missing
- upgrades pip
- installs the package
- creates `data/` and `logs/`
- runs `python -m compileall .`
- runs `pytest -q` unless `SKIP_TESTS=1`
- installs `deploy/systemd/ops-core.service`
- runs `systemctl daemon-reload`
- enables and restarts `ops-core`
- runs `scripts/smoke_test.sh`
- prints `systemctl status --no-pager ops-core`
- exits

It does not run uvicorn in the foreground.

## Smoke Test

```bash
scripts/smoke_test.sh
```

The smoke test calls:

- `GET http://127.0.0.1:8080/health`
- if `OPS_CORE_TOKEN` is set, `POST /api/interactions/telegram` with `/start`

It exits non-zero on failure.

## Logs

```bash
scripts/tail_logs.sh
```

This tails `logs/ops-core.log` if it exists, otherwise falls back to:

```bash
journalctl -u ops-core -f
```

## Troubleshooting

- `/health` fails: check `systemctl status ops-core` and `journalctl -u ops-core -f`.
- Protected endpoint returns 401: check `OPS_CORE_TOKEN` and the `Authorization` header.
- Telegram interaction returns 403: check `ADMIN_USER_IDS`.
- Service action fails with missing bearer token: set `AI_AGENT_TOKEN`, `AI_SEARCHER_TOKEN`, or `PRIVATE_DB_TOKEN`.
- Downstream unavailable: verify the service is listening at the registry `base_url` and the firewall allows ops-core.
- No logs file: use `journalctl -u ops-core -f`.
