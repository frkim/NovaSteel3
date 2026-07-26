"""Production Foundry Agent Service adapter (Entra managed identity, no keys).

Demonstrates the required pattern from solution-architecture.md §4.3 item 1 and
api-contracts.md §10: the agent is reached with ``DefaultAzureCredential`` (managed
identity) and a project/agent identity distinct from any user token. The agent runs
under the safety meta-prompt with the transcript spotlighted as untrusted data, and
is granted only its allow-listed tools. The ``azure-ai-projects``/``azure-identity``
SDKs are imported lazily; nothing here is required for the offline demo or tests.
Install SDKs only from the approved feed (see pip.conf).
"""

from __future__ import annotations

from typing import Optional

from ..models import Transcript
from .. import prompt_defense
from ..tools import ToolRegistry
from .base import AgentResult, FoundryAgentAdapter

# Entra token scope for Azure AI Foundry (Cognitive Services) data-plane access.
FOUNDRY_SCOPE = "https://ai.azure.com/.default"


class AzureFoundryKnowledgeAgent(FoundryAgentAdapter):
    """Knowledge-capture agent backed by Microsoft Foundry Agent Service."""

    agent_name = "knowledge-capture"

    def __init__(
        self,
        project_endpoint: str,
        agent_id: str,
        credential: Optional[object] = None,
    ):
        if not project_endpoint or not agent_id:
            raise ValueError("project_endpoint and agent_id are required")
        self.project_endpoint = project_endpoint
        self.agent_id = agent_id
        self._credential = credential
        # The agent may only use its allow-listed tools (least privilege).
        self.registry = ToolRegistry(self.agent_name)

    def _client(self):  # pragma: no cover - requires azure SDKs
        from azure.ai.projects import AIProjectClient

        credential = self._credential or _default_credential()
        return AIProjectClient(endpoint=self.project_endpoint, credential=credential)

    def extract_draft(self, task: str, transcript: Transcript) -> AgentResult:  # pragma: no cover - requires cloud
        prompt = prompt_defense.build_grounded_prompt(
            user_task=task,
            untrusted_context="\n".join(
                f"[{s.segment_id}] {s.speaker}: {s.text}" for s in transcript.segments
            ),
        )
        client = self._client()
        run = client.agents.create_and_process_run(
            agent_id=self.agent_id,
            instructions=prompt_defense.SAFETY_META_PROMPT,
            additional_messages=[{"role": "user", "content": prompt}],
        )
        # Mapping the structured tool-output run into ExtractedKnowledge is deployment
        # specific and validated at the integration gate; the offline adapter provides
        # the deterministic reference behaviour for tests and the demo.
        raise NotImplementedError(
            "wire structured run output to ExtractedKnowledge at the integration gate"
        )


def _default_credential():  # pragma: no cover - requires azure-identity
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()
