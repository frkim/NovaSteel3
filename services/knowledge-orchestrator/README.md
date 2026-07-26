# NovaSteel knowledge-orchestrator

Consent-aware **Speech-to-Text (STT)** and **Microsoft Foundry Agent Service**
knowledge-capture workflow for NovaSteel (Phase 0). This service coordinates the
"Operator Knowledge" flow: consent → Fast Transcription → grounded agent extraction →
draft → review → approved procedure, with append-only auditing.

> Scope guardrails: decision-support only, never a control system. Drafts and
> unapproved transcripts never become operational instruction. Every consequential
> AI output is grounded and append-only auditable. See
> `docs/architecture/solution-architecture.md` §4.3 and
> `docs/security/security-governance-and-threat-model.md` §12–13.

## Layout

```
services/knowledge-orchestrator/
├── src/knowledge_orchestrator/
│   ├── models.py              # dataclasses/enums (consent, audio, transcript, procedure, citation)
│   ├── consent.py             # consent state machine (PENDING→GRANTED→WITHDRAWN/EXPIRED)
│   ├── audio.py               # audio metadata validation bound to consent
│   ├── prompt_defense.py      # spotlighting, safety meta-prompt, injection scanner
│   ├── grounding.py           # grounded-citation enforcement (approved corpus / segments)
│   ├── tools.py               # restricted read/simulate/propose tool allow-list + registry
│   ├── procedure_workflow.py  # draft→review→approved (Knowledge.Publisher, optimistic concurrency)
│   ├── audit.py               # append-only, hash-chained decision audit
│   ├── orchestrator.py        # KnowledgeOrchestrator (BFF-facing methods)
│   ├── critic.py              # reflection/critic loop (APPROVE/REVISE per iteration)
│   ├── handoff.py             # dispatch↔RUL negotiation ports (RULScoringPort, DispatchReplanPort)
│   ├── state_graph.py         # introspectable workflow graph + Mermaid generator
│   ├── adapter_factory.py     # selects Azure vs local agent from environment
│   ├── telemetry.py           # OpenTelemetry setup, critic/handoff spans, JSON logging
│   ├── evaluation.py          # offline evaluation scorecard
│   ├── app.py                 # OPTIONAL FastAPI wiring (import-guarded)
│   ├── adapters/
│   │   ├── base.py            # SpeechTranscriptionAdapter / FoundryAgentAdapter ports
│   │   ├── azure_speech.py    # Fast Transcription via managed identity (no keys)
│   │   ├── azure_foundry.py   # live GPT-4o via managed identity, citation-enforced
│   │   ├── local_speech.py    # deterministic offline STT fake
│   │   └── local_foundry.py   # deterministic offline knowledge agent
│   └── contracts/knowledge-ai-openapi.yaml   # AI-specific contract (non-conflicting subfolder)
├── docs/workflow-state-graph.mmd  # generated Mermaid diagram of the workflow
├── fixtures/                  # transcript, injected transcript, safe prompts, attacks, approved corpus
├── demo_local.py              # fully offline end-to-end demo (no cloud, no keys)
├── Dockerfile                 # production image, protected feed only, non-root
├── requirements.txt           # pinned dependencies
├── pyproject.toml
└── pip.conf                   # approved feed only

tests/knowledge/              # focused pytest suite (offline, uses local fakes)
```

## Agent selection

`adapter_factory.create_agent()` returns the Azure GPT-4o adapter when
`FOUNDRY_ENDPOINT` is set and the Azure SDK is importable, and the local
fixture agent otherwise. An explicit `KNOWLEDGE_AGENT_MODE=local` forces
fixture mode and is checked **before** the endpoint, so the shipped image
defaults to offline-safe and a deployed environment must opt in with
`KNOWLEDGE_AGENT_MODE=azure`. The Azure adapter enforces `[S<n>]` citations and
declines on `INSUFFICIENT_CONTEXT` or missing citations rather than answering
ungrounded.

The critic loop writes `reflection.critic.iter<n>` audit records and the
handoff writes `handoff.rul_check` → `handoff.replan`, so both multi-agent
behaviours are visible in the append-only audit and as spans in Application
Insights.

## BFF route mapping (api-contracts.md §4.7, §10)

The core service is transport-agnostic; the BFF calls these methods directly, or
mounts the optional FastAPI app in `app.py`.

| BFF route | Orchestrator method | Notes |
|---|---|---|
| `POST /v1/knowledge/interviews` | `create_interview` | Consent-bound session; scope must be `knowledge-capture`. |
| (internal) submit audio | `submit_audio` | Validates consent + audio, calls Fast Transcription. |
| `GET /v1/knowledge/interviews/{id}/transcript` | `get_transcript` | `PROCESSING` until done; `Highly Confidential`. |
| (internal) extract draft | `extract_draft` | Grounded agent extraction → `DRAFT` only. |
| `GET /v1/knowledge/procedures` | `list_procedures` | Filter by `status`/`q`. |
| `GET /v1/knowledge/search` | `search_procedures` | **APPROVED only**; drafts never retrievable. |
| `POST /v1/knowledge/procedures/{id}:approve` | `approve_procedure` | `Knowledge.Publisher` + `expectedVersion` + `Idempotency-Key`. |
| `POST /v1/knowledge/procedures/{id}:reject` | `reject_procedure` | `Knowledge.Publisher`. |
| (GDPR Art. 17) withdraw consent | `withdraw_consent` | Deletes raw audio/transcript, emits directive. |
| `GET /v1/audit/decisions?domain=knowledge` | `get_audit` | Append-only, hash-chained records. |

## Security properties enforced in code

- **Consent** is captured before recording, scoped strictly to `knowledge-capture`
  (surveillance reuse refused), carries a retention deadline, and is withdrawable
  (propagates raw-audio deletion). — `consent.py`
- **Prompt-injection defense**: untrusted transcripts/tool results are *spotlighted*
  as data; a safety meta-prompt forbids obeying embedded instructions; a scanner
  flags jailbreak/override phrasing; the agent ignores injected instructions and
  refuses injected tasks. — `prompt_defense.py`, `adapters/local_foundry.py`
- **Grounding**: retrieval answers cite only approved procedures; extracted drafts
  cite only real transcript segments. — `grounding.py`
- **Restricted tools**: agents may call only `search_approved_procedures` /
  `write_draft_procedure` (knowledge) or read/forecast/simulate/propose (energy);
  approve/publish/commit/delete are never agent-callable. — `tools.py`
- **Workflow**: agents create `DRAFT` only; approval requires `Knowledge.Publisher`,
  an `expectedVersion` check (409 on stale), and yields an immutable APPROVED
  version. — `procedure_workflow.py`
- **Audit**: append-only, SHA-256 hash-chained, sensitive fields redacted. — `audit.py`
- **Identity**: Azure adapters use `DefaultAzureCredential`/managed identity and
  Entra bearer tokens — no API keys anywhere in source. — `adapters/azure_*.py`

## Run locally (offline, no cloud)

```powershell
# From the repo root. Tests and the demo use only the standard library + pytest.
python -m pytest tests\knowledge -q
python services\knowledge-orchestrator\demo_local.py
python -m knowledge_orchestrator.evaluation   # prints the evaluation scorecard JSON
```

## Package installation policy

All Python package installation/config uses **only** the approved Microsoft feed
`https://packagefeedproxy.microsoft.io/pypi/simple` (see `pip.conf`). Never add a
public PyPI fallback (`docs/tech/security_requirement.md`). The runtime core has no
mandatory third-party dependency; `serve`/`azure` extras are optional.

```powershell
# Only when the optional serve/azure extras are needed:
pip install --index-url https://packagefeedproxy.microsoft.io/pypi/simple `
  -e "services\knowledge-orchestrator[serve,azure]"
```
