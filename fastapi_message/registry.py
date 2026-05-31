from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError, RegistryError


DEFAULT_REGISTRY_PATH = "/opt/personal-infra/services.yaml"
VALID_AUTH = {"none", "bearer"}
VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


@dataclass(frozen=True)
class ActionConfig:
    name: str
    method: str
    path: str
    type: str | None = None


@dataclass(frozen=True)
class ServiceConfig:
    name: str
    base_url: str
    auth: str
    token_env: str | None
    health_path: str
    hello_path: str
    actions: dict[str, ActionConfig]


@dataclass(frozen=True)
class Registry:
    version: int
    timeout_seconds: float
    retries: int
    services: dict[str, ServiceConfig]
    path: Path

    def service(self, service_name: str) -> ServiceConfig:
        try:
            return self.services[service_name]
        except KeyError as exc:
            raise RegistryError(f"service not found: {service_name}", service_name=service_name) from exc

    def action(self, service_name: str, action_name: str) -> ActionConfig:
        service = self.service(service_name)
        try:
            return service.actions[action_name]
        except KeyError as exc:
            from .errors import ActionNotFoundError

            raise ActionNotFoundError(
                f"action not found: {service_name}.{action_name}",
                service_name=service_name,
                action_name=action_name,
            ) from exc


def registry_path(path: str | None = None) -> Path:
    configured = path or os.getenv("SERVICE_REGISTRY_PATH") or DEFAULT_REGISTRY_PATH
    if not configured:
        raise ConfigError("SERVICE_REGISTRY_PATH is empty")
    return Path(configured)


def load_registry(path: str | None = None) -> Registry:
    resolved = registry_path(path)
    if not resolved.exists():
        raise RegistryError(f"registry file not found: {resolved}")
    try:
        data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RegistryError(f"registry yaml is invalid: {resolved}") from exc
    except OSError as exc:
        raise RegistryError(f"cannot read registry file: {resolved}") from exc
    return parse_registry(data, resolved)


def parse_registry(data: Any, path: Path | None = None) -> Registry:
    path = path or Path("<memory>")
    if not isinstance(data, dict):
        raise RegistryError("registry root must be a mapping")
    if data.get("version") != 1:
        raise RegistryError("registry version must be 1")

    defaults = data.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise RegistryError("registry defaults must be a mapping")
    timeout_seconds = float(defaults.get("timeout_seconds", 30))
    retries = int(defaults.get("retries", 1))
    if timeout_seconds <= 0:
        raise RegistryError("defaults.timeout_seconds must be positive")
    if retries < 0:
        raise RegistryError("defaults.retries must be zero or positive")

    raw_services = data.get("services")
    if not isinstance(raw_services, dict) or not raw_services:
        raise RegistryError("registry services must be a non-empty mapping")

    services: dict[str, ServiceConfig] = {}
    for service_name, raw_service in raw_services.items():
        services[service_name] = _parse_service(service_name, raw_service)

    return Registry(
        version=1,
        timeout_seconds=timeout_seconds,
        retries=retries,
        services=services,
        path=path,
    )


def _parse_service(service_name: str, raw_service: Any) -> ServiceConfig:
    if not isinstance(raw_service, dict):
        raise RegistryError(f"service {service_name} must be a mapping", service_name=service_name)
    base_url = raw_service.get("base_url")
    if not isinstance(base_url, str) or not base_url:
        raise RegistryError(f"service {service_name} base_url is required", service_name=service_name)

    auth = raw_service.get("auth", "none")
    if auth not in VALID_AUTH:
        raise RegistryError(f"service {service_name} auth must be none or bearer", service_name=service_name)
    token_env = raw_service.get("token_env")
    if token_env is not None and not isinstance(token_env, str):
        raise RegistryError(f"service {service_name} token_env must be a string", service_name=service_name)

    raw_actions = raw_service.get("actions") or {}
    if not isinstance(raw_actions, dict):
        raise RegistryError(f"service {service_name} actions must be a mapping", service_name=service_name)

    actions = {
        action_name: _parse_action(service_name, action_name, raw_action)
        for action_name, raw_action in raw_actions.items()
    }
    return ServiceConfig(
        name=service_name,
        base_url=base_url.rstrip("/"),
        auth=auth,
        token_env=token_env,
        health_path=_normalize_path(raw_service.get("health_path", "/health")),
        hello_path=_normalize_path(raw_service.get("hello_path", "/pipeline/hello")),
        actions=actions,
    )


def _parse_action(service_name: str, action_name: str, raw_action: Any) -> ActionConfig:
    if not isinstance(raw_action, dict):
        raise RegistryError(f"action {service_name}.{action_name} must be a mapping")
    method = str(raw_action.get("method", "POST")).upper()
    if method not in VALID_METHODS:
        raise RegistryError(f"action {service_name}.{action_name} method is invalid")
    path = raw_action.get("path")
    if not isinstance(path, str) or not path:
        raise RegistryError(f"action {service_name}.{action_name} path is required")
    action_type = raw_action.get("type")
    if action_type is not None and action_type not in {"json", "file"}:
        raise RegistryError(f"action {service_name}.{action_name} type is invalid")
    return ActionConfig(name=action_name, method=method, path=_normalize_path(path), type=action_type)


def _normalize_path(path: str) -> str:
    return path if path.startswith("/") else f"/{path}"


def validate_registry(path: str | None = None, *, check_token_env: bool = False) -> Registry:
    registry = load_registry(path)
    if check_token_env:
        for service in registry.services.values():
            if service.auth == "bearer" and service.token_env and service.token_env not in os.environ:
                raise ConfigError(
                    f"token env var is not set for bearer service: {service.token_env}",
                    service_name=service.name,
                )
    return registry
