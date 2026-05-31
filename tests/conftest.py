from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture
def registry_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "services.yaml"
    path.write_text(
        """
version: 1
defaults:
  timeout_seconds: 5
  retries: 1
services:
  demo:
    base_url: "http://demo.local"
    auth: "none"
    health_path: "/health"
    hello_path: "/pipeline/hello"
    actions:
      echo:
        method: "POST"
        path: "/echo"
      text:
        method: "GET"
        path: "/text"
      upload:
        method: "POST"
        path: "/upload"
        type: "file"
  private_info_db:
    base_url: "http://private.local"
    auth: "bearer"
    token_env: "PRIVATE_INFO_DB_TOKEN"
    health_path: "/health"
    hello_path: "/pipeline/hello"
    actions:
      ingest_text:
        method: "POST"
        path: "/ingest/text"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("SERVICE_REGISTRY_PATH", str(path))
    monkeypatch.setenv("SERVICE_NAME", "source")
    return path
