from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_message import setup_message_pipeline


def test_setup_pipeline_health_without_auth(registry_file):
    app = FastAPI()
    setup_message_pipeline(app, service_name="demo", version="test", auth_mode="bearer")
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "demo", "version": "test"}


def test_pipeline_hello_requires_bearer(registry_file, monkeypatch):
    monkeypatch.setenv("API_TOKEN", "secret")
    app = FastAPI()
    setup_message_pipeline(app, service_name="demo", version="test", auth_mode="bearer")
    client = TestClient(app)
    assert client.get("/pipeline/hello").status_code == 401
    response = client.get(
        "/pipeline/hello",
        headers={"Authorization": "Bearer secret", "X-Source-Service": "tester", "X-Request-ID": "rid"},
    )
    assert response.status_code == 200
    assert response.json()["source_service"] == "tester"
    assert response.headers["X-Request-ID"] == "rid"


def test_pipeline_hello_returns_generated_request_id(registry_file, monkeypatch):
    monkeypatch.setenv("API_TOKEN", "secret")
    app = FastAPI()
    setup_message_pipeline(app, service_name="demo", version="test", auth_mode="bearer")
    client = TestClient(app)
    response = client.get("/pipeline/hello", headers={"Authorization": "Bearer secret"})
    assert response.status_code == 200
    assert response.json()["request_id"]
    assert response.headers["X-Request-ID"] == response.json()["request_id"]
