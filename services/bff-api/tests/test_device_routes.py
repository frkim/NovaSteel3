"""Route-level tests for the wave-6 device site filter and Copilot additions.

These four routes were merged from parked handoff notes, so they carry no
coverage from the adapter suites. The site filter in particular is easy to
regress: the plant-scope check and the `site` query parameter are two distinct
filters and both must survive.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bff_api.config import DemoMode, Settings
from bff_api.main import create_app

ALL_PLANTS = "NS-DEMO-LUX-01,NS-DEMO-BE-01,NS-DEMO-DE-01,NS-DEMO-ES-01"

HEADERS = {
    "X-Demo-User": "test-device-reader",
    "X-Demo-Roles": "Operator.Read",
    "X-Demo-Plants": ALL_PLANTS,
    "X-Demo-Display-Name": "Test Device Reader",
    "X-Demo-Locale": "en",
}


@pytest.fixture()
def client() -> TestClient:
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


def _items(client: TestClient, path: str, headers: dict[str, str]) -> list[dict]:
    response = client.get(path, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["items"]


def test_device_fleet_spans_every_demo_site(client: TestClient) -> None:
    rows = _items(client, "/v1/devices?size=100", HEADERS)

    assert len(rows) == 16
    assert sorted({row["site"] for row in rows}) == [
        "NS-DEMO-BE-01",
        "NS-DEMO-DE-01",
        "NS-DEMO-ES-01",
        "NS-DEMO-LUX-01",
    ]


@pytest.mark.parametrize("site", ["NS-DEMO-LUX-01", "NS-DEMO-BE-01", "NS-DEMO-DE-01"])
def test_device_site_filter_narrows_to_one_site(client: TestClient, site: str) -> None:
    rows = _items(client, f"/v1/devices?site={site}&size=100", HEADERS)

    assert rows, f"expected at least one device for {site}"
    assert {row["site"] for row in rows} == {site}


def test_sensor_site_filter_follows_the_parent_device(client: TestClient) -> None:
    every = _items(client, "/v1/devices/sensors?site=all&size=200", HEADERS)
    lux = _items(client, "/v1/devices/sensors?site=NS-DEMO-LUX-01&size=200", HEADERS)

    assert len(every) == 86
    assert 0 < len(lux) < len(every)
    lux_devices = {
        row["deviceId"]
        for row in _items(client, "/v1/devices?site=NS-DEMO-LUX-01&size=100", HEADERS)
    }
    assert {row["deviceId"] for row in lux} <= lux_devices


def test_plant_scope_still_applies_without_a_site_filter(client: TestClient) -> None:
    scoped = dict(HEADERS, **{"X-Demo-Plants": "NS-DEMO-LUX-01"})

    devices = _items(client, "/v1/devices?size=100", scoped)
    sensors = _items(client, "/v1/devices/sensors?size=200", scoped)

    assert {row["site"] for row in devices} == {"NS-DEMO-LUX-01"}
    assert {row["deviceId"] for row in sensors} <= {row["deviceId"] for row in devices}


def test_glossary_online_fallback_answers(client: TestClient) -> None:
    response = client.get("/v1/copilot/glossary/online?q=tuyere", headers=HEADERS)

    assert response.status_code == 200
    assert "data" in response.json()


def test_delete_all_conversations_returns_no_content(client: TestClient) -> None:
    response = client.delete("/v1/copilot/conversations", headers=HEADERS)

    assert response.status_code == 204
    assert client.get("/v1/copilot/conversations", headers=HEADERS).status_code == 200
