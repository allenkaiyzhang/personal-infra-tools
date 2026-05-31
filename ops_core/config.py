from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class OpsCoreConfig:
    service_name: str
    host: str
    port: int
    health_path: str
    data_dir: Path
    log_dir: Path
    log_file: Path
    require_admin_user: bool
    max_output_chars: int
    install_path: str
    systemd_service: str


DEFAULT_CONFIG_PATH = Path("config/ops-core.example.yaml")
DEFAULT_REGISTRY_PATH = Path("config/services.example.yaml")


def load_yaml(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {resolved}")
    return data


def get_config_path() -> Path:
    return Path(os.getenv("OPS_CORE_CONFIG_PATH") or DEFAULT_CONFIG_PATH)


def get_registry_path() -> Path:
    return Path(os.getenv("SERVICE_REGISTRY_PATH") or DEFAULT_REGISTRY_PATH)


def load_config(path: str | Path | None = None) -> OpsCoreConfig:
    data = load_yaml(path or get_config_path())
    service = data.get("service") or {}
    paths = data.get("paths") or {}
    security = data.get("security") or {}
    deploy = data.get("deploy") or {}

    return OpsCoreConfig(
        service_name=str(service.get("name", "ops-core")),
        host=str(service.get("host", "127.0.0.1")),
        port=int(service.get("port", 8080)),
        health_path=str(service.get("health_path", "/health")),
        data_dir=Path(paths.get("data_dir", "data")),
        log_dir=Path(paths.get("log_dir", "logs")),
        log_file=Path(paths.get("log_file", "logs/ops-core.log")),
        require_admin_user=bool(security.get("require_admin_user", False)),
        max_output_chars=int(security.get("max_output_chars", 4000)),
        install_path=str(deploy.get("install_path", "/opt/personal-infra-tools")),
        systemd_service=str(deploy.get("systemd_service", "ops-core")),
    )


def admin_user_ids() -> set[str]:
    raw = os.getenv("ADMIN_USER_IDS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}
