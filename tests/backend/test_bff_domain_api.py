from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient
from bff_api.config import DemoMode, Settings
from bff_api.main import create_app


def test_demo_auth_and_plant_scope_are_enforced(client: TestClient) -> None:
    unauthenticated = client.get("/v1/me")
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["code"] == "INVALID_TOKEN"

    quality_reader = {
        "X-Demo-User": "quality-engineer",
        "X-Demo-Roles": "ProcessEngineer.Contribute",
        "X-Demo-Plants": "NS-DEMO-LUX-01",
    }
    assert client.get("/v1/quality/batches", headers=quality_reader).status_code == 200
    assert client.get(
        "/v1/quality/batches?site=NS-DEMO-DE-01", headers=quality_reader
    ).json()["code"] == "FORBIDDEN_SCOPE"
    assert client.get(
        "/v1/furnaces/LUX-BF-01/lining-forecast", headers=quality_reader
    ).json()["code"] == "FORBIDDEN_ROLE"


def test_non_demo_mode_fails_closed_without_a_jwt_validation_adapter() -> None:
    settings = Settings(
        service_name="cloud-boundary-test",
        api_version="v1",
        environment="dev",
        demo_mode=DemoMode.OFF,
        data_namespace="NS-DEV-LUX-01",
        cors_origins=("http://localhost:5173",),
        auth_mode="entra",
        capacity_mode="arm",
    )
    client = TestClient(create_app(settings))

    response = client.get("/v1/me", headers={"Authorization": "Bearer unverified"})
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


def test_tbl_std_filters_global_search_sort_and_pagination(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.get(
        "/v1/quality/batches?grade=NS-AUTO-DP780&q=coil&"
        "resultStatus=PASS&resultStatus=FAIL&sort=riskScore:desc&page=1&size=3",
        headers=admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 3
    assert payload["size"] == 3
    assert all(row["grade"] == "NS-AUTO-DP780" for row in payload["items"])
    assert payload["items"] == sorted(
        payload["items"], key=lambda item: item["riskScore"], reverse=True
    )

    invalid_sort = client.get(
        "/v1/quality/batches?sort=unknown:asc", headers=admin_headers
    )
    assert invalid_sort.status_code == 400
    assert invalid_sort.json()["code"] == "VALIDATION_ERROR"

    numeric_range = client.get(
        "/v1/quality/batches?riskScore:0.7..1.0", headers=admin_headers
    )
    assert numeric_range.status_code == 200
    assert all(item["riskScore"] >= 0.7 for item in numeric_range.json()["items"])


def test_scoring_and_quality_what_if_match_demo_cues(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    forecast = client.get(
        "/v1/furnaces/LUX-BF-01/lining-forecast", headers=admin_headers
    )
    assert forecast.status_code == 200
    value = forecast.json()["data"]
    assert 15.0 <= value["value"] <= 25.0, "RUL from physics regression"
    assert value["confidence"]["p10"] < value["confidence"]["p50"] < value["confidence"]["p90"]
    assert value["riskLevel"] == "HIGH"
    assert len(value["drivers"]) >= 3

    what_if = client.post(
        "/v1/quality/what-if",
        headers=admin_headers,
        json={
            "batchId": "COIL-LUX-260725-017",
            "adjustments": {"coilingTempDeltaC": -8},
        },
    )
    assert what_if.status_code == 200
    proposed = what_if.json()["data"]
    assert proposed["current"]["predictedFirstPassYieldPct"] == 88.0
    assert proposed["proposed"]["predictedFirstPassYieldPct"] == 95.0
    assert proposed["proposed"]["operationalWrite"] is False


def test_energy_recommendation_is_constrained_auditable_and_idempotent(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    simulation = client.post(
        "/v1/energy/schedules:simulate",
        headers=admin_headers,
        json={
            "site": "NS-DEMO-LUX-01",
            "horizonHours": 24,
            "scenario": "evening-scarcity",
            "constraints": {},
        },
    )
    assert simulation.status_code == 200
    recommendation = simulation.json()["data"]
    # Cost savings: MILP multi-objective (CO₂ + cost) produces genuine ~7% cost savings.
    assert 5 <= recommendation["savings"]["costPct"] <= 12
    # Peak: genuine dispatch-attributable change (old test asserted the [3,7%] fake clamp).
    assert recommendation["savings"]["peakPct"] < 0
    # CO₂: physics-derived from per-slot carbon intensity — no longer a constant multiplier.
    assert recommendation["savings"]["co2Pct"] > 0
    assert recommendation["solver"] in ("MILP_CBC", "DETERMINISTIC_HEURISTIC")
    assert recommendation["baseline"]["tonnage"] == recommendation["optimized"]["tonnage"]
    assert recommendation["hardConstraintViolations"] == 0
    assert all(
        item["status"] == "SATISFIED" for item in recommendation["constraintReport"]
    )

    approval = {
        "reason": "Reviewed synthetic constraints",
        "approvalContext": {"reviewedConstraints": True},
        "expectedVersion": 1,
    }
    idempotency_key = str(uuid4())
    endpoint = f"/v1/energy/recommendations/{recommendation['recommendationId']}:approve"
    first = client.post(
        endpoint,
        headers=admin_headers | {"Idempotency-Key": idempotency_key},
        json=approval,
    )
    replay = client.post(
        endpoint,
        headers=admin_headers | {"Idempotency-Key": idempotency_key},
        json=approval,
    )
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert replay.headers["x-correlation-id"] == replay.json()["correlationId"]
    assert first.json()["data"]["status"] == "SIMULATED_APPROVED"

    conflict = client.post(
        endpoint,
        headers=admin_headers | {"Idempotency-Key": idempotency_key},
        json=approval | {"reason": "A different reason"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"


def test_alert_poll_workorder_capacity_and_knowledge_workflows(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    initial_events = client.get("/v1/realtime/alerts:poll", headers=admin_headers)
    assert initial_events.status_code == 200
    last_id = initial_events.json()["events"][-1]["id"]

    work_order = client.post(
        "/v1/workorders",
        headers=admin_headers | {"Idempotency-Key": str(uuid4())},
        json={
            "assetId": "LUX-BF-01",
            "title": "Inspect localized warm zone",
            "reason": "Predicted 21-day lining risk",
        },
    )
    assert work_order.status_code == 201
    assert work_order.json()["data"]["workOrderId"] == "WO-DEMO-LUX-1042"
    updated_events = client.get(
        f"/v1/realtime/alerts:poll?since={last_id}", headers=admin_headers
    ).json()
    assert any(event["type"] == "alert.updated" for event in updated_events["events"])
    assert updated_events["stale"] is False

    start = client.post(
        "/v1/platform/capacity/start-requests",
        headers=admin_headers | {"Idempotency-Key": str(uuid4())},
        json={"capacityId": "cap-novasteel-demo-sc", "reason": "Rehearsal"},
    )
    assert start.status_code == 200
    assert start.json()["data"]["status"] == "SIMULATED"
    operation_id = start.json()["data"]["operationId"]
    operation = client.get(
        f"/v1/platform/capacity/operations/{operation_id}", headers=admin_headers
    )
    assert operation.json()["data"]["state"] == "Running"

    procedures = client.get("/v1/knowledge/procedures", headers=admin_headers).json()
    in_review = next(
        item for item in procedures["items"] if item["status"] == "IN_REVIEW"
    )
    approved = client.post(
        f"/v1/knowledge/procedures/{in_review['procedureId']}:approve",
        headers=admin_headers | {"Idempotency-Key": str(uuid4())},
        json={"expectedVersion": in_review["version"]},
    )
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "APPROVED"
    search = client.get("/v1/knowledge/search?q=hearth", headers=admin_headers)
    assert all(item["status"] == "APPROVED" for item in search.json()["items"])
    assert client.app.state.services.audit.verify()


def test_sse_replay_frames_use_event_ids(client: TestClient, admin_headers: dict[str, str]) -> None:
    assert client.get("/v1/realtime/alerts:poll", headers=admin_headers).status_code == 200

    async def first_frame() -> str:
        stream = client.app.state.services.events.stream(None)
        try:
            return await anext(stream)
        finally:
            await stream.aclose()

    frame = asyncio.run(first_frame())
    assert frame.startswith("id: ")
    assert "event: alert.created" in frame


_SKU_ENDPOINT = "/v1/platform/capacity/sku-requests"
_ALLOWED_CAPACITY = "cap-novasteel-demo-sc"


def test_capacity_sku_change_happy_path(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(
        _SKU_ENDPOINT,
        headers=admin_headers | {"Idempotency-Key": str(uuid4())},
        json={"capacityId": _ALLOWED_CAPACITY, "sku": "F4", "reason": "Cost optimisation"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "SIMULATED"
    assert data["sku"] == "F4"
    assert data["previousSku"] == "F2"
    assert data["state"] == "Paused"  # scale does not change lifecycle state
    assert "operationId" in data
    assert "auditRef" in data
    assert data["capacityId"] == _ALLOWED_CAPACITY


def test_capacity_sku_change_invalid_sku(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(
        _SKU_ENDPOINT,
        headers=admin_headers | {"Idempotency-Key": str(uuid4())},
        json={"capacityId": _ALLOWED_CAPACITY, "sku": "F999", "reason": "Test"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "F2" in response.json()["message"]
    assert "F4" in response.json()["message"]
    assert "F8" in response.json()["message"]


def test_capacity_sku_change_non_allowlisted_capacity(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(
        _SKU_ENDPOINT,
        headers=admin_headers | {"Idempotency-Key": str(uuid4())},
        json={"capacityId": "cap-unknown-xyz", "sku": "F4", "reason": "Test"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "POLICY_DENIED"


def test_capacity_sku_change_same_sku_is_conflict(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    # Default SKU is F2; requesting F2 again is a conflict
    response = client.post(
        _SKU_ENDPOINT,
        headers=admin_headers | {"Idempotency-Key": str(uuid4())},
        json={"capacityId": _ALLOWED_CAPACITY, "sku": "F2", "reason": "No-op test"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "CAPACITY_STATE_CONFLICT"


def test_capacity_sku_change_idempotent_replay(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    key = str(uuid4())
    body = {"capacityId": _ALLOWED_CAPACITY, "sku": "F8", "reason": "Scale up"}
    first = client.post(_SKU_ENDPOINT, headers=admin_headers | {"Idempotency-Key": key}, json=body)
    second = client.post(_SKU_ENDPOINT, headers=admin_headers | {"Idempotency-Key": key}, json=body)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


def test_capacity_sku_change_missing_idempotency_key(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(
        _SKU_ENDPOINT,
        headers=admin_headers,  # no Idempotency-Key
        json={"capacityId": _ALLOWED_CAPACITY, "sku": "F4", "reason": "Test"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "IDEMPOTENCY_KEY_REQUIRED"
