"""API tests for operator audio upload and draft extraction endpoints.

Covers the happy path (upload -> transcript -> draft -> submit), consent-denied
403, oversized and unsupported-type rejection, role gating, and the demo-mode
path that runs with no cloud configuration at all.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from bff_api import routes
from bff_api.config import DemoMode, Settings
from bff_api.main import create_app


PUBLISHER_HEADERS = {
    "X-Demo-User": "test-reviewer",
    "X-Demo-Roles": "Knowledge.Publisher",
    "X-Demo-Plants": "NS-DEMO-LUX-01",
    "X-Demo-Display-Name": "Test Reviewer",
    "X-Demo-Locale": "en",
}

CONTRIBUTOR_HEADERS = {
    "X-Demo-User": "shopfloor-op",
    "X-Demo-Roles": "Knowledge.Contributor",
    "X-Demo-Plants": "NS-DEMO-LUX-01",
    "X-Demo-Display-Name": "Shop Floor Operator",
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


def _create_interview(client: TestClient, language: str = "en") -> str:
    body = {
        "operatorRef": "OP-AUDIO-001",
        "language": language,
        "consent": {"granted": True, "scope": "knowledge-capture", "retentionDays": 30},
    }
    response = client.post(
        "/v1/knowledge/interviews",
        json=body,
        headers={**PUBLISHER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]["sessionId"]


def _upload(client, session_id, *, headers=CONTRIBUTOR_HEADERS, data=b"webm-bytes",
            content_type="audio/webm", duration="12.5", language="en"):
    return client.post(
        f"/v1/knowledge/interviews/{session_id}/audio",
        files={"file": ("recording.webm", data, content_type)},
        data={"durationSeconds": duration, "language": language},
        headers=headers,
    )


class TestAudioUpload:
    def test_happy_path_upload_transcript_draft_submit(self, client: TestClient) -> None:
        session_id = _create_interview(client)

        upload = _upload(client, session_id)
        assert upload.status_code == 202, upload.json()
        payload = upload.json()["data"]
        assert payload["sessionId"] == session_id
        assert payload["status"] in {"PROCESSING", "COMPLETED"}
        assert payload["auditRef"]
        # audioRef must be an opaque reference, never a raw (SAS) URL.
        assert not payload["audioRef"].startswith("http")
        assert "sig=" not in payload["audioRef"].lower()

        transcript = client.get(
            f"/v1/knowledge/interviews/{session_id}/transcript", headers=PUBLISHER_HEADERS
        )
        assert transcript.status_code == 200
        assert transcript.json()["data"]["status"] == "COMPLETED"
        assert transcript.json()["data"]["segments"]

        draft = client.post(
            f"/v1/knowledge/interviews/{session_id}/draft",
            json={"title": "Operator recorded procedure", "domain": "hearth"},
            headers={**CONTRIBUTOR_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert draft.status_code == 201, draft.json()
        draft_data = draft.json()["data"]
        assert draft_data["status"] == "DRAFT"
        procedure_id = draft_data["procedureId"]

        # The DRAFT shows up in the normal procedures list and can be submitted.
        listing = client.get("/v1/knowledge/procedures?status=DRAFT", headers=PUBLISHER_HEADERS)
        assert any(row["procedureId"] == procedure_id for row in listing.json()["items"])

        submit = client.post(
            f"/v1/knowledge/procedures/{procedure_id}:submit", headers=PUBLISHER_HEADERS
        )
        assert submit.status_code == 200
        assert submit.json()["data"]["status"] == "IN_REVIEW"

    def test_publisher_may_also_upload(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        upload = _upload(client, session_id, headers=PUBLISHER_HEADERS)
        assert upload.status_code == 202

    def test_reader_role_forbidden(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        upload = _upload(client, session_id, headers=READER_HEADERS)
        assert upload.status_code == 403

    def test_unknown_session_404(self, client: TestClient) -> None:
        upload = _upload(client, "IV-UNKNOWN")
        assert upload.status_code == 404

    def test_consent_withdrawn_403(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        client.app.state.services.knowledge.orchestrator.withdraw_consent(
            session_id=session_id, deletion_request_ref="erase-req-1"
        )
        upload = _upload(client, session_id)
        assert upload.status_code == 403

    def test_unsupported_content_type_400(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        upload = _upload(client, session_id, content_type="application/pdf")
        assert upload.status_code == 400

    def test_invalid_language_400(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        upload = _upload(client, session_id, language="zz")
        assert upload.status_code == 400

    def test_invalid_duration_400(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        upload = _upload(client, session_id, duration="not-a-number")
        assert upload.status_code == 400

    def test_oversized_upload_413(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(routes, "_AUDIO_MAX_BYTES", 1024)
        session_id = _create_interview(client)
        upload = _upload(client, session_id, data=b"x" * 4096)
        assert upload.status_code == 413
        assert upload.json()["code"] == "PAYLOAD_TOO_LARGE"

    def test_language_mismatch_with_consent_400(self, client: TestClient) -> None:
        session_id = _create_interview(client, language="en")
        # Consent recorded 'en'; uploading 'fr' audio is a validation error.
        upload = _upload(client, session_id, language="fr")
        assert upload.status_code == 400


class TestDraftExtraction:
    def test_draft_requires_idempotency_key(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        _upload(client, session_id)
        response = client.post(
            f"/v1/knowledge/interviews/{session_id}/draft",
            json={"title": "T", "domain": "hearth"},
            headers=CONTRIBUTOR_HEADERS,
        )
        assert response.status_code == 400

    def test_draft_is_idempotent(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        _upload(client, session_id)
        key = str(uuid.uuid4())
        body = {"title": "Recorded procedure", "domain": "hearth"}
        first = client.post(
            f"/v1/knowledge/interviews/{session_id}/draft",
            json=body,
            headers={**CONTRIBUTOR_HEADERS, "Idempotency-Key": key},
        )
        second = client.post(
            f"/v1/knowledge/interviews/{session_id}/draft",
            json=body,
            headers={**CONTRIBUTOR_HEADERS, "Idempotency-Key": key},
        )
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["data"]["procedureId"] == second.json()["data"]["procedureId"]

    def test_draft_reader_forbidden(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        response = client.post(
            f"/v1/knowledge/interviews/{session_id}/draft",
            json={"title": "T", "domain": "hearth"},
            headers={**READER_HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 403


class TestDemoModeNoCloud:
    def test_demo_mode_uses_local_opaque_storage(self, client: TestClient) -> None:
        """Demo mode works end-to-end with no cloud config and an opaque audioRef."""
        knowledge = client.app.state.services.knowledge
        from knowledge_orchestrator.adapters import (
            LocalAudioStorageAdapter,
            LocalSpeechTranscriptionAdapter,
        )

        assert isinstance(knowledge._audio_storage, LocalAudioStorageAdapter)
        assert isinstance(knowledge.orchestrator.speech, LocalSpeechTranscriptionAdapter)

        session_id = _create_interview(client)
        upload = _upload(client, session_id)
        assert upload.status_code == 202
        assert upload.json()["data"]["audioRef"].startswith("af://")

    def test_audit_never_leaks_raw_audio(self, client: TestClient) -> None:
        session_id = _create_interview(client)
        _upload(client, session_id)
        audit = client.get("/v1/knowledge/audit", headers=PUBLISHER_HEADERS)
        blob = audit.text.lower()
        assert "webm-bytes" not in blob
