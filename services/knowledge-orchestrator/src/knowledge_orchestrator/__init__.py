"""NovaSteel knowledge-orchestrator service.

Consent-aware Speech-to-Text and Microsoft Foundry Agent Service knowledge-capture
workflow: consent state machine, audio validation, Fast Transcription + Foundry
adapters (managed identity, no keys), restricted tool allow-list, prompt-injection
defenses, grounded citations, draft->review->approved workflow, reflection/critic
loop, multi-agent handoff, introspectable state graph, and an append-only audit log.
See README.md for the BFF route mapping and demo instructions.
"""

from .orchestrator import (
    ConflictError,
    ForbiddenError,
    KnowledgeOrchestrator,
    NotFoundError,
    OrchestratorError,
)
from .evaluation import EvaluationReport, run_evaluation
from .critic import (
    CriticResult,
    DeterministicCritic,
    ReflectionOutcome,
    run_reflection_loop,
)
from .handoff import (
    HandoffOutcome,
    ScheduleProposal,
    RULConstraint,
    execute_handoff,
)
from .state_graph import (
    StateGraph,
    IllegalTransitionError,
    build_knowledge_capture_graph,
    generate_mermaid_file,
)
from .erasure import (
    ErasureError,
    ErasureNotFoundError,
    ErasureReceipt,
    ErasureRequest,
    ErasureService,
    ErasureStatus,
    ErasureTarget,
    SubjectType,
)
from .retrieval import (
    Chunk,
    CitationError,
    HybridRetriever,
    RetrievalResult,
    ScoredChunk,
    build_decline_answer,
    enforce_answer_citations,
    extract_citations,
)
from .pii import PiiMatch, RedactionResult, detect, pseudonymize, redact
from .content_safety import (
    LocalHeuristicContentSafety,
    SafetyCategory,
    SafetyVerdict,
    screen_input,
    screen_output,
)

__version__ = "0.1.0"

__all__ = [
    "KnowledgeOrchestrator",
    "OrchestratorError",
    "NotFoundError",
    "ConflictError",
    "ForbiddenError",
    "EvaluationReport",
    "run_evaluation",
    "CriticResult",
    "DeterministicCritic",
    "ReflectionOutcome",
    "run_reflection_loop",
    "HandoffOutcome",
    "ScheduleProposal",
    "RULConstraint",
    "execute_handoff",
    "StateGraph",
    "IllegalTransitionError",
    "build_knowledge_capture_graph",
    "generate_mermaid_file",
    "ErasureService",
    "ErasureRequest",
    "ErasureReceipt",
    "ErasureTarget",
    "ErasureStatus",
    "ErasureError",
    "ErasureNotFoundError",
    "SubjectType",
    "HybridRetriever",
    "RetrievalResult",
    "ScoredChunk",
    "Chunk",
    "CitationError",
    "extract_citations",
    "enforce_answer_citations",
    "build_decline_answer",
    "PiiMatch",
    "RedactionResult",
    "detect",
    "redact",
    "pseudonymize",
    "SafetyCategory",
    "SafetyVerdict",
    "LocalHeuristicContentSafety",
    "screen_input",
    "screen_output",
]
