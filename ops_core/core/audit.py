from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


logger = logging.getLogger("ops_core.audit")


def write_audit(
    *,
    user_id: str | None,
    service_id: str,
    action_id: str,
    success: bool,
    elapsed_ms: float,
    error: str | None = None,
) -> None:
    logger.info(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "service_id": service_id,
                "action_id": action_id,
                "success": success,
                "elapsed_ms": elapsed_ms,
                "error": error,
            },
            ensure_ascii=True,
        )
    )
