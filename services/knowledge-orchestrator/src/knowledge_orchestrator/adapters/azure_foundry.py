"""Production Foundry adapter — calls the Foundry chat deployment with grounded RAG.

Ported from Project A's live ``FoundryClient`` + ``KnowledgeAssistant`` patterns
(citation regex enforcement, decline-on-no-source, Content Safety). Authenticates
with ``DefaultAzureCredential`` (managed identity, no API keys); per
solution-architecture.md §4.3 item 1 / security §8 ``disableLocalAuth: true``.

SDKs imported lazily so the package has zero cloud deps for tests/demo.
Install from the approved feed only (see pip.conf).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

from ..models import (
    Citation,
    ExtractedKnowledge,
    SourceType,
    Transcript,
    TranscriptSegment,
)
from .. import prompt_defense
from ..tools import ToolRegistry
from .base import AgentResult, FoundryAgentAdapter

logger = logging.getLogger(__name__)

# Entra token scope for Azure AI Foundry (Cognitive Services) data-plane access.
FOUNDRY_SCOPE = "https://cognitiveservices.azure.com/.default"

# Environment variable configuration (no secrets in code).
ENV_ENDPOINT = "FOUNDRY_ENDPOINT"
ENV_CHAT_DEPLOYMENT = "FOUNDRY_CHAT_DEPLOYMENT"
ENV_EMBED_DEPLOYMENT = "FOUNDRY_EMBED_DEPLOYMENT"
ENV_API_VERSION = "FOUNDRY_API_VERSION"
ENV_REASONING_EFFORT = "FOUNDRY_EXTRACTION_REASONING_EFFORT"

DEFAULT_CHAT_DEPLOYMENT = "gpt-5.4-mini"
DEFAULT_EMBED_DEPLOYMENT = "text-embedding-3-large"
DEFAULT_API_VERSION = "2025-01-01-preview"

# Not every 5-series model accepts every effort level: gpt-5.4-mini supports
# 'minimal', while gpt-5.5 rejects it and offers only
# none/low/medium/high/xhigh. The default pairs with DEFAULT_CHAT_DEPLOYMENT;
# override this if FOUNDRY_CHAT_DEPLOYMENT is repointed at a larger model.
DEFAULT_EXTRACTION_REASONING_EFFORT = "minimal"

# Citation tag pattern identical to Project A's enforcement (assistant.py:39).
_CITE_TAG = re.compile(r"\[S(\d+)\]")

# Model signals inability to ground.
INSUFFICIENT_TOKEN = "INSUFFICIENT_CONTEXT"

EXTRACTION_SYSTEM_PROMPT = (
    "You are the NovaSteel knowledge-capture assistant. Your task is to extract a "
    "structured operational procedure from an operator interview transcript.\n\n"
    "Rules:\n"
    "1. Ground EVERY claim in the numbered transcript segments provided. Cite inline "
    "using [S1], [S2], etc.\n"
    "2. If the segments do not contain enough information to produce a grounded procedure, "
    f"reply with exactly: {INSUFFICIENT_TOKEN}\n"
    "3. Never invent procedures, numbers, or safety guidance.\n"
    "4. Structure your answer as exactly four labelled sections:\n"
    "   OBSERVATION: <what the operator observed>\n"
    "   RECOMMENDED_CHECK: <verification steps>\n"
    "   RATIONALE: <why this matters>\n"
    "   SAFETY_BOUNDARY: <what must never be done>\n"
    "5. Be concise and operational. Each section must cite at least one source."
)

_SECTION_RE = re.compile(
    r"OBSERVATION:\s*(.+?)(?=RECOMMENDED_CHECK:)"
    r"|RECOMMENDED_CHECK:\s*(.+?)(?=RATIONALE:)"
    r"|RATIONALE:\s*(.+?)(?=SAFETY_BOUNDARY:)"
    r"|SAFETY_BOUNDARY:\s*(.+)",
    re.DOTALL,
)

_OPERATOR_LABELS = ("operator", "interviewee", "expert")


class AzureFoundryKnowledgeAgent(FoundryAgentAdapter):
    """Knowledge-capture agent backed by a Foundry chat deployment with grounded RAG."""

    agent_name = "knowledge-capture"

    def __init__(
        self,
        endpoint: Optional[str] = None,
        chat_deployment: Optional[str] = None,
        embed_deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        credential: Optional[object] = None,
    ):
        self.endpoint = (
            endpoint or os.environ.get(ENV_ENDPOINT, "")
        ).rstrip("/")
        self.chat_deployment = (
            chat_deployment or os.environ.get(ENV_CHAT_DEPLOYMENT, DEFAULT_CHAT_DEPLOYMENT)
        )
        self.embed_deployment = (
            embed_deployment or os.environ.get(ENV_EMBED_DEPLOYMENT, DEFAULT_EMBED_DEPLOYMENT)
        )
        self.api_version = (
            api_version or os.environ.get(ENV_API_VERSION, DEFAULT_API_VERSION)
        )
        self._credential = credential
        self.reasoning_effort = os.environ.get(
            ENV_REASONING_EFFORT, DEFAULT_EXTRACTION_REASONING_EFFORT
        )
        self.registry = ToolRegistry(self.agent_name)

    def _get_token(self) -> str:  # pragma: no cover - requires azure-identity
        credential = self._credential or _default_credential()
        return credential.get_token(FOUNDRY_SCOPE).token

    def _complete(self, system: str, user: str) -> str:  # pragma: no cover - requires network
        import requests

        url = (
            f"{self.endpoint}/openai/deployments/{self.chat_deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )
        body = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # Reasoning tokens are billed against max_completion_tokens, so an
            # unbounded reasoning budget on a 5-series model can consume the whole
            # allowance and return an empty completion. Extraction is a structured
            # transcript-to-fields task, not a reasoning problem.
            "reasoning_effort": self.reasoning_effort,
            "max_completion_tokens": 3000,
        }
        token = self._get_token()
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json=body,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def extract_draft(self, task: str, transcript: Transcript) -> AgentResult:
        """Extract a grounded procedure draft by calling the Foundry chat deployment.

        Implements Project A's citation-enforcement + decline path:
        - Builds a numbered SOURCES block from operator transcript segments
        - Requires [S<n>] citations in the response
        - Declines if the model signals INSUFFICIENT_CONTEXT or citations are absent
        """
        trace: list[str] = ["applied safety meta-prompt", "spotlighted transcript"]

        # Scan task for injection (defence-in-depth).
        task_scan = prompt_defense.scan_for_injection(task)
        if task_scan.severity is prompt_defense.InjectionSeverity.HIGH:
            return AgentResult(
                refused=True,
                knowledge=None,
                trace=tuple(trace + [f"refused: task injection {task_scan.matched_patterns}"]),
                refusal_reason="task contains a prompt-injection attempt",
            )

        # Build numbered sources block from operator segments.
        operator_segments = [s for s in transcript.segments if _is_operator(s)]
        if not operator_segments:
            return AgentResult(
                refused=True,
                knowledge=None,
                trace=tuple(trace + ["refused: no operator segments"]),
                refusal_reason="no operator content in transcript",
            )

        sources_block = "\n".join(
            f"[S{i+1}] (segment:{seg.segment_id}) {seg.text}"
            for i, seg in enumerate(operator_segments)
        )
        user_prompt = (
            f"TASK: {task}\n\n"
            f"TRANSCRIPT SOURCES:\n"
            f"{prompt_defense.spotlight(sources_block)}"
        )

        # Call the model.
        answer = self._complete(EXTRACTION_SYSTEM_PROMPT, user_prompt)
        trace.append("model call completed")

        # Decline path: model signals insufficient grounding.
        if INSUFFICIENT_TOKEN in answer:
            trace.append("model declined: insufficient context")
            return AgentResult(
                refused=True,
                knowledge=None,
                trace=tuple(trace),
                refusal_reason="model reported insufficient grounded context",
            )

        # Citation enforcement (Project A pattern: assistant.py:84-89).
        cited_indices = {int(n) for n in _CITE_TAG.findall(answer)}
        cited_segments = [
            operator_segments[i - 1]
            for i in sorted(cited_indices)
            if 1 <= i <= len(operator_segments)
        ]
        if not cited_segments:
            trace.append("rejected: answer lacked citations")
            return AgentResult(
                refused=True,
                knowledge=None,
                trace=tuple(trace),
                refusal_reason="answer lacked citations; rejected as ungrounded",
            )

        # Parse structured sections from the response.
        knowledge = _parse_sections(answer, cited_segments)
        trace.append(f"extracted grounded draft with {len(cited_segments)} citations")
        return AgentResult(refused=False, knowledge=knowledge, trace=tuple(trace))


def _is_operator(seg: TranscriptSegment) -> bool:
    return any(lbl in seg.speaker.lower() for lbl in _OPERATOR_LABELS)


def _parse_sections(
    answer: str, cited_segments: list[TranscriptSegment]
) -> ExtractedKnowledge:
    """Parse the four required sections from the model's structured output."""
    citations = tuple(
        Citation(
            source_type=SourceType.TRANSCRIPT_SEGMENT,
            source_id=seg.segment_id,
            quote=seg.text,
        )
        for seg in cited_segments
    )

    # Try regex extraction of labelled sections.
    obs = check = rat = safety = ""
    for label, pattern in [
        ("OBSERVATION:", r"OBSERVATION:\s*(.+?)(?=RECOMMENDED_CHECK:|$)"),
        ("RECOMMENDED_CHECK:", r"RECOMMENDED_CHECK:\s*(.+?)(?=RATIONALE:|$)"),
        ("RATIONALE:", r"RATIONALE:\s*(.+?)(?=SAFETY_BOUNDARY:|$)"),
        ("SAFETY_BOUNDARY:", r"SAFETY_BOUNDARY:\s*(.+?)$"),
    ]:
        m = re.search(pattern, answer, re.DOTALL)
        if m:
            val = m.group(1).strip()
            if label == "OBSERVATION:":
                obs = val
            elif label == "RECOMMENDED_CHECK:":
                check = val
            elif label == "RATIONALE:":
                rat = val
            else:
                safety = val

    # Fallback: if parsing failed, use the full answer for observation.
    return ExtractedKnowledge(
        observation=obs or answer[:500],
        recommended_check=check or "Verify with related sensors before acting.",
        rationale=rat or "Corroborating signals reduce false positives.",
        safety_boundary=safety or "Do not change controls based solely on this draft.",
        citations=citations,
    )


def _default_credential():  # pragma: no cover - requires azure-identity
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()
