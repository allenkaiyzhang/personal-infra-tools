from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


logger = logging.getLogger("fastapi_message")


def log_access(
    *,
    service_name: str,
    request_id: str,
    source_service: str | None,
    target_service: str | None,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client_host: str | None,
) -> None:
    logger.info(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service_name": service_name,
                "request_id": request_id,
                "source_service": source_service,
                "target_service": target_service,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "client_host": client_host,
            },
            ensure_ascii=True,
        )
    )
