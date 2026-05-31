from __future__ import annotations

from typing import Any

import httpx

from .errors import (
    DecodeError,
    NetworkError,
    RemoteError,
    STATUS_ERROR_MAP,
    TimeoutError,
)
from .headers import build_headers
from .registry import load_registry

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def send_message(
    service_name: str,
    path: str,
    payload: dict | None = None,
    *,
    method: str = "POST",
    idempotency_key: str | None = None,
    request_id: str | None = None,
    timeout_seconds: float | None = None,
) -> dict:
    registry = load_registry()
    service = registry.service(service_name)
    timeout = timeout_seconds or registry.timeout_seconds
    retries = registry.retries
    return _request_json(
        service_name=service_name,
        action_name=None,
        url=f"{service.base_url}{_normalize_path(path)}",
        method=method,
        payload=payload,
        service=service,
        timeout_seconds=timeout,
        retries=retries,
        idempotency_key=idempotency_key,
        request_id=request_id,
    )


def _request_json(
    *,
    service_name: str,
    action_name: str | None,
    url: str,
    method: str,
    payload: dict | None,
    service,
    timeout_seconds: float,
    retries: int,
    idempotency_key: str | None,
    request_id: str | None,
    include_auth: bool = True,
) -> dict:
    data, _meta = _request_json_with_meta(
        service_name=service_name,
        action_name=action_name,
        url=url,
        method=method,
        payload=payload,
        service=service,
        timeout_seconds=timeout_seconds,
        retries=retries,
        idempotency_key=idempotency_key,
        request_id=request_id,
        include_auth=include_auth,
    )
    return data


def _request_json_with_meta(
    *,
    service_name: str,
    action_name: str | None,
    url: str,
    method: str,
    payload: dict | None,
    service,
    timeout_seconds: float,
    retries: int,
    idempotency_key: str | None,
    request_id: str | None,
    include_auth: bool = True,
) -> tuple[dict, dict]:
    headers, resolved_request_id = build_headers(
        service,
        request_id=request_id,
        idempotency_key=idempotency_key,
        include_auth=include_auth,
    )
    attempts = max(1, retries + 1)
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.request(method.upper(), url, json=payload or {}, headers=headers)
        except httpx.TimeoutException as exc:
            last_error = TimeoutError(
                "request timed out",
                service_name=service_name,
                action_name=action_name,
                path=url,
                request_id=resolved_request_id,
            )
            if attempt < attempts - 1:
                continue
            raise last_error from exc
        except httpx.RequestError as exc:
            raise NetworkError(
                "request failed",
                service_name=service_name,
                action_name=action_name,
                path=url,
                request_id=resolved_request_id,
            ) from exc

        if response.status_code in RETRYABLE_STATUS_CODES and attempt < attempts - 1:
            continue
        data = decode_response(
            response,
            service_name=service_name,
            action_name=action_name,
            path=url,
            request_id=resolved_request_id,
        )
        return data, {
            "http_status": response.status_code,
            "request_id": response.headers.get("X-Request-ID") or resolved_request_id,
            "sent_request_id": resolved_request_id,
        }
    if last_error:
        raise last_error
    raise NetworkError("request failed", service_name=service_name, action_name=action_name, path=url)


def decode_response(
    response: httpx.Response,
    *,
    service_name: str,
    action_name: str | None = None,
    path: str | None = None,
    request_id: str | None = None,
) -> dict:
    if 200 <= response.status_code < 300:
        try:
            data = response.json()
        except ValueError as exc:
            raise DecodeError(
                "response is not valid JSON",
                service_name=service_name,
                action_name=action_name,
                path=path,
                status_code=response.status_code,
                request_id=request_id,
            ) from exc
        if not isinstance(data, dict):
            raise DecodeError(
                "response JSON must be an object",
                service_name=service_name,
                action_name=action_name,
                path=path,
                status_code=response.status_code,
                request_id=request_id,
            )
        return data

    error_message, error_code = _extract_remote_error(response)
    exc_type = STATUS_ERROR_MAP.get(response.status_code, RemoteError)
    raise exc_type(
        error_message,
        service_name=service_name,
        action_name=action_name,
        path=path,
        status_code=response.status_code,
        request_id=request_id,
        error_code=error_code,
    )


def _extract_remote_error(response: httpx.Response) -> tuple[str, str | None]:
    try:
        data: Any = response.json()
    except ValueError:
        return f"remote service returned HTTP {response.status_code}", None
    if isinstance(data, dict) and isinstance(data.get("error"), dict):
        error = data["error"]
        return str(error.get("message") or response.reason_phrase), error.get("code")
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"]), None
    return f"remote service returned HTTP {response.status_code}", None


def _normalize_path(path: str) -> str:
    return path if path.startswith("/") else f"/{path}"
