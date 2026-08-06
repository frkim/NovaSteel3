"""Production audio storage adapter for Azure Blob Storage (managed identity).

Mirrors the auth pattern used by the other Azure adapters (``azure_speech.py``,
``search_store.py``): authenticate with ``DefaultAzureCredential`` — managed
identity in Azure, developer identity locally — and never an account key or
connection string in source. The Azure SDK is imported lazily so the rest of the
service (and its tests/demo) runs with zero cloud dependencies. Install packages
only from the approved feed (see pip.conf).

``store`` returns the blob name as an **opaque** reference; a SAS URL is never
returned to callers so credentials never leak into responses, logs, or the audit
trail.
"""

from __future__ import annotations

import hashlib
from typing import Optional

from .base import AudioStorageAdapter


class AzureBlobAudioStorageAdapter(AudioStorageAdapter):
    """Persist interview audio to a Blob container using a managed-identity token."""

    def __init__(
        self,
        account_url: str,
        container: str = "knowledge-audio",
        credential: Optional[object] = None,
    ):
        if not account_url:
            raise ValueError("Blob account_url is required")
        self.account_url = account_url.rstrip("/")
        self.container = container
        self._credential = credential  # dependency-injected for testability

    def _container_client(self):  # pragma: no cover - requires azure-storage-blob
        from azure.storage.blob import BlobServiceClient

        credential = self._credential or _default_credential()
        service = BlobServiceClient(
            account_url=self.account_url, credential=credential
        )
        return service.get_container_client(self.container)

    def store(self, *, session_id: str, data: bytes, content_type: str) -> str:  # pragma: no cover - requires cloud
        from azure.storage.blob import ContentSettings

        digest = hashlib.sha256(data).hexdigest()[:16]
        blob_name = f"{session_id}/{digest}"
        client = self._container_client()
        client.upload_blob(
            name=blob_name,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )
        # Opaque reference: the blob path scoped to the configured container, not
        # a SAS URL — resolution requires a fresh managed-identity token.
        return f"azureblob://{self.container}/{blob_name}"

    def delete(self, audio_ref: str) -> None:  # pragma: no cover - requires cloud
        prefix = f"azureblob://{self.container}/"
        if not audio_ref.startswith(prefix):
            return
        blob_name = audio_ref[len(prefix):]
        client = self._container_client()
        try:
            client.delete_blob(blob_name)
        except Exception:  # noqa: BLE001 - deletion is best-effort/idempotent
            pass


def _default_credential():  # pragma: no cover - requires azure-identity
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()
