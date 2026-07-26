"""Persona-level local demo journeys across the BFF and deterministic workers."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
for source in (
    ROOT / "services" / "bff-api" / "src",
    ROOT / "services" / "optimizer-worker" / "src",
    ROOT / "services" / "scoring-worker" / "src",
    ROOT / "services" / "knowledge-orchestrator" / "src",
):
    sys.path.insert(0, str(source))

from bff_api.main import create_app  # noqa: E402


def _headers(role: str) -> dict[str, str]:
    return {
        "X-Demo-User": f"e2e-{role.split('.')[0].lower()}",
        "X-Demo-Roles": role,
        "X-Demo-Plants": "NS-DEMO-LUX-01",
    }


def test_maintenance_persona_can_turn_a_lining_warning_into_synthetic_work() -> None:
    client = TestClient(create_app())
    headers = _headers("MaintenanceEngineer.Read")

    identity = client.get("/v1/me", headers=headers)
    forecast = client.get("/v1/furnaces/LUX-BF-01/lining-forecast", headers=headers)
    work_order = client.post(
        "/v1/workorders",
        headers=headers | {"Idempotency-Key": str(uuid4())},
        json={
            "assetId": "LUX-BF-01",
            "title": "Inspect the localized warm zone",
            "reason": "The synthetic forecast has a 21-day lining warning.",
        },
    )

    assert identity.status_code == forecast.status_code == 200
    assert identity.json()["data"]["personas"] == ["MaintenanceReliabilityEngineer"]
    assert forecast.json()["data"]["value"] == 21.0
    assert work_order.status_code == 201
    assert work_order.json()["data"]["synthetic"] is True
    assert work_order.json()["data"]["status"] == "PLANNED_INSPECTION"


def test_energy_persona_can_review_a_shadow_recommendation_with_an_audit_record() -> None:
    client = TestClient(create_app())
    headers = _headers("EnergyPlanner.Approve")
    simulation = client.post(
        "/v1/energy/schedules:simulate",
        headers=headers,
        json={
            "site": "NS-DEMO-LUX-01",
            "horizonHours": 24,
            "scenario": "evening-scarcity",
            "constraints": {},
        },
    )
    assert simulation.status_code == 200
    recommendation = simulation.json()["data"]

    approval = client.post(
        f"/v1/energy/recommendations/{recommendation['recommendationId']}:approve",
        headers=headers | {"Idempotency-Key": str(uuid4())},
        json={
            "reason": "Reviewed deterministic constraints in the demo.",
            "approvalContext": {"reviewedConstraints": True},
            "expectedVersion": recommendation["version"],
        },
    )

    assert approval.status_code == 200
    assert approval.json()["data"]["status"] == "SIMULATED_APPROVED"
    assert approval.json()["data"]["approvalAuditRef"]
    assert client.app.state.services.audit.verify()


def test_knowledge_publisher_can_approve_only_a_reviewable_procedure() -> None:
    client = TestClient(create_app())
    headers = _headers("Knowledge.Publisher")
    procedures = client.get("/v1/knowledge/procedures", headers=headers)
    assert procedures.status_code == 200
    in_review = next(
        procedure
        for procedure in procedures.json()["items"]
        if procedure["status"] == "IN_REVIEW"
    )

    approval = client.post(
        f"/v1/knowledge/procedures/{in_review['procedureId']}:approve",
        headers=headers | {"Idempotency-Key": str(uuid4())},
        json={"expectedVersion": in_review["version"]},
    )
    search = client.get("/v1/knowledge/search?q=hearth", headers=headers)

    assert approval.status_code == 200
    assert approval.json()["data"]["status"] == "APPROVED"
    assert all(item["status"] == "APPROVED" for item in search.json()["items"])
