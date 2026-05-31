from __future__ import annotations

from fastapi import FastAPI

from ops_core.api.routes_health import router as health_router
from ops_core.api.routes_interactions import router as interactions_router
from ops_core.api.routes_services import router as services_router
from ops_core.config import load_config
from ops_core.logging_config import configure_logging

config = load_config()
configure_logging(config)

app = FastAPI(title="ops-core", version="0.1.0")
app.include_router(health_router)
app.include_router(interactions_router)
app.include_router(services_router)
