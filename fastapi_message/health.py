from __future__ import annotations


def health_payload(service_name: str, version: str | None) -> dict:
    return {
        "status": "ok",
        "service": service_name,
        "version": version,
    }
