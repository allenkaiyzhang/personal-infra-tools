from __future__ import annotations

import pytest

from fastapi_message.errors import ConfigError
from fastapi_message.headers import build_headers
from fastapi_message.registry import load_registry


def test_headers_without_auth(registry_file):
    service = load_registry().service("demo")
    headers, request_id = build_headers(service, request_id="rid-1")
    assert request_id == "rid-1"
    assert headers["X-Source-Service"] == "source"
    assert headers["X-Target-Service"] == "demo"
    assert "Authorization" not in headers


def test_headers_with_bearer(registry_file, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PRIVATE_INFO_DB_TOKEN", "secret")
    service = load_registry().service("private_info_db")
    headers, _ = build_headers(service)
    assert headers["Authorization"] == "Bearer secret"


def test_missing_bearer_token_raises_config_error(registry_file, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PRIVATE_INFO_DB_TOKEN", raising=False)
    service = load_registry().service("private_info_db")
    with pytest.raises(ConfigError):
        build_headers(service)
