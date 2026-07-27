"""Tests for the knowledge procedure lifecycle: transitions, consent, audit."""

import uuid

import pytest
from fastapi.testclient import TestClient

from bff_api.config import DemoMode, Settings
from bff_api.main import create_app


PUBLISHER_HEADERS = {
    "X-Demo-User": "test-reviewer",
    "X-Demo-Roles": "Knowledge.Publisher",
    "X-Demo-Plants": "NS-DEMO-LUX-01",
    "X-Demo-Display-Name": "Test Reviewer",
    "X-Demo-Locale": "en",
}

READER_HEADERS = {
    "X-Demo-User": "test-reader",
    "X-Demo-Roles": "Operator.Read",
    "X-Demo-Plants": "NS-DEMO-LUX-01",
    "X-Demo-Display-Name": "Test Reader",
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


def _create_interview(client: TestClient) -> dict:
    """Helper: create an interview with consent and get back session+draft."""
    body = {
        "operatorRef": "OP-TEST-001",
        "language": "en",
        "consent": {
            "granted": True,
            "scope": "knowledge-capture",
            "retentionDays": 30,
        },
    }
    response = client.post(
        "/v1/knowledge/interviews",
        json=body,
        headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 201, f"Create failed: {response.json()}"
    return response.json()["data"]


class TestConsentRequired:
    def test_consent_denied_rejects(self, client: TestClient) -> None:
        body = {
            "operatorRef": "OP-TEST-002",
            "language": "en",
            "consent": {
                "granted": False,
                "scope": "knowledge-capture",
                "retentionDays": 30,
            },
        }
        response = client.post(
            "/v1/knowledge/interviews",
            json=body,
            headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 400
        assert "consent" in response.json()["message"].lower()

    def test_consent_wrong_scope_rejects(self, client: TestClient) -> None:
        body = {
            "operatorRef": "OP-TEST-002",
            "language": "en",
            "consent": {
                "granted": True,
                "scope": "surveillance",
                "retentionDays": 30,
            },
        }
        response = client.post(
            "/v1/knowledge/interviews",
            json=body,
            headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 400

    def test_consent_missing_retention_rejects(self, client: TestClient) -> None:
        body = {
            "operatorRef": "OP-TEST-002",
            "language": "en",
            "consent": {
                "granted": True,
                "scope": "knowledge-capture",
            },
        }
        response = client.post(
            "/v1/knowledge/interviews",
            json=body,
            headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 400


class TestLegalTransitions:
    def test_draft_to_in_review(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        response = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:submit",
            headers=PUBLISHER_HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "IN_REVIEW"

    def test_in_review_to_approved(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        client.post(
            f"/v1/knowledge/procedures/{procedure_id}:submit",
            headers=PUBLISHER_HEADERS,
        )
        response = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:approve",
            json={"expectedVersion": 1},
            headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "APPROVED"

    def test_in_review_to_rejected(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        client.post(
            f"/v1/knowledge/procedures/{procedure_id}:submit",
            headers=PUBLISHER_HEADERS,
        )
        response = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:reject",
            json={"reason": "Insufficient detail on safety checks"},
            headers=PUBLISHER_HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "REJECTED"

    def test_draft_to_rejected(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        response = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:reject",
            json={"reason": "Duplicate of existing procedure"},
            headers=PUBLISHER_HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "REJECTED"


class TestIllegalTransitions:
    def test_approved_cannot_be_submitted(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        client.post(f"/v1/knowledge/procedures/{procedure_id}:submit", headers=PUBLISHER_HEADERS)
        client.post(
            f"/v1/knowledge/procedures/{procedure_id}:approve",
            json={"expectedVersion": 1},
            headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        response = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:submit",
            headers=PUBLISHER_HEADERS,
        )
        assert response.status_code == 403

    def test_approved_cannot_be_rejected(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        client.post(f"/v1/knowledge/procedures/{procedure_id}:submit", headers=PUBLISHER_HEADERS)
        client.post(
            f"/v1/knowledge/procedures/{procedure_id}:approve",
            json={"expectedVersion": 1},
            headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        response = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:reject",
            json={"reason": "Too late"},
            headers=PUBLISHER_HEADERS,
        )
        assert response.status_code == 403

    def test_rejected_cannot_be_approved(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        client.post(f"/v1/knowledge/procedures/{procedure_id}:submit", headers=PUBLISHER_HEADERS)
        client.post(
            f"/v1/knowledge/procedures/{procedure_id}:reject",
            json={"reason": "Needs rework"},
            headers=PUBLISHER_HEADERS,
        )
        response = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:approve",
            json={"expectedVersion": 1},
            headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 403

    def test_rejected_cannot_be_submitted(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        client.post(
            f"/v1/knowledge/procedures/{procedure_id}:reject",
            json={"reason": "Bad"},
            headers=PUBLISHER_HEADERS,
        )
        response = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:submit",
            headers=PUBLISHER_HEADERS,
        )
        assert response.status_code == 403

    def test_draft_cannot_be_approved_directly(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        response = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:approve",
            json={"expectedVersion": 1},
            headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 403


class TestAuditChain:
    def test_audit_written_and_chain_verifies(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        client.post(f"/v1/knowledge/procedures/{procedure_id}:submit", headers=PUBLISHER_HEADERS)
        client.post(
            f"/v1/knowledge/procedures/{procedure_id}:approve",
            json={"expectedVersion": 1},
            headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        response = client.get("/v1/knowledge/audit", headers=PUBLISHER_HEADERS)
        assert response.status_code == 200
        records = response.json()["items"]
        assert len(records) >= 3

        # Verify BFF-level audit chain
        response_full = client.get("/v1/audit/decisions?domain=knowledge", headers=PUBLISHER_HEADERS)
        assert response_full.status_code == 200


class TestDemoSeedReset:
    def test_seed_adds_procedures(self, client: TestClient) -> None:
        response = client.post("/v1/knowledge/demo/seed", headers=PUBLISHER_HEADERS)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["seeded"] == 25

    def test_reset_returns_to_baseline(self, client: TestClient) -> None:
        client.post("/v1/knowledge/demo/seed", headers=PUBLISHER_HEADERS)
        response = client.post("/v1/knowledge/demo/reset", headers=PUBLISHER_HEADERS)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["reset"] is True
        assert data["procedureCount"] == 2  # the two seed procedures

    def test_reader_cannot_seed(self, client: TestClient) -> None:
        response = client.post("/v1/knowledge/demo/seed", headers=READER_HEADERS)
        assert response.status_code == 403

    def test_reader_cannot_reset(self, client: TestClient) -> None:
        response = client.post("/v1/knowledge/demo/reset", headers=READER_HEADERS)
        assert response.status_code == 403


class TestGetProcedure:
    def test_get_existing_procedure(self, client: TestClient) -> None:
        data = _create_interview(client)
        procedure_id = data["draftProcedureId"]
        response = client.get(
            f"/v1/knowledge/procedures/{procedure_id}", headers=PUBLISHER_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["data"]["procedureId"] == procedure_id

    def test_get_nonexistent_procedure(self, client: TestClient) -> None:
        response = client.get(
            "/v1/knowledge/procedures/PROC-NONEXIST", headers=PUBLISHER_HEADERS
        )
        assert response.status_code == 404
