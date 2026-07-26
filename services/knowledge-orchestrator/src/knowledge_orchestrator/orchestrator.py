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
import re
from dataclasses import dataclass, field, replace
from typing import Optional

from . import audio as audio_mod
from . import consent as consent_mod
from . import grounding
from . import procedure_workflow as wf
from .adapters.base import FoundryAgentAdapter, SpeechTranscriptionAdapter
from .adapters.local_foundry import LocalFoundryKnowledgeAgent
from .adapters.local_speech import LocalSpeechTranscriptionAdapter
from .audit import AuditLog
from .content_safety import LocalHeuristicContentSafety, screen_input, screen_output
from .pii import redact as _pii_redact
from .retrieval import (
    CitationError,
    HybridRetriever,
    _tokenize,
    build_decline_answer,
    enforce_answer_citations,
    extract_citations,
)
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


_MIN_CONTENT_TERM_LEN = 4


def _shares_content_term(query: str, text: str) -> bool:
    """True when the question and the candidate chunk share a content term.

    Guards the RRF ranking, which is rank-only and therefore always returns a
    "best" chunk even for a completely unrelated question.
    """
    q_terms = {t for t in _tokenize(query) if len(t) >= _MIN_CONTENT_TERM_LEN}
    if not q_terms:
        return False
    return bool(q_terms & set(_tokenize(text)))


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
        self._retriever = HybridRetriever()
        self._retriever_fingerprint: tuple[tuple[str, int], ...] | None = None
        self._safety = LocalHeuristicContentSafety()

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

    # -- POST /v1/knowledge/query (grounded RAG, content-safety gated) ------
    def answer_query(self, q: str, *, top_k: int = 5) -> dict:
        """Screened, hybrid-retrieval answer over APPROVED procedures only.

        Input is screened by Content Safety, PII is redacted from the echoed
        query, retrieval fuses BM25 + cosine ranks, and an ungrounded result
        yields an explicit decline rather than an unsourced answer.
        """
        query = (q or "").strip()
        verdict = screen_input(query, self._safety)
        if not verdict.allowed:
            return {
                "query": _pii_redact(query).text,
                "declined": True,
                "declineReason": "content_policy_violation",
                "answer": build_decline_answer("content_policy_violation"),
                "citations": [],
                "chunks": [],
                "blockedBy": list(verdict.blockedBy),
                "providerUsed": verdict.providerUsed,
            }

        self._reindex_retriever()
        result = self._retriever.retrieve(query, top_k=top_k)
        redacted_query = _pii_redact(query).text
        # RRF fusion is rank-only, so an off-topic query still returns a ranked
        # chunk. Require the cited chunk to share at least one content term with
        # the question; otherwise decline rather than cite an irrelevant source.
        grounded = bool(result.chunks) and _shares_content_term(
            query, result.chunks[0].chunk.text
        )
        if result.declined or not grounded:
            reason = result.declineReason or "no_grounded_source"
            return {
                "query": redacted_query,
                "declined": True,
                "declineReason": reason,
                "answer": build_decline_answer(reason),
                "citations": [],
                "chunks": [],
                "blockedBy": [],
                "providerUsed": result.providerUsed,
            }

        chunks = [
            {
                "chunkId": s.chunk.chunk_id,
                "procedureId": s.chunk.procedure_id,
                "procedureTitle": s.chunk.procedure_title,
                "section": s.chunk.section,
                "text": _pii_redact(s.chunk.text).text,
                "fusedScore": round(s.fusedScore, 6),
                "lexicalRank": s.lexicalRank,
                "semanticRank": s.semanticRank,
            }
            for s in result.chunks
        ]
        top = result.chunks[0].chunk
        # Every factual sentence must carry the marker of the chunk it came from,
        # placed before the terminal punctuation so sentence splitting stays intact.
        marker = f"[[{top.chunk_id}]]"
        sentences = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+", _pii_redact(top.text).text)
            if s.strip()
        ]
        cited = [
            f"{s[:-1].rstrip()} {marker}{s[-1]}" if s[-1] in ".!?" else f"{s} {marker}"
            for s in sentences
        ]
        answer = " ".join(cited) or f"{_pii_redact(top.text).text} {marker}"
        # Citation enforcement: an answer without a retrieved citation declines.
        try:
            enforce_answer_citations(answer, {c["chunkId"] for c in chunks})
        except CitationError:
            return {
                "query": redacted_query,
                "declined": True,
                "declineReason": "citation_enforcement_failed",
                "answer": build_decline_answer("citation_enforcement_failed"),
                "citations": [],
                "chunks": chunks,
                "blockedBy": [],
                "providerUsed": result.providerUsed,
            }
        out_verdict = screen_output(answer, self._safety)
        if not out_verdict.allowed:
            return {
                "query": redacted_query,
                "declined": True,
                "declineReason": "content_policy_violation",
                "answer": build_decline_answer("content_policy_violation"),
                "citations": [],
                "chunks": [],
                "blockedBy": list(out_verdict.blockedBy),
                "providerUsed": out_verdict.providerUsed,
            }
        return {
            "query": redacted_query,
            "declined": False,
            "declineReason": None,
            "answer": answer,
            "citations": extract_citations(answer),
            "chunks": chunks,
            "blockedBy": [],
            "providerUsed": result.providerUsed,
        }

    def _reindex_retriever(self) -> None:
        """Re-index only when the APPROVED corpus changed (cheap, deterministic)."""
        approved = [p for p in self._repos.procedures.values() if wf.is_retrievable(p)]
        fingerprint = tuple(sorted((p.procedure_id, p.version) for p in approved))
        if fingerprint == self._retriever_fingerprint:
            return
        self._retriever.index(approved)
        self._retriever_fingerprint = fingerprint

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

    # -- GDPR Art. 17 erasure adapter surface -------------------------------
    # Satisfies InterviewSessionStoreProtocol and ProcedureStoreProtocol from
    # ``knowledge_orchestrator.erasure`` without importing it (no cycle).

    def scan_subject_sessions(self, subject_id: str) -> list[str]:
        return [
            sid
            for sid, rec in self._repos.consents.items()
            if rec.operator_ref == subject_id
        ]

    def erase_session_transcripts(self, session_ids: list[str]) -> int:
        count = 0
        for sid in session_ids:
            if self._repos.transcripts.pop(sid, None) is not None:
                count += 1
        return count

    def scan_subject_procedures(self, subject_id: str) -> list[str]:
        owned_sessions = set(self.scan_subject_sessions(subject_id))
        return [
            pid
            for pid, p in self._repos.procedures.items()
            if p.created_by == subject_id
            or (p.session_id is not None and p.session_id in owned_sessions)
        ]

    def pseudonymize_procedures(self, procedure_ids: list[str], pseudo_id: str) -> int:
        count = 0
        for pid in procedure_ids:
            p = self._repos.procedures.get(pid)
            if p is None:
                continue
            self._repos.procedures[pid] = replace(
                p,
                created_by=pseudo_id,
                session_id=None,
                approved_by=(
                    pseudo_id if p.approved_by == p.created_by else p.approved_by
                ),
            )
            count += 1
        return count

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
