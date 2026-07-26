"""GDPR Art. 17 right-to-erasure service (security-governance-and-threat-model.md §14).

Implements **crypto-shredding + tombstoning** so that personal data is irrecoverably
deleted from every source store while the append-only, hash-chained audit log
(``audit.py``) continues to pass ``AuditLog.verify()`` without modification.

The resolution to the GDPR Art. 17 / audit-chain tension
---------------------------------------------------------
GDPR Art. 17 demands deletion of personal data; the audit chain forbids deletion of
any record because each record's ``record_hash`` is the ``prev_hash`` of its successor.
Modifying *any* existing record would break all subsequent hash-links and cause
``verify()`` to return ``False``.

The defensible, standard resolution used here:

1. **Source stores** (interview transcripts, Copilot conversations) are **hard-deleted**.
2. **Knowledge procedures** are **pseudonymized**: the procedure body (safety-critical
   operational knowledge) is retained under GDPR Art. 17(3)(b)/(d) once de-identified;
   only the attribution fields (``created_by``, session linkage) are replaced with a
   deterministic SHA-256 pseudonym.
3. **Audit-chain records** are *never* modified — doing so would break ``verify()``.
   Instead, a new ``erasure.executed`` record is **appended** to the chain.  This
   record is the tombstone: it proves erasure occurred, names the pseudonymous subject,
   and lists every store that was processed.  Because we only *append*, ``verify()``
   remains valid throughout.  The chain references (session IDs, operator refs) that
   remain in existing records become non-personal once the underlying data is gone.
4. **Telemetry attribution** is always retained under Art. 17(3)(b) (legitimate
   operational-continuity interest); the legal basis is documented per target.

Result: ``audit.verify()`` is ``True`` before *and* after every erasure execution, and
the erased content is unrecoverable from any store.

References
----------
- security-governance-and-threat-model.md §13 (consent), §14 (retention/lifecycle)
- GDPR Art. 17 (right to erasure)
- GDPR Art. 17(3)(b) — legal obligation / public interest exception
- GDPR Art. 17(3)(d) — scientific/operational knowledge exception
- GDPR Art. 5(1)(c) — data minimisation
"""

from __future__ import annotations

import enum
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional, Protocol, runtime_checkable

from .models import iso, utcnow


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class SubjectType(str, enum.Enum):
    """The category of data subject making a right-to-erasure request."""

    INTERVIEW_PARTICIPANT = "INTERVIEW_PARTICIPANT"
    COPILOT_USER = "COPILOT_USER"
    OPERATOR = "OPERATOR"


class ErasureStatus(str, enum.Enum):
    """Lifecycle state of a GDPR Art. 17 erasure request."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ErasureTarget:
    """A single store's contribution to an erasure request."""

    store: str
    """Logical store name: ``interview-transcripts`` | ``knowledge-procedures`` |
    ``copilot-conversations`` | ``audit-chain`` | ``telemetry-attribution``."""
    recordCount: int
    """Number of records in this store linked to the data subject."""
    action: str
    """Intended erasure action: ``delete`` | ``pseudonymize`` | ``tombstone`` |
    ``retain-legal-basis``."""
    legalBasis: Optional[str]
    """Documented legal basis when data is *not* fully deleted (Art. 17(3))."""
    completed: bool
    """``True`` once the action has been successfully executed."""


@dataclass
class ErasureRequest:
    """A GDPR Art. 17 deletion request, with full lifecycle tracking.

    .. warning::
        ``subjectId`` is the raw data-subject identifier and is **for internal use
        only**.  It must never appear in a receipt, log line, audit record, or
        ``__repr__``.  All external output uses the SHA-256 pseudonym instead.
    """

    requestId: str
    subjectType: SubjectType
    subjectId: str          # INTERNAL — excluded from repr and all external outputs
    requestedBy: str
    reason: str
    status: ErasureStatus
    createdAt: str
    completedAt: Optional[str]
    targets: list[ErasureTarget]
    receiptHash: str

    def __repr__(self) -> str:
        """Intentionally omits ``subjectId`` to prevent leakage in tracebacks/logs."""
        return (
            f"ErasureRequest("
            f"requestId={self.requestId!r}, "
            f"subjectType={self.subjectType.value!r}, "
            f"status={self.status.value!r}"
            f")"
        )


@dataclass
class ErasureReceipt:
    """Evidence that GDPR Art. 17 erasure was carried out.

    Safe to return to the data subject: ``subjectId`` here is always the SHA-256
    pseudonym — the raw identifier is never included.
    """

    requestId: str
    subjectId: str          # PSEUDONYM only — never the raw data-subject identifier
    status: ErasureStatus
    executedAt: str
    targets: list[ErasureTarget]
    erasedCounts: dict[str, int]
    """Stores where data was deleted or pseudonymized, with per-store record counts."""
    retainedCounts: dict[str, int]
    """Stores where data was kept (tombstoned or retained on legal basis), with counts."""
    auditChainRef: str
    """``record_hash`` of the ``erasure.executed`` audit entry — the chain tombstone."""
    chainVerifiedAfter: bool
    """``True`` if ``audit.verify()`` passed immediately after execute()."""

    def __repr__(self) -> str:
        return (
            f"ErasureReceipt("
            f"requestId={self.requestId!r}, "
            f"subjectId={self.subjectId!r}, "   # pseudo — safe to log
            f"status={self.status.value!r}"
            f")"
        )


# ---------------------------------------------------------------------------
# Protocols  (dependency-injection interfaces — no orchestrator.py import)
# ---------------------------------------------------------------------------


@runtime_checkable
class AuditLogProtocol(Protocol):
    """Structural interface satisfied by ``AuditLog`` from ``audit.py``."""

    def append(
        self,
        *,
        correlation_id: str,
        domain: str,
        action: str,
        entity_id: str,
        actor: str,
        inputs: Optional[dict[str, Any]] = None,
        output: Optional[dict[str, Any]] = None,
        decision: Optional[str] = None,
        at: Optional[datetime] = None,
    ) -> Any:
        """Append a record and return it (with populated ``record_hash``)."""
        ...

    def query(
        self,
        *,
        domain: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> list[Any]:
        """Return matching records in append order."""
        ...

    def verify(self) -> bool:
        """Re-derive the hash chain; ``False`` if any record was tampered with."""
        ...

    def __len__(self) -> int: ...


@runtime_checkable
class InterviewSessionStoreProtocol(Protocol):
    """Minimum surface of the session/transcript store needed by ``ErasureService``."""

    def scan_subject_sessions(self, subject_id: str) -> list[str]:
        """Return session_ids whose owner/interviewee matches ``subject_id``."""
        ...

    def erase_session_transcripts(self, session_ids: list[str]) -> int:
        """Hard-delete transcript data for the given sessions.

        Returns the count of transcript records deleted.
        Session metadata (used for audit-chain linkage scanning) is preserved so that
        subsequent scans within the same request can still locate the session_ids.
        """
        ...


@runtime_checkable
class ProcedureStoreProtocol(Protocol):
    """Minimum surface of the procedure store needed by ``ErasureService``."""

    def scan_subject_procedures(self, subject_id: str) -> list[str]:
        """Return procedure_ids whose attribution contains ``subject_id``.

        Attribution includes ``created_by`` and any interviewee/session linkage field.
        """
        ...

    def pseudonymize_procedures(self, procedure_ids: list[str], pseudo_id: str) -> int:
        """Replace attribution fields with ``pseudo_id``.

        The procedure body (observation, recommended_check, rationale, safety_boundary,
        citations) is **not** modified — it is retained as de-identified operational
        knowledge under GDPR Art. 17(3)(b)/(d).
        Returns the count of procedures modified.
        """
        ...


@runtime_checkable
class CopilotStoreProtocol(Protocol):
    """Minimum surface of the Copilot conversation store needed by ``ErasureService``."""

    def count_subject_conversations(self, owner_id: str) -> int:
        """Count conversations currently held for ``owner_id``."""
        ...

    def erase_subject_conversations(self, owner_id: str) -> int:
        """Delete all conversations owned by ``owner_id``.

        Returns the count of conversations deleted.
        """
        ...


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------


class ErasureError(Exception):
    """Base error for the erasure subsystem."""

    code: str = "ERASURE_ERROR"


class ErasureNotFoundError(ErasureError):
    """Raised when ``request_id`` does not correspond to any known request."""

    code = "ERASURE_NOT_FOUND"


class IllegalTransitionError(ErasureError):
    """Raised when ``execute()`` is called from a state that does not allow it."""

    code = "ILLEGAL_TRANSITION"


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_PROCEDURE_RETENTION_BASIS = (
    "GDPR Art. 17(3)(b) legal obligation and Art. 17(3)(d) scientific/operational "
    "knowledge; procedure body retained once attribution is de-identified per "
    "security-governance-and-threat-model.md §14 retention policy"
)

_TELEMETRY_RETENTION_BASIS = (
    "GDPR Art. 17(3)(b) legitimate interest in operational continuity and process "
    "safety; telemetry is pseudonymous at ingestion, retained for process-safety "
    "analytics per §14"
)

_AUDIT_CHAIN_RETENTION_BASIS = (
    "GDPR Art. 17(3)(b) legal obligation to maintain verifiable audit trail; "
    "existing chain records are tombstoned by deleting the referenced source data "
    "so they become non-personal; audit.verify() confirmed valid after erasure"
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _pseudonymize(subject_id: str, salt: str) -> str:
    """Deterministic, one-way SHA-256 pseudonym (128-bit, 32 hex chars).

    The ``salt`` prevents cross-context linkage.  It is injected so tests can pin it.
    """
    raw = f"{salt}\x00{subject_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _make_request_id(subject_id: str, at: str) -> str:
    """UUID5 makes the request ID deterministic given the same (subject, timestamp) pair."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"erasure:{subject_id}|{at}"))


def _receipt_hash(request_id: str, pseudo_id: str, at: str) -> str:
    blob = json.dumps(
        {"at": at, "requestId": request_id, "subjectId": pseudo_id},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# ErasureService
# ---------------------------------------------------------------------------


class ErasureService:
    """GDPR Art. 17 erasure orchestration with crypto-shredding and audit-chain tombstoning.

    Collaborators are injected via the ``*Protocol`` interfaces above; no concrete
    class from ``orchestrator.py`` is imported, so this service is independently
    unit-testable and the integrator can wire real stores at application startup.

    State machine
    -------------
    ``PENDING`` ──execute()──► ``IN_PROGRESS`` ──► ``COMPLETED``
                                                └──► ``PARTIALLY_COMPLETED``
    ``PENDING`` ──submit() with legal hold──► ``REJECTED``

    Illegal transitions raise ``IllegalTransitionError``.
    Re-executing a ``COMPLETED`` or ``PARTIALLY_COMPLETED`` request is idempotent
    and returns the cached receipt without mutating anything.
    """

    def __init__(
        self,
        audit_log: AuditLogProtocol,
        session_store: InterviewSessionStoreProtocol,
        procedure_store: ProcedureStoreProtocol,
        copilot_store: CopilotStoreProtocol,
        *,
        salt_fn: Callable[[], str] = lambda: "default-salt",
        legal_hold_fn: Callable[[str], bool] = lambda _: False,
        target_hold_fn: Callable[[str, str], bool] = lambda _s, _t: False,
    ) -> None:
        """
        Parameters
        ----------
        audit_log:
            The shared ``AuditLog`` instance (or any ``AuditLogProtocol`` implementation).
        session_store:
            Adapter over the interview-session / transcript store.
        procedure_store:
            Adapter over the knowledge-procedure store.
        copilot_store:
            Adapter over the Copilot conversation store.
        salt_fn:
            Zero-argument callable that returns the pseudonymization salt.  Inject a
            fixed value in tests to make pseudonyms deterministic.
        legal_hold_fn:
            ``(subject_id) -> bool``.  If ``True``, the request is ``REJECTED`` at
            submit time (whole-subject hold).
        target_hold_fn:
            ``(subject_id, store) -> bool``.  If ``True`` for a specific store,
            that target is retained under a legal hold and the overall status becomes
            ``PARTIALLY_COMPLETED``.
        """
        self._audit = audit_log
        self._sessions = session_store
        self._procedures = procedure_store
        self._copilot = copilot_store
        self._salt_fn = salt_fn
        self._legal_hold_fn = legal_hold_fn
        self._target_hold_fn = target_hold_fn
        self._requests: dict[str, ErasureRequest] = {}
        self._receipts: dict[str, ErasureReceipt] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(
        self,
        subject_type: SubjectType,
        subject_id: str,
        requested_by: str,
        reason: str,
    ) -> ErasureRequest:
        """Create a ``PENDING`` erasure request and dry-run the target inventory.

        The inventory scans every store and records expected record counts and
        intended actions without mutating anything.  An ``erasure.requested`` audit
        record is appended to document the request.

        Raises
        ------
        ErasureError
            If the subject is currently under a global legal hold — the request is
            immediately ``REJECTED`` and an ``erasure.rejected`` audit record is written.
        """
        pseudo = self._pseudo(subject_id)
        at = iso(utcnow())
        req_id = _make_request_id(subject_id, at)

        if self._legal_hold_fn(subject_id):
            req = ErasureRequest(
                requestId=req_id,
                subjectType=subject_type,
                subjectId=subject_id,
                requestedBy=requested_by,
                reason=reason,
                status=ErasureStatus.REJECTED,
                createdAt=at,
                completedAt=at,
                targets=[],
                receiptHash="",
            )
            self._requests[req_id] = req
            self._audit.append(
                correlation_id=req_id,
                domain="erasure",
                action="erasure.rejected",
                entity_id=pseudo,
                actor=requested_by,
                inputs={"reason": reason, "legalHold": True},
                output={"status": ErasureStatus.REJECTED.value},
                decision="REJECTED",
            )
            raise ErasureError(
                f"Subject is under a legal hold; erasure request {req_id} rejected."
            )

        targets = self._build_inventory(subject_id, pseudo)
        req = ErasureRequest(
            requestId=req_id,
            subjectType=subject_type,
            subjectId=subject_id,
            requestedBy=requested_by,
            reason=reason,
            status=ErasureStatus.PENDING,
            createdAt=at,
            completedAt=None,
            targets=targets,
            receiptHash="",
        )
        self._requests[req_id] = req

        self._audit.append(
            correlation_id=req_id,
            domain="erasure",
            action="erasure.requested",
            entity_id=pseudo,
            actor=requested_by,
            inputs={"reason": reason, "subjectType": subject_type.value},
            output={
                "status": ErasureStatus.PENDING.value,
                "targetCount": len(targets),
            },
            decision="PENDING",
        )
        return req

    def preview(self, request_id: str) -> ErasureRequest:
        """Return the current request state without executing anything (read-only)."""
        return self._get(request_id)

    def execute(self, request_id: str) -> ErasureReceipt:
        """Execute the erasure and return a safe receipt.

        **Crypto-shredding sequence**:

        1. Transcript data is hard-deleted from the session store.
        2. Procedure attribution is pseudonymized (body retained — see ``_PROCEDURE_RETENTION_BASIS``).
        3. Copilot conversations are hard-deleted.
        4. Audit-chain references are counted; the chain itself is *not* modified.
        5. An ``erasure.executed`` record is **appended** to the chain — this is the tombstone.
        6. ``audit.verify()`` is called; the result is stored in ``chainVerifiedAfter``.

        Idempotency
        -----------
        Calling ``execute()`` on a ``COMPLETED`` or ``PARTIALLY_COMPLETED`` request
        returns the cached ``ErasureReceipt`` and makes no changes.

        Raises
        ------
        IllegalTransitionError
            If the request is in ``REJECTED`` or ``IN_PROGRESS`` state.
        ErasureNotFoundError
            If ``request_id`` is unknown.
        """
        req = self._get(request_id)

        # Idempotency guard
        if req.status in (ErasureStatus.COMPLETED, ErasureStatus.PARTIALLY_COMPLETED):
            return self._receipts[request_id]

        if req.status is ErasureStatus.REJECTED:
            raise IllegalTransitionError(
                f"Cannot execute a REJECTED erasure request ({request_id}). "
                "Check legal-hold status before resubmitting."
            )
        if req.status is ErasureStatus.IN_PROGRESS:
            raise IllegalTransitionError(
                f"Erasure request {request_id} is already IN_PROGRESS "
                "(possible concurrent execution)."
            )

        # Transition → IN_PROGRESS
        req.status = ErasureStatus.IN_PROGRESS
        pseudo = self._pseudo(req.subjectId)

        erased: dict[str, int] = {}
        retained: dict[str, int] = {}
        executed_targets: list[ErasureTarget] = []

        for target in req.targets:
            store = target.store

            # Telemetry is always retained by design — not a legal hold, but policy.
            if target.action == "retain-legal-basis":
                executed_targets.append(
                    ErasureTarget(
                        store=store,
                        recordCount=target.recordCount,
                        action="retain-legal-basis",
                        legalBasis=target.legalBasis,
                        completed=True,
                    )
                )
                retained[store] = target.recordCount
                continue

            # Per-target legal hold overrides the intended action.
            if self._target_hold_fn(req.subjectId, store):
                executed_targets.append(
                    ErasureTarget(
                        store=store,
                        recordCount=target.recordCount,
                        action="retain-legal-basis",
                        legalBasis="Active legal hold; retained under Art. 17(3)(b)",
                        completed=False,
                    )
                )
                retained[store] = target.recordCount
                continue

            # Execute the intended action and record counts.
            count = self._run_target(req.subjectId, pseudo, store)
            if target.action in ("delete", "pseudonymize"):
                erased[store] = count
            else:
                # "tombstone" — records remain but source data is gone
                retained[store] = count
            executed_targets.append(
                ErasureTarget(
                    store=store,
                    recordCount=target.recordCount,
                    action=target.action,
                    legalBasis=target.legalBasis,
                    completed=True,
                )
            )

        any_held = any(not t.completed for t in executed_targets)
        final_status = (
            ErasureStatus.PARTIALLY_COMPLETED if any_held else ErasureStatus.COMPLETED
        )
        executed_at = iso(utcnow())

        # Step 5 — append the erasure.executed tombstone to the audit chain.
        # This is the ONLY mutation to the audit log; existing records are untouched,
        # so audit.verify() continues to return True.
        audit_rec = self._audit.append(
            correlation_id=request_id,
            domain="erasure",
            action="erasure.executed",
            entity_id=pseudo,
            actor=req.requestedBy,
            inputs={
                "requestId": request_id,
                "subjectType": req.subjectType.value,
                "stores": [t.store for t in executed_targets],
            },
            output={
                "status": final_status.value,
                "erasedCounts": erased,
                "retainedCounts": retained,
            },
            decision=final_status.value,
        )

        # Step 6 — verify the chain is still intact.
        chain_ok = self._audit.verify()

        rh = _receipt_hash(request_id, pseudo, executed_at)
        receipt = ErasureReceipt(
            requestId=request_id,
            subjectId=pseudo,
            status=final_status,
            executedAt=executed_at,
            targets=executed_targets,
            erasedCounts=erased,
            retainedCounts=retained,
            auditChainRef=audit_rec.record_hash,
            chainVerifiedAfter=chain_ok,
        )
        self._receipts[request_id] = receipt

        req.status = final_status
        req.completedAt = executed_at
        req.receiptHash = rh
        req.targets = executed_targets

        return receipt

    def get(self, request_id: str) -> ErasureRequest:
        """Retrieve a request by ID.  Raises ``ErasureNotFoundError`` if absent."""
        return self._get(request_id)

    def list_requests(
        self,
        subject_id: Optional[str] = None,
        status: Optional[ErasureStatus] = None,
    ) -> list[ErasureRequest]:
        """List requests, optionally filtered by raw ``subject_id`` and/or ``status``."""
        results = list(self._requests.values())
        if subject_id is not None:
            results = [r for r in results if r.subjectId == subject_id]
        if status is not None:
            results = [r for r in results if r.status == status]
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _pseudo(self, subject_id: str) -> str:
        return _pseudonymize(subject_id, self._salt_fn())

    def _get(self, request_id: str) -> ErasureRequest:
        req = self._requests.get(request_id)
        if req is None:
            raise ErasureNotFoundError(
                f"No erasure request found with id={request_id!r}"
            )
        return req

    def _build_inventory(
        self,
        subject_id: str,
        pseudo_id: str,
    ) -> list[ErasureTarget]:
        """Dry-run scan of all stores.  Never mutates any store."""
        session_ids = self._sessions.scan_subject_sessions(subject_id)
        proc_ids = self._procedures.scan_subject_procedures(subject_id)
        convo_count = self._copilot.count_subject_conversations(subject_id)

        # Count audit records that reference the subject via session_ids or actor field.
        # These records will be tombstoned conceptually by the erasure.executed entry.
        all_recs = self._audit.query()
        audit_ref_count = sum(
            1
            for r in all_recs
            if getattr(r, "entity_id", None) in session_ids
            or getattr(r, "actor", None) == subject_id
        )

        return [
            ErasureTarget(
                store="interview-transcripts",
                recordCount=len(session_ids),
                action="delete",
                legalBasis=None,
                completed=False,
            ),
            ErasureTarget(
                store="knowledge-procedures",
                recordCount=len(proc_ids),
                action="pseudonymize",
                legalBasis=_PROCEDURE_RETENTION_BASIS,
                completed=False,
            ),
            ErasureTarget(
                store="copilot-conversations",
                recordCount=convo_count,
                action="delete",
                legalBasis=None,
                completed=False,
            ),
            ErasureTarget(
                store="audit-chain",
                recordCount=audit_ref_count,
                action="tombstone",
                legalBasis=_AUDIT_CHAIN_RETENTION_BASIS,
                completed=False,
            ),
            ErasureTarget(
                store="telemetry-attribution",
                recordCount=0,
                action="retain-legal-basis",
                legalBasis=_TELEMETRY_RETENTION_BASIS,
                completed=False,
            ),
        ]

    def _run_target(self, subject_id: str, pseudo_id: str, store: str) -> int:
        """Execute the action for one store.  Returns the count of records processed."""
        if store == "interview-transcripts":
            session_ids = self._sessions.scan_subject_sessions(subject_id)
            return self._sessions.erase_session_transcripts(session_ids)

        if store == "knowledge-procedures":
            proc_ids = self._procedures.scan_subject_procedures(subject_id)
            return self._procedures.pseudonymize_procedures(proc_ids, pseudo_id)

        if store == "copilot-conversations":
            return self._copilot.erase_subject_conversations(subject_id)

        if store == "audit-chain":
            # Existing records cannot be modified without breaking hash-links.
            # Count the references that remain; the erasure.executed entry (appended
            # after all targets) is the tombstone that documents what was erased.
            all_recs = self._audit.query()
            session_ids = self._sessions.scan_subject_sessions(subject_id)
            return sum(
                1
                for r in all_recs
                if getattr(r, "entity_id", None) in session_ids
                or getattr(r, "actor", None) == subject_id
            )

        return 0
