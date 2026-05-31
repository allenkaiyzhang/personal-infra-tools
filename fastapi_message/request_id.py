from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4


_request_id: ContextVar[str | None] = ContextVar("fastapi_message_request_id", default=None)


def new_request_id() -> str:
    return str(uuid4())


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(request_id: str | None):
    return _request_id.set(request_id)


def reset_request_id(token) -> None:
    _request_id.reset(token)


def resolve_request_id(request_id: str | None = None) -> str:
    return request_id or get_request_id() or new_request_id()
