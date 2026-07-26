"""NovaSteel knowledge-orchestrator service.

Consent-aware Speech-to-Text and Microsoft Foundry Agent Service knowledge-capture
workflow: consent state machine, audio validation, Fast Transcription + Foundry
adapters (managed identity, no keys), restricted tool allow-list, prompt-injection
defenses, grounded citations, draft->review->approved workflow, and an append-only
audit log. See README.md for the BFF route mapping and demo instructions.
"""

from .orchestrator import (
    ConflictError,
    ForbiddenError,
    KnowledgeOrchestrator,
    NotFoundError,
    OrchestratorError,
)
from .evaluation import EvaluationReport, run_evaluation

__version__ = "0.1.0"

__all__ = [
    "KnowledgeOrchestrator",
    "OrchestratorError",
    "NotFoundError",
    "ConflictError",
    "ForbiddenError",
    "EvaluationReport",
    "run_evaluation",
]
