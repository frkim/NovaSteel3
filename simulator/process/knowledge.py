"""Synthetic operator-knowledge capture dataset (docs section 3.7).

All content is composed from an approved synthetic phrase library
(``config.KNOWLEDGE_FACT_TEMPLATES``). No real operator names, voices, or
free text modeled on real people is ever generated. Captured guidance is
always emitted as a draft requiring expert review.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from simulator import config
from simulator.clock import iso


def build_interview_session(*, interview_id: str, plant_id: str, operator_id: str,
                             role: str, scenario_id: str, start_ts: datetime, rng) -> dict:
    return {
        "interview_id": interview_id,
        "operator_id": operator_id,
        "role": role,
        "plant_id": plant_id,
        "language": "en",
        "consent_state": "SYNTHETIC-CONSENT-GRANTED",
        "scenario_id": scenario_id,
        "start_ts": iso(start_ts),
        "data_classification": config.DATA_CLASSIFICATION,
        "privacy_label": config.PRIVACY_LABEL,
    }


def build_knowledge_segments(*, interview_id: str, start_ts: datetime, sector: str, rng) -> list[dict]:
    segments = []
    ts = start_ts
    for i, fact_template in enumerate(config.KNOWLEDGE_FACT_TEMPLATES):
        ts = ts + timedelta(seconds=rng.uniform(20, 60))
        segment_id = f"{interview_id}-SEG-{i:02d}"
        transcript = fact_template["trigger"].format(sector=sector)
        segments.append({
            "interview_id": interview_id,
            "segment_id": segment_id,
            "segment_ts": iso(ts),
            "transcript": f"Demo synthetic transcript: {transcript}.",
            "stt_confidence": round(rng.uniform(0.82, 0.99), 3),
            "speaker_role": "Furnace Operator",
            "knowledge_fact": {
                "trigger": fact_template["trigger"].format(sector=sector),
                "observation": fact_template["observation"].format(sector=sector),
                "action": fact_template["action"].format(sector=sector),
                "rationale": fact_template["rationale"].format(sector=sector),
                "cautions": fact_template["cautions"],
                "source_segment": segment_id,
            },
            "procedure_draft": {
                "steps": [
                    fact_template["observation"].format(sector=sector),
                    fact_template["action"].format(sector=sector),
                ],
                "prerequisites": ["Confirm sensor health before acting on the observation."],
                "safety_boundary": "Draft guidance only; not a control instruction.",
                "reviewer_status": "PENDING_EXPERT_REVIEW",
                "citations": [f"event:{segment_id}"],
            },
            "data_classification": config.DATA_CLASSIFICATION,
            "privacy_label": config.PRIVACY_LABEL,
        })
    return segments
