from knowledge_orchestrator.audit import AuditLog


def _log_two(log):
    log.append(
        correlation_id="c1",
        domain="knowledge",
        action="draft.create",
        entity_id="PROC-1",
        actor="agent",
        inputs={"sessionId": "IV-1"},
        output={"status": "DRAFT"},
        decision="DRAFT_CREATED",
    )
    log.append(
        correlation_id="c2",
        domain="knowledge",
        action="procedure.approve",
        entity_id="PROC-1",
        actor="ke",
        output={"version": 2},
        decision="APPROVED",
    )


def test_append_and_query():
    log = AuditLog()
    _log_two(log)
    assert len(log) == 2
    rows = log.query(domain="knowledge", entity_id="PROC-1")
    assert [r.action for r in rows] == ["draft.create", "procedure.approve"]


def test_hash_chain_valid():
    log = AuditLog()
    _log_two(log)
    assert log.verify() is True
    assert log.query()[0].prev_hash == "0" * 64
    assert log.query()[1].prev_hash == log.query()[0].record_hash


def test_tamper_detected():
    log = AuditLog()
    _log_two(log)
    # Simulate tampering by mutating the internal list (append-only API forbids this).
    tampered = log.query()[0]
    object.__setattr__(tampered, "action", "hacked")
    log._records[0] = tampered
    assert log.verify() is False


def test_sensitive_fields_redacted():
    log = AuditLog()
    rec = log.append(
        correlation_id="c",
        domain="knowledge",
        action="interview.transcribe",
        entity_id="IV-1",
        actor="mi",
        inputs={"audio": "s3://bucket/op.wav", "language": "en"},
        output={"transcript": "secret words"},
    )
    assert rec.inputs["audio"] == "[REDACTED]"
    assert rec.inputs["language"] == "en"
    assert rec.output["transcript"] == "[REDACTED]"


def test_no_update_or_delete_api():
    log = AuditLog()
    assert not hasattr(log, "update")
    assert not hasattr(log, "delete")
