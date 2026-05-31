from __future__ import annotations

import pytest

from fastapi_message.errors import ActionNotFoundError, RegistryError
from fastapi_message.registry import load_registry


def test_load_registry(registry_file):
    registry = load_registry()
    assert registry.timeout_seconds == 5
    assert registry.retries == 1
    assert registry.service("demo").base_url == "http://demo.local"
    assert registry.action("demo", "echo").path == "/echo"


def test_missing_service_raises(registry_file):
    registry = load_registry()
    with pytest.raises(RegistryError):
        registry.service("missing")


def test_missing_action_raises(registry_file):
    registry = load_registry()
    with pytest.raises(ActionNotFoundError):
        registry.action("demo", "missing")
