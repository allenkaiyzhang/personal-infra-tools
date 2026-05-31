from __future__ import annotations

from .message import _request_json
from .registry import load_registry


def send_action(
    service_name: str,
    action_name: str,
    payload: dict | None = None,
    *,
    idempotency_key: str | None = None,
    request_id: str | None = None,
    timeout_seconds: float | None = None,
) -> dict:
    registry = load_registry()
    service = registry.service(service_name)
    action = registry.action(service_name, action_name)
    timeout = timeout_seconds or registry.timeout_seconds
    return _request_json(
        service_name=service_name,
        action_name=action_name,
        url=f"{service.base_url}{action.path}",
        method=action.method,
        payload=payload,
        service=service,
        timeout_seconds=timeout,
        retries=registry.retries,
        idempotency_key=idempotency_key,
        request_id=request_id,
    )


def ping(service_name: str) -> dict:
    registry = load_registry()
    service = registry.service(service_name)
    return _request_json(
        service_name=service_name,
        action_name="health",
        url=f"{service.base_url}{service.health_path}",
        method="GET",
        payload=None,
        service=service,
        timeout_seconds=registry.timeout_seconds,
        retries=registry.retries,
        idempotency_key=None,
        request_id=None,
        include_auth=False,
    )
