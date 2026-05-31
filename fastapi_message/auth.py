from __future__ import annotations

import os

from fastapi import Header, HTTPException


def expected_bearer_token(token_env: str | None = None) -> str | None:
    env_name = token_env or "API_TOKEN"
    return os.getenv(env_name) or os.getenv("API_TOKEN")


def verify_bearer_header(authorization: str | None, *, token_env: str | None = None) -> None:
    token = expected_bearer_token(token_env)
    if not token:
        raise HTTPException(status_code=500, detail="server bearer token is not configured")
    expected = f"Bearer {token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


def require_bearer_auth(authorization: str | None = Header(default=None)) -> None:
    verify_bearer_header(authorization)
