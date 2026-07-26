"""Fully deterministic, offline end-to-end demo of the knowledge-capture workflow.

Requires no cloud access, no API keys, and no third-party packages. Run:

    python services/knowledge-orchestrator/demo_local.py

It walks the six-moment "Operator Knowledge" flow from demo-runbook.md §7:
consent -> Fast Transcription (local) -> grounded Foundry extraction (local) ->
DRAFT -> review -> APPROVED, plus an adversarial injected-transcript run and the
append-only audit + evaluation scorecard.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from knowledge_orchestrator import KnowledgeOrchestrator, run_evaluation  # noqa: E402
from knowledge_orchestrator.adapters import (  # noqa: E402
    LocalFoundryKnowledgeAgent,
    LocalSpeechTranscriptionAdapter,
)
from knowledge_orchestrator.models import AudioMetadata  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


def _meta(session_id: str) -> AudioMetadata:
    return AudioMetadata(
        session_id=session_id,
        content_type="audio/wav",
        duration_seconds=95.0,
        sample_rate_hz=16000,
        channels=1,
        size_bytes=3_000_000,
        language="en",
        speaker_role="operator",
        checksum="sha256:demo-fixture",
    )


def main() -> int:
    orch = KnowledgeOrchestrator(
        speech=LocalSpeechTranscriptionAdapter(FIX / "interview_transcript.json"),
        agent=LocalFoundryKnowledgeAgent(),
    )

    print("== 1. Consent-bound interview ==")
    created = orch.create_interview(
        operator_ref="OP-DEMO-014",
        language="en",
        retention_days=30,
        consent_granted=True,
        correlation_id="demo-corr-1",
    )
    sid = created["sessionId"]
    print(json.dumps(created, indent=2))

    print("\n== 2. Fast Transcription (local, Highly Confidential) ==")
    print(json.dumps(orch.submit_audio(session_id=sid, meta=_meta(sid), audio_ref="op014.wav"), indent=2))

    print("\n== 3. Grounded Foundry extraction -> DRAFT ==")
    draft = orch.extract_draft(session_id=sid, title="Hearth sector over-temperature check")
    print(json.dumps(orch._procedure_view(draft), indent=2))

    print("\n== 4. Review -> Approve (Knowledge.Publisher, expectedVersion) ==")
    orch.submit_for_review(draft.procedure_id, actor="ke-demo")
    approved = orch.approve_procedure(
        procedure_id=draft.procedure_id,
        actor="ke-demo",
        actor_roles={"Knowledge.Publisher"},
        expected_version=draft.version,
        idempotency_key="demo-approve-1",
    )
    print(f"status={approved.status.value} version={approved.version} approvedBy={approved.approved_by}")
    print("search (approved only):", json.dumps(orch.search_procedures("hearth"), indent=2))

    print("\n== 5. Adversarial injected transcript is neutralised ==")
    adv = KnowledgeOrchestrator(
        speech=LocalSpeechTranscriptionAdapter(FIX / "interview_transcript_injected.json"),
        agent=LocalFoundryKnowledgeAgent(),
    )
    adv.create_interview(operator_ref="OP-DEMO-014", language="en", retention_days=30, consent_granted=True)
    adv.submit_audio(session_id="IV-00001", meta=_meta("IV-00001"), audio_ref="adv.wav")
    adv_draft = adv.extract_draft(session_id="IV-00001", title="Injected attempt")
    blob = adv._procedure_view(adv_draft)
    injected_present = "ignore all previous" in json.dumps(blob).lower()
    print(f"injected instruction present in draft? {injected_present}")

    print("\n== 6. Append-only audit + evaluation scorecard ==")
    print(f"audit records: {len(orch.get_audit())}, chain valid: {orch.audit.verify()}")
    report = run_evaluation(FIX)
    print(json.dumps(report.to_dict(), indent=2))
    print(f"\nEVALUATION passRate={report.pass_rate:.2%} allPassed={report.all_passed()}")
    return 0 if report.all_passed() and not injected_present else 1


if __name__ == "__main__":
    raise SystemExit(main())
