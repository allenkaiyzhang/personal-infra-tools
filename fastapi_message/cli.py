from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .actions import ping, send_action
from .files import send_file, send_file_action
from .message import send_message
from .registry import load_registry, validate_registry

app = typer.Typer(help="Registry-driven FastAPI message helpers.")


@app.command("validate-registry")
def validate_registry_command(check_token_env: bool = False) -> None:
    registry = validate_registry(check_token_env=check_token_env)
    typer.echo(f"OK registry={registry.path} services={len(registry.services)}")


@app.command("ping")
def ping_command(service_name: str) -> None:
    result = ping(service_name)
    typer.echo(json.dumps({"service": service_name, "status": result.get("status"), "response": result}, indent=2))


@app.command("smoke")
def smoke_command(service_name: str) -> None:
    registry = load_registry()
    service = registry.service(service_name)
    health = send_message(service_name, service.health_path, method="GET")
    hello = send_message(service_name, service.hello_path, method="GET")
    typer.echo(json.dumps({"service": service_name, "health": health, "hello": hello}, indent=2))


@app.command("action")
def action_command(service_name: str, action_name: str, payload_json: str = "{}") -> None:
    payload = _load_json(payload_json)
    typer.echo(json.dumps(send_action(service_name, action_name, payload), indent=2))


@app.command("file-action")
def file_action_command(
    service_name: str,
    action_name: str,
    file_path: Path,
    field: Annotated[list[str] | None, typer.Option("--field")] = None,
    idempotency_key: str | None = None,
) -> None:
    typer.echo(
        json.dumps(
            send_file_action(
                service_name,
                action_name,
                str(file_path),
                fields=_parse_fields(field),
                idempotency_key=idempotency_key,
            ),
            indent=2,
        )
    )


@app.command("post-json")
def post_json_command(service_name: str, path: str, payload_json: str = "{}") -> None:
    typer.echo(json.dumps(send_message(service_name, path, _load_json(payload_json)), indent=2))


@app.command("post-file")
def post_file_command(
    service_name: str,
    path: str,
    file_path: Path,
    field: Annotated[list[str] | None, typer.Option("--field")] = None,
    idempotency_key: str | None = None,
) -> None:
    typer.echo(
        json.dumps(
            send_file(service_name, path, str(file_path), fields=_parse_fields(field), idempotency_key=idempotency_key),
            indent=2,
        )
    )


@app.command("list-actions")
def list_actions_command(service_name: str) -> None:
    registry = load_registry()
    service = registry.service(service_name)
    for action in service.actions.values():
        typer.echo(f"{action.name}\t{action.method}\t{action.path}\t{action.type or 'json'}")


def _load_json(payload_json: str) -> dict:
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter("payload must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise typer.BadParameter("payload must be a JSON object")
    return payload


def _parse_fields(fields: list[str] | None) -> dict:
    parsed = {}
    for item in fields or []:
        if "=" not in item:
            raise typer.BadParameter("--field must use key=value")
        key, value = item.split("=", 1)
        parsed[key] = value
    return parsed
