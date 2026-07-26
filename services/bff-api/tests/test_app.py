import pytest
from fastapi.testclient import TestClient

from bff_api.config import ConfigurationError, DemoMode, Settings
from bff_api.main import create_app


def make_client() -> TestClient:
    settings = Settings(
        service_name="test-bff",
        api_version="v1",
        environment="demo",
        demo_mode=DemoMode.LOCAL,
        data_namespace="NS-DEMO-LUX-01",
        cors_origins=("http://localhost:5173",),
        auth_mode="demo",
    )
    return TestClient(create_app(settings))


def test_liveness_returns_a_correlation_id() -> None:
    response = make_client().get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-correlation-id"] == response.json()["correlationId"]


def test_metadata_exposes_demo_safe_context() -> None:
    response = make_client().get("/v1/meta")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "apiVersion": "v1",
        "service": "test-bff",
        "environment": "demo",
        "demoMode": True,
        "authMode": "demo",
        "dataNamespace": "NS-DEMO-LUX-01",
        "bridgeContractVersion": "1.0",
    }


def test_unknown_route_uses_the_error_envelope() -> None:
    response = make_client().get("/v1/not-implemented")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert response.json()["retryable"] is False


def test_cors_is_restricted_to_configured_origin() -> None:
    response = make_client().options(
        "/v1/meta",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": (
                "x-demo-user,x-demo-roles,x-demo-plants,"
                "x-demo-display-name,x-demo-locale"
            ),
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "x-demo-user" in allowed_headers
    assert "x-demo-locale" in allowed_headers


def test_local_demo_rejects_non_demo_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "local")
    monkeypatch.setenv("BFF_DATA_NAMESPACE", "NS-PROD-LUX-01")

    with pytest.raises(ConfigurationError, match="NS-DEMO"):
        Settings.from_environment()
