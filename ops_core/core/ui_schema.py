from __future__ import annotations


def button(label: str, action: str) -> dict:
    return {"label": label, "action": action}


def screen(text: str, buttons: list[list[dict]] | None = None, *, delivery: str = "reply") -> dict:
    return {
        "type": "screen",
        "text": text,
        "parse_mode": "HTML",
        "buttons": buttons or [],
        "delivery": {"mode": delivery},
    }


def ok(response: dict) -> dict:
    return {"ok": True, "response": response}


def error_screen(message: str) -> dict:
    return ok(screen(f"Error\n\n{message}", [[button("Home", "nav:home")]]))
