from __future__ import annotations

from ops_core.core.service_registry import ServiceDefinition
from ops_core.core.ui_schema import button, screen


def services_list_screen(services: list[ServiceDefinition]) -> dict:
    rows = [[button(service.label, f"services:view:{service.service_id}")] for service in services]
    rows.append([button("Home", "nav:home")])
    labels = "\n".join(f"- {service.label}" for service in services)
    return screen(f"Services\n\n{labels}", rows)


def service_detail_screen(service: ServiceDefinition) -> dict:
    actions = "\n".join(f"- {action.label} ({action.action_id})" for action in service.actions.values())
    return screen(
        f"{service.label}\n\n{service.description}\n\nEnabled: {service.enabled}\n\nActions:\n{actions}",
        [
            [
                button("Health", f"services:health:{service.service_id}"),
                button("Demo", f"services:demo:{service.service_id}"),
            ],
            [button("Home", "nav:home")],
        ],
    )


def confirmation_screen(service: ServiceDefinition) -> dict:
    return screen(
        f"Confirm demo\n\n{service.label} demo is marked unsafe. Confirm to execute the registry-defined demo payload.",
        [
            [button("Confirm", f"services:confirm_demo:{service.service_id}")],
            [button("Home", "nav:home")],
        ],
    )


def action_result_screen(service: ServiceDefinition, action_id: str, result: dict) -> dict:
    if result.get("ok"):
        title = "Action result"
    else:
        title = "Action failed"
    body = result.get("body", result.get("error"))
    return screen(
        (
            f"{title}\n\n"
            f"Service: {service.label}\n"
            f"Action: {action_id}\n"
            f"HTTP status: {result.get('status_code')}\n"
            f"Latency: {result.get('elapsed_ms')} ms\n\n"
            f"{body}"
        ),
        [[button("Back", f"services:view:{service.service_id}"), button("Home", "nav:home")]],
    )
