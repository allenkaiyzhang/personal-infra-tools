from __future__ import annotations

import os
import time
from uuid import uuid4

import httpx

from ops_core.config import load_config
from ops_core.core.service_registry import ServiceAction, ServiceDefinition


def execute_service_action(service: ServiceDefinition, action: ServiceAction) -> dict:
    config = load_config()
    started = time.perf_counter()
    request_id = str(uuid4())
    url = f"{service.base_url}{action.path}"
    headers = {
        "X-Request-ID": request_id,
        "X-Source-Service": "ops-core",
        "X-Target-Service": service.service_id,
        "User-Agent": "ops-core",
    }
    if service.auth_mode == "bearer":
        token = os.getenv(service.token_env or "")
        if not token:
            return _failure("missing bearer token env", 0, started, config.max_output_chars)
        headers["Authorization"] = f"Bearer {token}"

    try:
        with httpx.Client(timeout=action.timeout_seconds) as client:
            if action.method == "GET":
                response = client.get(url, headers=headers)
            elif action.method == "POST":
                response = client.post(url, json=action.demo_payload or {}, headers=headers)
            else:
                return _failure(f"unsupported method: {action.method}", 0, started, config.max_output_chars)
    except httpx.RequestError as exc:
        return _failure(str(exc), 0, started, config.max_output_chars)

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    body = _decode_body(response, config.max_output_chars)
    return {
        "ok": 200 <= response.status_code < 300,
        "status_code": response.status_code,
        "elapsed_ms": elapsed_ms,
        "body": body,
        "request_id": response.headers.get("X-Request-ID") or request_id,
    }


def _decode_body(response: httpx.Response, max_chars: int) -> dict | str:
    try:
        data = response.json()
    except ValueError:
        return _clamp(response.text, max_chars)
    return _clamp_nested(data, max_chars)


def _failure(error: str, status_code: int, started: float, max_chars: int) -> dict:
    return {
        "ok": False,
        "status_code": status_code,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "error": _clamp(error, max_chars),
    }


def _clamp(value: str, max_chars: int) -> str:
    return value if len(value) <= max_chars else value[:max_chars] + "...[truncated]"


def _clamp_nested(value, max_chars: int):
    text = repr(value)
    if len(text) <= max_chars:
        return value
    return _clamp(text, max_chars)
