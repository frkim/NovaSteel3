"""Knowledge-orchestrator service (solution-architecture.md §5.2).

Coordinates consent, Speech Fast Transcription, the Foundry knowledge agent,
grounding/prompt-injection defenses, the draft->review->approved workflow, and the
append-only audit log. Methods map 1:1 to the ``/v1/knowledge/*`` BFF routes in
api-contracts.md §4.7/§10 so the BFF can delegate directly (see contracts/ and
README.md for the route mapping). This class is transport-agnostic and fully offline
with the local adapters.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Optional

from . import audio as audio_mod
from . import consent as consent_mod
from . import grounding
from . import procedure_workflow as wf
from .adapters.base import FoundryAgentAdapter, SpeechTranscriptionAdapter
from .adapters.local_foundry import LocalFoundryKnowledgeAgent
from .adapters.local_speech import LocalSpeechTranscriptionAdapter
from .audit import AuditLog
from .models import (
    AudioMetadata,
    ConsentRecord,
    ConsentState,
    Procedure,
    ProcedureStatus,
    Transcript,
)


class OrchestratorError(Exception):
    """Base error carrying a stable ``code`` compatible with api-contracts §6."""

    code = "ORCHESTRATOR_ERROR"


class NotFoundError(OrchestratorError):
    code = "NOT_FOUND"


class ConflictError(OrchestratorError):
    code = "CONFLICT"


class ForbiddenError(OrchestratorError):
    code = "FORBIDDEN"


@dataclass
class _Repos:
    consents: dict[str, ConsentRecord] = field(default_factory=dict)
    transcripts: dict[str, Transcript] = field(default_factory=dict)
    procedures: dict[str, Procedure] = field(default_factory=dict)
    idempotency: dict[str, str] = field(default_factory=dict)  # key -> procedure_id


class KnowledgeOrchestrator:
    """In-memory, deterministic orchestration of the knowledge-capture workflow."""

    def __init__(
        self,
        speech: Optional[SpeechTranscriptionAdapter] = None,
        agent: Optional[FoundryAgentAdapter] = None,
        audit: Optional[AuditLog] = None,
    ):
        self.speech = speech or LocalSpeechTranscriptionAdapter()
        self.agent = agent or LocalFoundryKnowledgeAgent()
        self.audit = audit or AuditLog()
        self._repos = _Repos()
        self._seq = itertools.count(1)

    # -- POST /v1/knowledge/interviews --------------------------------------
    def create_interview(
        self,
        *,
        operator_ref: str,
        language: str,
        retention_days: int,
        consent_granted: bool,
        speaker_role: str = "operator",
        scope: str = consent_mod.CONSENT_SCOPE,
        correlation_id: str = "",
    ) -> dict:
        """Create a consent-bound interview session (api-contracts §4.7)."""
        session_id = f"IV-{next(self._seq):05d}"
        record = consent_mod.create_session(
            session_id=session_id,
            operator_ref=operator_ref,
            language=language,
            speaker_role=speaker_role,
            retention_days=retention_days,
            scope=scope,
        )
        if consent_granted:
            record = consent_mod.grant(record)
        else:
            record = consent_mod.deny(record)
        self._repos.consents[session_id] = record
        self.audit.append(
            correlation_id=correlation_id or session_id,
            domain="knowledge",
            action="interview.create",
            entity_id=session_id,
            actor=operator_ref,
            inputs={"scope": scope, "retentionDays": retention_days},
            output={"consentState": record.state.value},
            decision="CONSENT_GRANTED" if consent_granted else "CONSENT_DENIED",
        )
        return {"sessionId": session_id, "consentState": record.state.value}

    # -- internal: submit audio to Speech Fast Transcription ----------------
    def submit_audio(
        self, *, session_id: str, meta: AudioMetadata, audio_ref: str, correlation_id: str = ""
    ) -> dict:
        """Validate consent+audio and transcribe (api-contracts §10.3 step 2-3)."""
        record = self._require_consent(session_id)
        consent_mod.require_capture_allowed(record)
        audio_mod.validate_audio_metadata(meta, record)
        transcript = self.speech.transcribe(audio_ref, meta)
        self._repos.transcripts[session_id] = transcript
        self.audit.append(
            correlation_id=correlation_id or session_id,
            domain="knowledge",
            action="interview.transcribe",
            entity_id=session_id,
            actor="mi-ns-knowledge",
            inputs={"language": meta.language, "audio": audio_ref},
            output={"status": transcript.status, "segments": len(transcript.segments)},
        )
        return {"sessionId": session_id, "status": transcript.status}

    # -- GET /v1/knowledge/interviews/{sessionId}/transcript ----------------
    def get_transcript(self, session_id: str) -> dict:
        record = self._require_consent(session_id)
        if record.state is ConsentState.WITHDRAWN:
            raise ForbiddenError("transcript unavailable: consent withdrawn")
        transcript = self._repos.transcripts.get(session_id)
        if transcript is None:
            return {"status": "PROCESSING"}
        return {
            "status": transcript.status,
            "language": transcript.language,
            "classification": transcript.classification.value,
            "segments": [
                {
                    "segmentId": s.segment_id,
                    "speaker": s.speaker,
                    "start": s.start_seconds,
                    "end": s.end_seconds,
                    "text": s.text,
                    "confidence": s.confidence,
                }
                for s in transcript.segments
            ],
        }

    # -- internal: extract a DRAFT procedure via the knowledge agent --------
    def extract_draft(
        self, *, session_id: str, title: str, task: str = "", correlation_id: str = ""
    ) -> Procedure:
        """Run the knowledge agent to write a grounded DRAFT (api-contracts §10.3 step 5)."""
        self._require_consent(session_id)
        transcript = self._repos.transcripts.get(session_id)
        if transcript is None:
            raise NotFoundError("transcript not available for extraction")

        task = task or "Extract a grounded operational procedure draft."
        result = self.agent.extract_draft(task, transcript)
        if result.refused or result.knowledge is None:
            self.audit.append(
                correlation_id=correlation_id or session_id,
                domain="knowledge",
                action="draft.refused",
                entity_id=session_id,
                actor=self.agent.agent_name,
                inputs={"prompt": task},
                output={"trace": list(result.trace)},
                decision="REFUSED",
            )
            raise ConflictError(result.refusal_reason or "agent refused extraction")

        # Grounding gate: every citation must reference a real transcript segment.
        grounding.enforce_extraction_grounding(
            result.knowledge.citations, transcript.segment_ids()
        )

        procedure_id = f"PROC-{session_id}"
        procedure = wf.create_draft(
            procedure_id=procedure_id,
            title=title,
            knowledge=result.knowledge,
            session_id=session_id,
            created_by=self.agent.agent_name,
        )
        self._repos.procedures[procedure_id] = procedure
        self.audit.append(
            correlation_id=correlation_id or session_id,
            domain="knowledge",
            action="draft.create",
            entity_id=procedure_id,
            actor=self.agent.agent_name,
            inputs={"sessionId": session_id},
            output={
                "status": procedure.status.value,
                "citations": [c.to_ref() for c in procedure.citations],
            },
            decision="DRAFT_CREATED",
        )
        return procedure

    # -- GET /v1/knowledge/procedures ---------------------------------------
    def list_procedures(
        self,
        *,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> dict:
        items = list(self._repos.procedures.values())
        if status:
            items = [p for p in items if p.status.value == status]
        if q:
            ql = q.lower()
            items = [p for p in items if ql in p.title.lower()]
        total = len(items)
        start = (page - 1) * size
        window = items[start : start + size]
        return {
            "items": [self._procedure_view(p) for p in window],
            "total": total,
            "page": page,
            "size": size,
        }

    # -- GET /v1/knowledge/search (APPROVED only) ---------------------------
    def search_procedures(self, q: str) -> dict:
        """Search the derived index of APPROVED procedures only (never drafts)."""
        ql = (q or "").lower()
        items = [
            p
            for p in self._repos.procedures.values()
            if wf.is_retrievable(p)
            and (not ql or ql in p.title.lower() or ql in p.knowledge.observation.lower())
        ]
        return {"items": [self._procedure_view(p) for p in items], "total": len(items)}

    def get_procedure(self, procedure_id: str) -> Procedure:
        procedure = self._repos.procedures.get(procedure_id)
        if procedure is None:
            raise NotFoundError(f"procedure '{procedure_id}' not found")
        return procedure

    def submit_for_review(self, procedure_id: str, actor: str) -> Procedure:
        procedure = self.get_procedure(procedure_id)
        updated = wf.submit_for_review(procedure, actor)
        self._repos.procedures[procedure_id] = updated
        return updated

    # -- POST /v1/knowledge/procedures/{id}:approve -------------------------
    def approve_procedure(
        self,
        *,
        procedure_id: str,
        actor: str,
        actor_roles: set[str],
        expected_version: int,
        idempotency_key: str,
        correlation_id: str = "",
    ) -> Procedure:
        """Publish a reviewed immutable version (Knowledge.Publisher only)."""
        if idempotency_key in self._repos.idempotency:
            return self.get_procedure(self._repos.idempotency[idempotency_key])

        procedure = self.get_procedure(procedure_id)
        try:
            approved = wf.approve(
                procedure, actor, actor_roles, expected_version
            )
        except wf.WorkflowError as exc:
            raise ForbiddenError(str(exc)) from exc
        except wf.StaleApprovalError as exc:
            raise ConflictError(str(exc)) from exc

        self._repos.procedures[procedure_id] = approved
        self._repos.idempotency[idempotency_key] = procedure_id
        self.audit.append(
            correlation_id=correlation_id or procedure_id,
            domain="knowledge",
            action="procedure.approve",
            entity_id=procedure_id,
            actor=actor,
            inputs={"expectedVersion": expected_version},
            output={"status": approved.status.value, "version": approved.version},
            decision="APPROVED",
        )
        return approved

    # -- POST /v1/knowledge/procedures/{id}:reject --------------------------
    def reject_procedure(
        self, *, procedure_id: str, actor: str, actor_roles: set[str], correlation_id: str = ""
    ) -> Procedure:
        procedure = self.get_procedure(procedure_id)
        try:
            rejected = wf.reject(procedure, actor, actor_roles)
        except wf.WorkflowError as exc:
            raise ForbiddenError(str(exc)) from exc
        self._repos.procedures[procedure_id] = rejected
        self.audit.append(
            correlation_id=correlation_id or procedure_id,
            domain="knowledge",
            action="procedure.reject",
            entity_id=procedure_id,
            actor=actor,
            inputs={},
            output={"status": rejected.status.value},
            decision="REJECTED",
        )
        return rejected

    # -- consent withdrawal (GDPR Art. 17) ----------------------------------
    def withdraw_consent(
        self, *, session_id: str, deletion_request_ref: str, correlation_id: str = ""
    ) -> dict:
        record = self._require_consent(session_id)
        updated, directive = consent_mod.withdraw(record, deletion_request_ref)
        self._repos.consents[session_id] = updated
        # Propagate raw-audio/transcript deletion.
        self._repos.transcripts.pop(session_id, None)
        self.audit.append(
            correlation_id=correlation_id or session_id,
            domain="knowledge",
            action="consent.withdraw",
            entity_id=session_id,
            actor=record.operator_ref,
            inputs={"deletionRequestRef": deletion_request_ref},
            output={"consentState": updated.state.value},
            decision="WITHDRAWN",
        )
        return {
            "sessionId": session_id,
            "consentState": updated.state.value,
            "deletion": {
                "sessionId": directive.session_id,
                "reason": directive.reason,
                "deletionRequestRef": directive.deletion_request_ref,
            },
        }

    # -- GET /v1/audit/decisions?domain=knowledge ---------------------------
    def get_audit(self, *, domain: str = "knowledge", entity_id: Optional[str] = None) -> list[dict]:
        return [
            {
                "sequence": r.sequence,
                "correlationId": r.correlation_id,
                "domain": r.domain,
                "action": r.action,
                "entityId": r.entity_id,
                "actor": r.actor,
                "decision": r.decision,
                "at": r.at,
                "recordHash": r.record_hash,
            }
            for r in self.audit.query(domain=domain, entity_id=entity_id)
        ]

    # -- helpers ------------------------------------------------------------
    def _require_consent(self, session_id: str) -> ConsentRecord:
        record = self._repos.consents.get(session_id)
        if record is None:
            raise NotFoundError(f"interview session '{session_id}' not found")
        return record

    @staticmethod
    def _procedure_view(p: Procedure) -> dict:
        return {
            "procedureId": p.procedure_id,
            "title": p.title,
            "status": p.status.value,
            "version": p.version,
            "sessionId": p.session_id,
            "observation": p.knowledge.observation,
            "recommendedCheck": p.knowledge.recommended_check,
            "rationale": p.knowledge.rationale,
            "safetyBoundary": p.knowledge.safety_boundary,
            "citations": [c.to_ref() for c in p.citations],
        }
