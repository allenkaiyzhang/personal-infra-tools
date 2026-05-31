from __future__ import annotations

import os

from . import __version__
from .errors import ConfigError
from .registry import ServiceConfig
from .request_id import resolve_request_id


def source_service_name() -> str:
    return os.getenv("SERVICE_NAME", "unknown")


def build_headers(
    service: ServiceConfig,
    *,
    request_id: str | None = None,
    idempotency_key: str | None = None,
    include_auth: bool = True,
) -> tuple[dict[str, str], str]:
    resolved_request_id = resolve_request_id(request_id)
    headers = {
        "X-Request-ID": resolved_request_id,
        "X-Source-Service": source_service_name(),
        "X-Target-Service": service.name,
        "User-Agent": f"personal-infra-tools/fastapi-message/{__version__}",
    }
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key
    if include_auth and service.auth == "bearer":
        token_env = service.token_env or "API_TOKEN"
        token = os.getenv(token_env)
        if not token:
            raise ConfigError(
                f"missing bearer token env var: {token_env}",
                service_name=service.name,
                request_id=resolved_request_id,
            )
        headers["Authorization"] = f"Bearer {token}"
    return headers, resolved_request_id
