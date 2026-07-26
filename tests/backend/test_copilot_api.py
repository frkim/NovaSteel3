from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def _chat(
    client: TestClient, headers: dict[str, str], **body: Any
) -> dict[str, Any]:
    payload: dict[str, Any] = {"question": "What is the risk?"}
    payload.update(body)
    response = client.post("/v1/copilot/chat", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_copilot_endpoints_require_authentication(client: TestClient) -> None:
    for path in (
        "/v1/copilot/suggestions",
        "/v1/copilot/glossary",
        "/v1/copilot/conversations",
        "/v1/copilot/conversations/conv-1",
    ):
        response = client.get(path)
        assert response.status_code == 401, path
        assert response.json()["code"] == "INVALID_TOKEN"

    assert client.delete("/v1/copilot/conversations/conv-1").status_code == 401
    chat = client.post("/v1/copilot/chat", json={"question": "hi"})
    assert chat.status_code == 401
    assert chat.json()["code"] == "INVALID_TOKEN"


def test_suggestions_follow_the_section_and_locale(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    english = client.get(
        "/v1/copilot/suggestions?section=furnace-health", headers=admin_headers
    )
    assert english.status_code == 200
    data = english.json()["data"]
    assert data["section"] == "furnace-health"
    assert data["language"] == "en"
    assert len(data["questions"]) == 5

    french = client.get(
        "/v1/copilot/suggestions?section=furnace-health&locale=fr",
        headers=admin_headers,
    )
    french_data = french.json()["data"]
    assert french_data["language"] == "fr"
    assert french_data["questions"] != data["questions"]

    unknown = client.get(
        "/v1/copilot/suggestions?section=not-a-screen", headers=admin_headers
    )
    assert unknown.status_code == 200
    assert len(unknown.json()["data"]["questions"]) == 5


def test_glossary_search_and_section_defaults(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    searched = client.get(
        "/v1/copilot/glossary?q=thermal&limit=3", headers=admin_headers
    )
    assert searched.status_code == 200
    entries = searched.json()["data"]["entries"]
    assert 1 <= len(entries) <= 3
    assert any("thermal" in entry["term"].lower() for entry in entries)

    scoped = client.get(
        "/v1/copilot/glossary?section=furnace-health&locale=de", headers=admin_headers
    )
    scoped_data = scoped.json()["data"]
    assert scoped_data["language"] == "de"
    assert scoped_data["entries"]

    assert (
        client.get("/v1/copilot/glossary?limit=0", headers=admin_headers).status_code
        == 400
    )


def test_chat_persists_a_conversation_that_can_be_replayed_and_deleted(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    answer = _chat(
        client,
        admin_headers,
        context={"section": "furnace-health"},
    )
    assert answer["conversationId"]
    assert answer["answer"]["role"] == "assistant"
    assert answer["answer"]["sources"]
    assert answer["resolvedConcepts"]
    assert answer["resolvedReasoning"] in {"default", "high"}

    conversation_id = answer["conversationId"]
    listed = client.get("/v1/copilot/conversations", headers=admin_headers)
    assert conversation_id in {
        item["conversationId"] for item in listed.json()["data"]["conversations"]
    }

    replay = client.get(
        f"/v1/copilot/conversations/{conversation_id}", headers=admin_headers
    )
    assert replay.status_code == 200
    assert len(replay.json()["data"]["messages"]) == 2

    follow_up = _chat(
        client,
        admin_headers,
        question="And what drives it?",
        conversationId=conversation_id,
    )
    assert follow_up["conversationId"] == conversation_id

    deleted = client.delete(
        f"/v1/copilot/conversations/{conversation_id}", headers=admin_headers
    )
    assert deleted.status_code == 204
    missing = client.get(
        f"/v1/copilot/conversations/{conversation_id}", headers=admin_headers
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "NOT_FOUND"


def test_temporary_chats_are_never_stored(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    before = client.get("/v1/copilot/conversations", headers=admin_headers)
    baseline = len(before.json()["data"]["conversations"])

    answer = _chat(client, admin_headers, temporary=True)
    assert answer["temporary"] is True

    after = client.get("/v1/copilot/conversations", headers=admin_headers)
    assert len(after.json()["data"]["conversations"]) == baseline
    assert (
        client.get(
            f"/v1/copilot/conversations/{answer['conversationId']}",
            headers=admin_headers,
        ).status_code
        == 404
    )


def test_chat_localises_the_answer_and_reports_the_grounding_mode(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    offline = _chat(
        client,
        admin_headers,
        question="Comment fonctionne la signature thermique ?",
        locale="fr",
        temporary=True,
        context={"section": "furnace-health"},
    )
    assert offline["language"] == "fr"
    assert offline["onlineSearchUsed"] is False
    assert all(
        source["kind"] != "online" for source in offline["answer"]["sources"]
    )

    online = _chat(
        client,
        admin_headers,
        question="What are the latest EU ETS announcements?",
        onlineSearch=True,
        temporary=True,
        context={"section": "co2-compliance"},
    )
    assert online["onlineSearchUsed"] is True
    online_sources = [
        source for source in online["answer"]["sources"] if source["kind"] == "online"
    ]
    assert online_sources
    assert all(source.get("url") for source in online_sources)


def test_chat_rejects_malformed_payloads(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    cases = (
        {},
        {"question": "   "},
        {"question": "hi", "unexpected": True},
        {"question": "hi", "context": "furnace-health"},
        {"question": "hi", "onlineSearch": "yes"},
        {"question": "hi", "temporary": 1},
        {"question": "hi", "reasoning": "turbo"},
    )
    for payload in cases:
        response = client.post("/v1/copilot/chat", json=payload, headers=admin_headers)
        assert response.status_code == 400, payload
        assert response.json()["code"] == "VALIDATION_ERROR", payload


def test_conversations_are_scoped_to_their_owner(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    owned = _chat(client, admin_headers)["conversationId"]
    other = dict(admin_headers)
    other["X-Demo-User"] = "another-operator"

    assert client.get("/v1/copilot/conversations", headers=other).json()["data"][
        "conversations"
    ] == []
    assert (
        client.get(f"/v1/copilot/conversations/{owned}", headers=other).status_code
        == 404
    )
    assert (
        client.delete(f"/v1/copilot/conversations/{owned}", headers=other).status_code
        == 404
    )
