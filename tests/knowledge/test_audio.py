import pytest

from knowledge_orchestrator import audio as a
from knowledge_orchestrator import consent as c


def _granted(session_id="IV-00001", language="en"):
    rec = c.create_session(
        session_id=session_id,
        operator_ref="OP-1",
        language=language,
        speaker_role="operator",
        retention_days=30,
    )
    return c.grant(rec)


def test_valid_audio_passes(audio_meta):
    a.validate_audio_metadata(audio_meta(), _granted())


def test_rejects_unconsented_audio(audio_meta):
    pending = c.create_session(
        session_id="IV-00001",
        operator_ref="OP-1",
        language="en",
        speaker_role="operator",
        retention_days=30,
    )
    with pytest.raises(a.AudioValidationError) as exc:
        a.validate_audio_metadata(audio_meta(), pending)
    assert any("does not permit audio capture" in e for e in exc.value.errors)


def test_rejects_unsupported_content_type(audio_meta):
    with pytest.raises(a.AudioValidationError) as exc:
        a.validate_audio_metadata(audio_meta(content_type="video/mp4"), _granted())
    assert any("content_type" in e for e in exc.value.errors)


def test_rejects_session_mismatch(audio_meta):
    with pytest.raises(a.AudioValidationError) as exc:
        a.validate_audio_metadata(audio_meta(session_id="OTHER"), _granted())
    assert any("does not match consent session" in e for e in exc.value.errors)


def test_rejects_language_mismatch(audio_meta):
    with pytest.raises(a.AudioValidationError) as exc:
        a.validate_audio_metadata(audio_meta(language="fr"), _granted(language="en"))
    assert any("language" in e for e in exc.value.errors)


@pytest.mark.parametrize(
    "field,value,needle",
    [
        ("duration_seconds", 0, "duration_seconds"),
        ("duration_seconds", 10_000, "duration_seconds"),
        ("sample_rate_hz", 4000, "sample_rate_hz"),
        ("channels", 0, "channels"),
        ("size_bytes", 0, "size_bytes"),
        ("checksum", "", "checksum"),
    ],
)
def test_rejects_bad_envelope(audio_meta, field, value, needle):
    with pytest.raises(a.AudioValidationError) as exc:
        a.validate_audio_metadata(audio_meta(**{field: value}), _granted())
    assert any(needle in e for e in exc.value.errors)


def test_recommended_quality(audio_meta):
    assert a.is_recommended_quality(audio_meta(sample_rate_hz=16000)) is True
    assert a.is_recommended_quality(audio_meta(sample_rate_hz=8000)) is False
