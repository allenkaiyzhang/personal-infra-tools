from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .config import OpsCoreConfig


def configure_logging(config: OpsCoreConfig) -> None:
    config.log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(config.log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger("ops_core")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(handler)
