from __future__ import annotations

from ops_core.core.ui_schema import button, screen


def home_screen(*, help_text: bool = False) -> dict:
    text = "ops-core\n\nCentral control plane"
    if help_text:
        text += "\n\nUse the buttons to inspect services, run health checks, and execute safe demos."
    return screen(
        text,
        [
            [
                button("AI Agent", "services:view:ai_agent"),
                button("AI Searcher", "services:view:ai_searcher"),
            ],
            [
                button("Private DB", "services:view:private_db"),
                button("System", "system:status"),
            ],
        ],
    )
