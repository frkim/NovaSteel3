"""Tests for audio storage adapters and the speech/audio adapter factories.

Covers the opaque-reference contract of the local audio store, the filesystem
variant, and the environment-driven selection between local fixtures and the
Azure adapters (which must never require the cloud SDK at import time).
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from knowledge_orchestrator.adapter_factory import (
    create_audio_storage,
    create_speech,
)
from knowledge_orchestrator.adapters import (
    AudioStorageAdapter,
    LocalAudioStorageAdapter,
    LocalSpeechTranscriptionAdapter,
)
from knowledge_orchestrator.adapters.azure_audio import AzureBlobAudioStorageAdapter
from knowledge_orchestrator.adapters.azure_speech import (
    AzureSpeechFastTranscriptionAdapter,
)


class TestLocalAudioStorageAdapter:
    def test_store_returns_opaque_reference(self):
        store = LocalAudioStorageAdapter()
        ref = store.store(session_id="IV-00001", data=b"webm-bytes", content_type="audio/webm")

        assert isinstance(store, AudioStorageAdapter)
        # Opaque — not a fetchable/credentialed URL, no SAS signature.
        assert not ref.startswith("http")
        assert "sig=" not in ref.lower()
        assert "IV-00001" in ref

    def test_store_is_content_addressed_and_retrievable(self):
        store = LocalAudioStorageAdapter()
        ref1 = store.store(session_id="IV-1", data=b"same", content_type="audio/wav")
        ref2 = store.store(session_id="IV-1", data=b"same", content_type="audio/wav")
        assert ref1 == ref2
        assert store._blobs[ref1] == b"same"

    def test_delete_removes_blob(self):
        store = LocalAudioStorageAdapter()
        ref = store.store(session_id="IV-1", data=b"bytes", content_type="audio/wav")
        store.delete(ref)
        assert ref not in store._blobs
        # Deleting a missing ref is a no-op.
        store.delete(ref)

    def test_filesystem_backed_store(self, tmp_path):
        store = LocalAudioStorageAdapter(base_dir=tmp_path)
        ref = store.store(session_id="IV-9", data=b"persist-me", content_type="audio/webm")
        written = list(tmp_path.rglob("*"))
        assert any(p.is_file() and p.read_bytes() == b"persist-me" for p in written)
        store.delete(ref)
        assert not any(p.is_file() for p in tmp_path.rglob("*"))


class TestAudioStorageFactory:
    def test_no_account_url_returns_local(self):
        with patch.dict(os.environ, {}, clear=True):
            assert isinstance(create_audio_storage(), LocalAudioStorageAdapter)

    def test_explicit_local_mode(self):
        with patch.dict(os.environ, {"KNOWLEDGE_AUDIO_MODE": "local"}, clear=True):
            assert isinstance(create_audio_storage(), LocalAudioStorageAdapter)

    def test_account_url_selects_azure_adapter(self):
        env = {"AUDIO_STORAGE_ACCOUNT_URL": "https://acct.blob.core.windows.net"}
        with patch.dict(os.environ, env, clear=True):
            adapter = create_audio_storage()
            # Construction must not require the cloud SDK (imported lazily per call).
            assert isinstance(adapter, AzureBlobAudioStorageAdapter)
            assert adapter.container == "knowledge-audio"

    def test_local_mode_wins_over_account_url(self):
        env = {
            "KNOWLEDGE_AUDIO_MODE": "local",
            "AUDIO_STORAGE_ACCOUNT_URL": "https://acct.blob.core.windows.net",
        }
        with patch.dict(os.environ, env, clear=True):
            assert isinstance(create_audio_storage(), LocalAudioStorageAdapter)


class TestSpeechFactory:
    def test_no_endpoint_returns_local(self):
        with patch.dict(os.environ, {}, clear=True):
            assert isinstance(create_speech(), LocalSpeechTranscriptionAdapter)

    def test_explicit_local_mode(self):
        with patch.dict(os.environ, {"KNOWLEDGE_SPEECH_MODE": "local"}, clear=True):
            assert isinstance(create_speech(), LocalSpeechTranscriptionAdapter)

    def test_endpoint_selects_azure_adapter(self):
        env = {"SPEECH_ENDPOINT": "https://swedencentral.stt.speech.microsoft.com"}
        with patch.dict(os.environ, env, clear=True):
            adapter = create_speech()
            assert isinstance(adapter, AzureSpeechFastTranscriptionAdapter)

    def test_local_mode_wins_over_endpoint(self):
        env = {
            "KNOWLEDGE_SPEECH_MODE": "local",
            "SPEECH_ENDPOINT": "https://swedencentral.stt.speech.microsoft.com",
        }
        with patch.dict(os.environ, env, clear=True):
            assert isinstance(create_speech(), LocalSpeechTranscriptionAdapter)


class TestOrchestratorAudioRoundTrip:
    """Store a browser blob locally, then transcribe it through the orchestrator."""

    def test_submit_audio_via_local_store(self, orchestrator):
        created = orchestrator.create_interview(
            operator_ref="OP-1",
            language="en",
            retention_days=30,
            consent_granted=True,
        )
        session_id = created["sessionId"]

        store = LocalAudioStorageAdapter()
        audio_ref = store.store(
            session_id=session_id, data=b"opus-bytes", content_type="audio/webm"
        )
        from knowledge_orchestrator.models import AudioMetadata

        meta = AudioMetadata(
            session_id=session_id,
            content_type="audio/webm",
            duration_seconds=42.0,
            sample_rate_hz=16000,
            channels=1,
            size_bytes=len(b"opus-bytes"),
            language="en",
            speaker_role="operator",
            checksum="sha256:deadbeef",
        )
        result = orchestrator.submit_audio(
            session_id=session_id, meta=meta, audio_ref=audio_ref
        )
        assert result["status"] == "COMPLETED"

        transcript = orchestrator.get_transcript(session_id)
        assert transcript["status"] == "COMPLETED"
        assert transcript["segments"]
