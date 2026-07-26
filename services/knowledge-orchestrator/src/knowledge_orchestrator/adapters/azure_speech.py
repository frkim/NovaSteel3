"""Production Speech Fast Transcription adapter (Entra managed identity, no keys).

This adapter demonstrates the required auth pattern from solution-architecture.md
§4.3/§8: authenticate with ``DefaultAzureCredential`` (managed identity in Azure,
developer identity locally) and acquire an Entra bearer token for the Cognitive
Services scope — never an account key in source. The Azure SDK / requests packages
are imported lazily so the rest of the service (and its tests) run with zero cloud
dependencies. Install packages only from the approved feed (see pip.conf).
"""

from __future__ import annotations

from typing import Optional

from ..models import AudioMetadata, Classification, Transcript, TranscriptSegment
from .base import SpeechTranscriptionAdapter

# Entra token scope for Azure AI Services (Speech) resource-plane access.
COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"


class AzureSpeechFastTranscriptionAdapter(SpeechTranscriptionAdapter):
    """Fast Transcription via the Speech REST API using a managed-identity token."""

    def __init__(
        self,
        endpoint: str,
        region: str = "swedencentral",
        credential: Optional[object] = None,
    ):
        if not endpoint:
            raise ValueError("Speech endpoint is required")
        self.endpoint = endpoint.rstrip("/")
        self.region = region
        self._credential = credential  # dependency-injected for testability

    def _get_token(self) -> str:
        """Acquire a short-lived Entra bearer token; never a Speech account key."""
        credential = self._credential or _default_credential()
        return credential.get_token(COGNITIVE_SERVICES_SCOPE).token

    def transcribe(self, audio_ref: str, meta: AudioMetadata) -> Transcript:  # pragma: no cover - requires cloud
        import requests  # lazy: only needed for live calls

        token = self._get_token()
        url = f"{self.endpoint}/speechtotext/transcriptions:transcribe?api-version=2024-11-15"
        headers = {"Authorization": f"Bearer {token}"}
        definition = {
            "locales": [meta.language],
            "profanityFilterMode": "Masked",
            "diarization": {"maxSpeakers": 2, "enabled": True},
        }
        with open(audio_ref, "rb") as fh:
            resp = requests.post(
                url,
                headers=headers,
                files={"audio": fh},
                data={"definition": _to_json(definition)},
                timeout=120,
            )
        resp.raise_for_status()
        return _map_response(resp.json(), meta)


def _default_credential():  # pragma: no cover - requires azure-identity
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


def _to_json(obj) -> str:
    import json

    return json.dumps(obj)


def _map_response(payload: dict, meta: AudioMetadata) -> Transcript:  # pragma: no cover
    segments = []
    for i, phrase in enumerate(payload.get("phrases", [])):
        segments.append(
            TranscriptSegment(
                segment_id=f"seg-{i:03d}",
                speaker=f"speaker-{phrase.get('speaker', 0)}",
                start_seconds=phrase.get("offsetMilliseconds", 0) / 1000.0,
                end_seconds=(
                    phrase.get("offsetMilliseconds", 0)
                    + phrase.get("durationMilliseconds", 0)
                )
                / 1000.0,
                text=phrase.get("text", ""),
                confidence=phrase.get("confidence", 0.0),
            )
        )
    return Transcript(
        session_id=meta.session_id,
        language=meta.language,
        status="COMPLETED",
        segments=tuple(segments),
        classification=Classification.HIGHLY_CONFIDENTIAL,
    )
