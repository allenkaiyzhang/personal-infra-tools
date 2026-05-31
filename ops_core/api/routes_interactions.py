from __future__ import annotations

from fastapi import APIRouter, Depends

from ops_core.core.auth import check_admin_user, require_ops_core_token
from ops_core.core.interaction_router import route_interaction

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.post("/telegram", dependencies=[Depends(require_ops_core_token)])
def telegram_interaction(event: dict) -> dict:
    check_admin_user(event)
    return route_interaction(event)
