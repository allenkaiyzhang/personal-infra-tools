from __future__ import annotations

from pathlib import Path

import httpx

from .errors import ActionNotFoundError, NetworkError, TimeoutError
from .headers import build_headers
from .message import decode_response
from .registry import load_registry


FILE_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def send_file_action(
    service_name: str,
    action_name: str,
    file_path: str,
    fields: dict | None = None,
    *,
    idempotency_key: str | None = None,
    request_id: str | None = None,
    timeout_seconds: float | None = None,
) -> dict:
    registry = load_registry()
    service = registry.service(service_name)
    action = registry.action(service_name, action_name)
    if action.type not in {None, "file"}:
        raise ActionNotFoundError(
            f"action is not a file action: {service_name}.{action_name}",
            service_name=service_name,
            action_name=action_name,
        )
    retries = registry.retries if idempotency_key else 0
    return _request_file(
        service_name=service_name,
        action_name=action_name,
        url=f"{service.base_url}{action.path}",
        service=service,
        file_path=file_path,
        fields=fields,
        timeout_seconds=timeout_seconds or registry.timeout_seconds,
        retries=retries,
        idempotency_key=idempotency_key,
        request_id=request_id,
    )


def send_file(
    service_name: str,
    path: str,
    file_path: str,
    fields: dict | None = None,
    *,
    idempotency_key: str | None = None,
    request_id: str | None = None,
    timeout_seconds: float | None = None,
) -> dict:
    registry = load_registry()
    service = registry.service(service_name)
    retries = registry.retries if idempotency_key else 0
    normalized_path = path if path.startswith("/") else f"/{path}"
    return _request_file(
        service_name=service_name,
        action_name=None,
        url=f"{service.base_url}{normalized_path}",
        service=service,
        file_path=file_path,
        fields=fields,
        timeout_seconds=timeout_seconds or registry.timeout_seconds,
        retries=retries,
        idempotency_key=idempotency_key,
        request_id=request_id,
    )


def _request_file(
    *,
    service_name: str,
    action_name: str | None,
    url: str,
    service,
    file_path: str,
    fields: dict | None,
    timeout_seconds: float,
    retries: int,
    idempotency_key: str | None,
    request_id: str | None,
) -> dict:
    path = Path(file_path)
    headers, resolved_request_id = build_headers(
        service, request_id=request_id, idempotency_key=idempotency_key
    )
    attempts = max(1, retries + 1)
    for attempt in range(attempts):
        try:
            with path.open("rb") as file_obj:
                files = {"file": (path.name, file_obj)}
                with httpx.Client(timeout=timeout_seconds) as client:
                    response = client.post(url, data=fields or {}, files=files, headers=headers)
        except httpx.TimeoutException as exc:
            if attempt < attempts - 1:
                continue
            raise TimeoutError(
                "file request timed out",
                service_name=service_name,
                action_name=action_name,
                path=url,
                request_id=resolved_request_id,
            ) from exc
        except httpx.RequestError as exc:
            raise NetworkError(
                "file request failed",
                service_name=service_name,
                action_name=action_name,
                path=url,
                request_id=resolved_request_id,
            ) from exc
        if response.status_code in FILE_RETRYABLE_STATUS_CODES and attempt < attempts - 1:
            continue
        return decode_response(
            response,
            service_name=service_name,
            action_name=action_name,
            path=url,
            request_id=resolved_request_id,
        )
    raise NetworkError("file request failed", service_name=service_name, action_name=action_name, path=url)
