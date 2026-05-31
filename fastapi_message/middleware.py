from __future__ import annotations

import os
import time
from typing import Any

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from . import __version__
from .auth import verify_bearer_header
from .errors import MessageError
from .health import health_payload
from .logging import log_access
from .registry import load_registry
from .request_id import new_request_id, reset_request_id, set_request_id


def setup_message_pipeline(
    app: FastAPI,
    service_name: str | None = None,
    version: str | None = None,
    auth_mode: str | None = None,
) -> None:
    resolved_service_name = service_name or os.getenv("SERVICE_NAME") or "unknown"
    resolved_version = version or __version__
    resolved_auth_mode, token_env = _resolve_auth_mode(resolved_service_name, auth_mode)

    @app.middleware("http")
    async def request_id_and_access_log(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        request.state.request_id = request_id
        token = set_request_id(request_id)
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            client_host = request.client.host if request.client else None
            log_access(
                service_name=resolved_service_name,
                request_id=request_id,
                source_service=request.headers.get("X-Source-Service"),
                target_service=request.headers.get("X-Target-Service"),
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
                client_host=client_host,
            )
            reset_request_id(token)

    @app.exception_handler(MessageError)
    async def message_error_handler(request: Request, exc: MessageError):
        status = exc.status_code or 500
        return JSONResponse(status_code=status, content=exc.to_dict(), headers={"X-Request-ID": exc.request_id or ""})

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return health_payload(resolved_service_name, resolved_version)

    @app.get("/pipeline/hello")
    async def pipeline_hello(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        if resolved_auth_mode == "bearer":
            verify_bearer_header(authorization, token_env=token_env)
        return {
            "status": "ok",
            "service": resolved_service_name,
            "source_service": request.headers.get("X-Source-Service"),
            "request_id": request.state.request_id,
        }


def _resolve_auth_mode(service_name: str, explicit_auth_mode: str | None) -> tuple[str, str | None]:
    if explicit_auth_mode:
        return explicit_auth_mode, None
    try:
        registry = load_registry()
        service = registry.services.get(service_name)
    except Exception:
        service = None
    if service:
        return service.auth, service.token_env
    return "none", None
