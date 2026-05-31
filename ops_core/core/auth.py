from __future__ import annotations

import os

from fastapi import Header, HTTPException, Request

from ops_core.config import admin_user_ids


def require_ops_core_token(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv("OPS_CORE_TOKEN", "")
    if not token and os.getenv("OPS_CORE_ALLOW_NO_AUTH") == "1":
        return
    if not token:
        raise HTTPException(status_code=401, detail="ops-core token is not configured")
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="unauthorized")


def check_admin_user(event: dict) -> None:
    allowed = admin_user_ids()
    if not allowed:
        return
    user_id = str(((event.get("user") or {}).get("id")) or "")
    if user_id not in allowed:
        raise HTTPException(status_code=403, detail="user is not allowed")
