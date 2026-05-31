from __future__ import annotations

from ops_core.config import load_config
from ops_core.core.audit import write_audit
from ops_core.core.service_client import execute_service_action
from ops_core.core.service_registry import (
    RegistryError,
    enabled_services,
    get_action,
    get_service,
    load_service_registry,
)
from ops_core.core.ui_schema import error_screen, ok, screen
from ops_core.modules.home import home_screen
from ops_core.modules.services import (
    action_result_screen,
    confirmation_screen,
    service_detail_screen,
    services_list_screen,
)


def route_interaction(event: dict) -> dict:
    action = _event_action(event)
    user_id = str(((event.get("user") or {}).get("id")) or "") or None

    if action in {"/start", "nav:home"}:
        return ok(home_screen())
    if action == "/help":
        return ok(home_screen(help_text=True))
    if action == "services:list":
        return ok(services_list_screen(enabled_services()))
    if action == "system:status":
        config = load_config()
        return ok(screen(f"System\n\nservice=ops-core\nmax_output_chars={config.max_output_chars}", [[{"label": "Home", "action": "nav:home"}]]))

    parts = action.split(":")
    if len(parts) == 3 and parts[0] == "services":
        command, service_id = parts[1], parts[2]
        try:
            service = get_service(service_id)
        except RegistryError:
            return error_screen(f"Unknown service: {service_id}")
        if not service.enabled:
            return error_screen(f"Service is disabled: {service_id}")
        if command == "view":
            return ok(service_detail_screen(service))
        if command == "health":
            return _execute_and_render(service, "health", user_id)
        if command == "demo":
            action_cfg = get_action(service, "demo")
            if not action_cfg.safe:
                return ok(confirmation_screen(service))
            return _execute_and_render(service, "demo", user_id)
        if command == "confirm_demo":
            return _execute_and_render(service, "demo", user_id)

    return error_screen(f"Unknown action: {action}")


def _execute_and_render(service, action_id: str, user_id: str | None) -> dict:
    try:
        action = get_action(service, action_id)
    except RegistryError:
        return error_screen(f"Unknown action: {service.service_id}.{action_id}")
    result = execute_service_action(service, action)
    write_audit(
        user_id=user_id,
        service_id=service.service_id,
        action_id=action_id,
        success=bool(result.get("ok")),
        elapsed_ms=float(result.get("elapsed_ms") or 0),
        error=result.get("error"),
    )
    return ok(action_result_screen(service, action_id, result))


def _event_action(event: dict) -> str:
    if event.get("event_type") == "command":
        command = (event.get("command") or {}).get("name")
        return f"/{command}" if command else "/start"
    if event.get("event_type") == "callback":
        return str((event.get("callback") or {}).get("action") or "")
    return ""
