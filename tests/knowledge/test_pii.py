"""Tests for PII detection, redaction, and pseudonymization (pii.py).

Covers: each detector kind, IBAN mod-97 accept/reject, overlapping match
resolution, unicode offset correctness, pseudonymize determinism and salt
sensitivity, PiiMatch.__repr__ never leaking raw text, and RedactionResult
structure.
"""

from __future__ import annotations

import re

import pytest

from knowledge_orchestrator.pii import (
    PiiMatch,
    RedactionResult,
    _validate_iban,
    detect,
    pseudonymize,
    redact,
)


# ---------------------------------------------------------------------------
# Email detection
# ---------------------------------------------------------------------------


def test_email_detected():
    matches = detect("Contact operator@novasteel.com for details.")
    assert any(m.kind == "email" for m in matches)


def test_email_text_correct():
    text = "Email: test@example.com is the address."
    matches = [m for m in detect(text) if m.kind == "email"]
    assert matches
    assert matches[0].text == "test@example.com"


def test_email_offsets_correct():
    text = "Email: test@example.com is the address."
    matches = [m for m in detect(text) if m.kind == "email"]
    assert matches
    m = matches[0]
    assert text[m.start : m.end] == m.text


def test_email_not_detected_on_clean_text():
    matches = detect("The hearth sector temperature is 1200 degrees.")
    assert not any(m.kind == "email" for m in matches)


# ---------------------------------------------------------------------------
# Phone detection
# ---------------------------------------------------------------------------


def test_phone_e164_detected():
    """E.164 format with spaces must be detected."""
    matches = detect("Call us at +33 1 23 45 67 89 please.")
    assert any(m.kind == "phone" for m in matches)


def test_phone_eu_local_detected():
    """EU local format (0X XX XX XX XX) must be detected."""
    matches = detect("Reach the plant at 01 23 45 67 89 extension 200.")
    assert any(m.kind == "phone" for m in matches)


def test_phone_offsets_correct():
    text = "Call +33 1 23 45 67 89 now."
    matches = [m for m in detect(text) if m.kind == "phone"]
    for m in matches:
        assert text[m.start : m.end] == m.text


# ---------------------------------------------------------------------------
# IBAN detection and mod-97 validation
# ---------------------------------------------------------------------------


def test_iban_valid_german_detected():
    """DE89370400440532013000 is a well-known valid German IBAN."""
    matches = detect("IBAN: DE89370400440532013000")
    assert any(m.kind == "iban" for m in matches)


def test_iban_invalid_check_digits_rejected():
    """Flipping check digits to 00 must invalidate the IBAN."""
    matches = detect("IBAN: DE00370400440532013000")
    assert not any(m.kind == "iban" for m in matches)


def test_validate_iban_valid():
    assert _validate_iban("DE89370400440532013000")


def test_validate_iban_invalid():
    assert not _validate_iban("DE00370400440532013000")


def test_validate_iban_too_short():
    assert not _validate_iban("DE89")


def test_iban_text_is_correct():
    text = "Payment IBAN: DE89370400440532013000 done."
    matches = [m for m in detect(text) if m.kind == "iban"]
    assert matches
    assert matches[0].text == "DE89370400440532013000"


# ---------------------------------------------------------------------------
# Employee ID detection
# ---------------------------------------------------------------------------


def test_employee_id_detected():
    matches = detect("Badge: EMP-12345 was scanned at the gate.")
    assert any(m.kind == "employee_id" for m in matches)


def test_employee_id_text_correct():
    text = "Worker EMP-99999 clocked in."
    matches = [m for m in detect(text) if m.kind == "employee_id"]
    assert matches
    assert matches[0].text == "EMP-99999"


def test_employee_id_not_matched_wrong_format():
    matches = detect("EMP-1234 is short and EMP-123456 is long.")
    emp = [m for m in matches if m.kind == "employee_id"]
    # Neither has exactly 5 digits
    assert len(emp) == 0


# ---------------------------------------------------------------------------
# IPv4 detection
# ---------------------------------------------------------------------------


def test_ipv4_detected():
    matches = detect("Server at 192.168.1.100 responded OK.")
    assert any(m.kind == "ipv4" for m in matches)


def test_ipv4_text_correct():
    text = "PLC address is 10.0.0.1 for control."
    matches = [m for m in detect(text) if m.kind == "ipv4"]
    assert matches
    assert matches[0].text == "10.0.0.1"


def test_ipv4_octet_out_of_range_not_matched():
    """999.999.999.999 has octets > 255 and must not match."""
    matches = detect("Bad address 999.999.999.999 detected.")
    assert not any(m.kind == "ipv4" for m in matches)


# ---------------------------------------------------------------------------
# Person name detection
# ---------------------------------------------------------------------------


def test_person_name_after_operator_detected():
    matches = detect("Operator: John Smith confirmed the reading.")
    assert any(m.kind == "person_name" for m in matches)


def test_person_name_text_correct():
    text = "Interviewee: Jane Doe provided the account."
    matches = [m for m in detect(text) if m.kind == "person_name"]
    assert matches
    assert matches[0].text == "Jane Doe"


def test_person_name_without_context_not_detected():
    """Standalone capitalised words must not be detected as person names."""
    matches = detect("The Furnace Control System is operational.")
    assert not any(m.kind == "person_name" for m in matches)


# ---------------------------------------------------------------------------
# Date of birth detection
# ---------------------------------------------------------------------------


def test_dob_born_on_detected():
    matches = detect("Employee born on 15/06/1985 started work.")
    assert any(m.kind == "dob" for m in matches)


def test_dob_date_of_birth_label_detected():
    matches = detect("Date of birth: 01-03-1990 as recorded.")
    assert any(m.kind == "dob" for m in matches)


def test_dob_text_is_date_only():
    """Captured text must be the date value, not the context keyword."""
    text = "Born on 22/07/1978 at the hospital."
    matches = [m for m in detect(text) if m.kind == "dob"]
    assert matches
    assert "born" not in matches[0].text.lower()
    assert "22" in matches[0].text or "1978" in matches[0].text


# ---------------------------------------------------------------------------
# Overlapping matches
# ---------------------------------------------------------------------------


def test_no_overlapping_spans_in_output():
    """resolve_overlaps must produce a non-overlapping set of matches."""
    # email "john@EMP-12345.com" and employee_id "EMP-12345" overlap;
    # longest (the full email) must win.
    text = "Mail john@EMP-12345.com for badge EMP-99999."
    matches = detect(text)
    spans = [(m.start, m.end) for m in matches]
    for i, (s1, e1) in enumerate(spans):
        for j, (s2, e2) in enumerate(spans):
            if i != j:
                assert not (s1 < e2 and e1 > s2), (
                    f"Overlapping spans at ({s1},{e1}) and ({s2},{e2})"
                )


def test_overlapping_longer_match_wins():
    """When two patterns overlap, the one with a greater span must survive."""
    text = "Contact john@EMP-12345.com today."
    matches = detect(text)
    # The email (longer) should appear; employee_id inside domain should not
    # coexist with the email match
    email_matches = [m for m in matches if m.kind == "email"]
    emp_matches = [m for m in matches if m.kind == "employee_id"]
    if email_matches and emp_matches:
        em = email_matches[0]
        ep = emp_matches[0]
        # They must not overlap in the resolved output
        assert ep.end <= em.start or ep.start >= em.end


# ---------------------------------------------------------------------------
# Unicode offsets
# ---------------------------------------------------------------------------


def test_unicode_offsets_correct():
    """Character offsets must be correct even when non-ASCII chars precede PII."""
    # 'é' is one Unicode code point; offset must be in chars, not bytes.
    text = "Réf: EMP-12345 est enregistré. Email test@example.com fin."
    matches = detect(text)
    for m in matches:
        assert text[m.start : m.end] == m.text, (
            f"Offset mismatch for {m!r}: expected {text[m.start:m.end]!r}"
        )


def test_unicode_multiple_pii_offsets():
    text = "Opér: Opérateur: Jean Dupont. Badge EMP-00001. Email x@y.com."
    matches = detect(text)
    for m in matches:
        assert text[m.start : m.end] == m.text


# ---------------------------------------------------------------------------
# PiiMatch repr
# ---------------------------------------------------------------------------


def test_pii_match_repr_does_not_leak_text():
    m = PiiMatch(kind="email", start=0, end=20, text="secret@novasteel.com")
    r = repr(m)
    assert "secret@novasteel.com" not in r


def test_pii_match_repr_contains_redacted_sentinel():
    m = PiiMatch(kind="iban", start=5, end=27, text="DE89370400440532013000")
    r = repr(m)
    assert "[REDACTED]" in r


def test_pii_match_repr_shows_kind_and_offsets():
    m = PiiMatch(kind="employee_id", start=3, end=12, text="EMP-12345")
    r = repr(m)
    assert "employee_id" in r
    assert "3" in r
    assert "12" in r


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def test_redact_removes_email():
    result = redact("Contact operator@novasteel.com for info.")
    assert "operator@novasteel.com" not in result.text
    assert "[REDACTED:EMAIL]" in result.text


def test_redact_removes_employee_id():
    result = redact("Badge EMP-12345 used.")
    assert "EMP-12345" not in result.text
    assert "[REDACTED:EMPLOYEE_ID]" in result.text


def test_redact_two_emails_counted():
    result = redact("a@b.com and c@d.com are both emails.")
    assert result.counts.get("email", 0) == 2


def test_redact_result_structure():
    result = redact("Email: test@example.com.")
    assert isinstance(result, RedactionResult)
    assert isinstance(result.text, str)
    assert isinstance(result.matches, list)
    assert isinstance(result.counts, dict)


def test_redact_clean_text_unchanged():
    text = "The hearth sector temperature is nominal."
    result = redact(text)
    assert result.text == text
    assert result.matches == []
    assert result.counts == {}


# ---------------------------------------------------------------------------
# Pseudonymization
# ---------------------------------------------------------------------------


def test_pseudonymize_deterministic():
    text = "Contact john@example.com for badge EMP-12345."
    s1 = pseudonymize(text, salt="session-abc")
    s2 = pseudonymize(text, salt="session-abc")
    assert s1 == s2


def test_pseudonymize_salt_sensitive():
    text = "Contact john@example.com."
    assert pseudonymize(text, salt="salt-aaa") != pseudonymize(text, salt="salt-bbb")


def test_pseudonymize_uses_hash_format():
    text = "Badge EMP-12345 was used."
    result = pseudonymize(text, salt="test-salt")
    assert re.search(r"\[EMPLOYEE_ID:[0-9a-f]{8}\]", result)


def test_pseudonymize_same_value_same_hash_within_session():
    """Same PII value → same pseudonym when using the same salt."""
    text = "EMP-12345 then again EMP-12345."
    result = pseudonymize(text, salt="fixed-salt")
    # Extract all hashes
    found = re.findall(r"\[EMPLOYEE_ID:([0-9a-f]{8})\]", result)
    assert len(found) == 2
    assert found[0] == found[1]
