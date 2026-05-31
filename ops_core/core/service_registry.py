from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops_core.config import get_registry_path, load_yaml


@dataclass(frozen=True)
class ServiceAction:
    action_id: str
    label: str
    method: str
    path: str
    timeout_seconds: float
    safe: bool
    demo_payload: dict | None


@dataclass(frozen=True)
class ServiceDefinition:
    service_id: str
    label: str
    description: str
    base_url: str
    auth_mode: str
    token_env: str | None
    enabled: bool
    actions: dict[str, ServiceAction]

    def public_dict(self) -> dict:
        return {
            "id": self.service_id,
            "label": self.label,
            "description": self.description,
            "enabled": self.enabled,
            "auth": {"mode": self.auth_mode, "token_env": self.token_env},
            "actions": {
                action_id: {
                    "label": action.label,
                    "method": action.method,
                    "path": action.path,
                    "timeout_seconds": action.timeout_seconds,
                    "safe": action.safe,
                }
                for action_id, action in self.actions.items()
            },
        }


class RegistryError(ValueError):
    pass


def load_service_registry(path: str | Path | None = None) -> dict[str, ServiceDefinition]:
    data = load_yaml(path or get_registry_path())
    raw_services = data.get("services")
    if not isinstance(raw_services, dict):
        raise RegistryError("services registry must contain a services mapping")
    return {
        service_id: _parse_service(service_id, raw_service)
        for service_id, raw_service in raw_services.items()
    }


def get_service(service_id: str, registry: dict[str, ServiceDefinition] | None = None) -> ServiceDefinition:
    services = registry or load_service_registry()
    try:
        return services[service_id]
    except KeyError as exc:
        raise RegistryError(f"unknown service: {service_id}") from exc


def get_action(service: ServiceDefinition, action_id: str) -> ServiceAction:
    try:
        return service.actions[action_id]
    except KeyError as exc:
        raise RegistryError(f"unknown action: {service.service_id}.{action_id}") from exc


def enabled_services(registry: dict[str, ServiceDefinition] | None = None) -> list[ServiceDefinition]:
    services = registry or load_service_registry()
    return [service for service in services.values() if service.enabled]


def _parse_service(service_id: str, raw: Any) -> ServiceDefinition:
    if not isinstance(raw, dict):
        raise RegistryError(f"service must be a mapping: {service_id}")
    auth = raw.get("auth") or {}
    actions = raw.get("actions") or {}
    if not isinstance(actions, dict):
        raise RegistryError(f"actions must be a mapping: {service_id}")
    return ServiceDefinition(
        service_id=service_id,
        label=str(raw.get("label", service_id)),
        description=str(raw.get("description", "")),
        base_url=str(raw["base_url"]).rstrip("/"),
        auth_mode=str(auth.get("mode", "none")),
        token_env=auth.get("token_env"),
        enabled=bool(raw.get("enabled", True)),
        actions={action_id: _parse_action(action_id, action) for action_id, action in actions.items()},
    )


def _parse_action(action_id: str, raw: Any) -> ServiceAction:
    if not isinstance(raw, dict):
        raise RegistryError(f"action must be a mapping: {action_id}")
    method = str(raw.get("method", "GET")).upper()
    if method not in {"GET", "POST"}:
        raise RegistryError(f"unsupported method for {action_id}: {method}")
    path = str(raw.get("path", ""))
    if not path.startswith("/"):
        raise RegistryError(f"action path must start with /: {action_id}")
    return ServiceAction(
        action_id=action_id,
        label=str(raw.get("label", action_id)),
        method=method,
        path=path,
        timeout_seconds=float(raw.get("timeout_seconds", 30)),
        safe=bool(raw.get("safe", True)),
        demo_payload=raw.get("demo_payload") if isinstance(raw.get("demo_payload"), dict) else None,
    )
