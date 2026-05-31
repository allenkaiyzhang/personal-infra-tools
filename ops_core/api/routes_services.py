from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ops_core.core.auth import require_ops_core_token
from ops_core.core.audit import write_audit
from ops_core.core.service_client import execute_service_action
from ops_core.core.service_registry import (
    RegistryError,
    enabled_services,
    get_action,
    get_service,
)

router = APIRouter(prefix="/api/services", tags=["services"], dependencies=[Depends(require_ops_core_token)])


@router.get("")
def list_services() -> dict:
    return {"services": [service.public_dict() for service in enabled_services()]}


@router.get("/{service_id}")
def service_detail(service_id: str) -> dict:
    try:
        service = get_service(service_id)
    except RegistryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not service.enabled:
        raise HTTPException(status_code=404, detail="service is disabled")
    return {"service": service.public_dict()}


@router.post("/{service_id}/actions/{action_id}")
def execute_action(service_id: str, action_id: str, body: dict | None = None) -> dict:
    body = body or {}
    if set(body) - {"confirmed"}:
        raise HTTPException(status_code=400, detail="request body may contain only confirmed")
    try:
        service = get_service(service_id)
        action = get_action(service, action_id)
    except RegistryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not service.enabled:
        raise HTTPException(status_code=404, detail="service is disabled")
    if action_id == "demo" and not action.safe and body.get("confirmed") is not True:
        raise HTTPException(status_code=409, detail="confirmation required")
    result = execute_service_action(service, action)
    write_audit(
        user_id=None,
        service_id=service.service_id,
        action_id=action_id,
        success=bool(result.get("ok")),
        elapsed_ms=float(result.get("elapsed_ms") or 0),
        error=result.get("error"),
    )
    return {"ok": result.get("ok"), "result": result}
