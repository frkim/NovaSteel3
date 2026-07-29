# NovaSteel knowledge-orchestrator

Consent-aware **Speech-to-Text (STT)** and **Microsoft Foundry Agent Service**
knowledge-capture workflow for NovaSteel (demonstration). This service coordinates the
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
│   ├── search_store.py        # Azure AI Search procedure store (APPROVED-only) + local fallback
│   ├── foundry_iq.py          # Foundry IQ knowledge sources/base over the procedure index
│   ├── agent_service.py       # Foundry Agent Service hosting (procedure agent, web search)
│   ├── telemetry.py           # OpenTelemetry setup, GenAI/agent/retrieval spans, JSON logging
│   ├── evaluation.py          # offline evaluation scorecard
│   ├── app.py                 # OPTIONAL FastAPI wiring (import-guarded)
│   ├── copilot/
│   │   ├── agents.py          # chat tiers: gpt-5.4-mini (standard) / gpt-5.5 (high reasoning)
│   │   └── online_provider.py # Web IQ → web_search → curated-corpus online search chain
│   ├── adapters/
│   │   ├── base.py            # SpeechTranscriptionAdapter / FoundryAgentAdapter ports
│   │   ├── azure_speech.py    # Fast Transcription via managed identity (no keys)
│   │   ├── azure_foundry.py   # live Foundry chat model via managed identity, citation-enforced
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

`adapter_factory.create_agent()` returns the Azure Foundry adapter when
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

## Models and reasoning tiers

| Tier | Deployment | `reasoning_effort` | Used for |
|---|---|---|---|
| Standard | `gpt-5.4-mini` (`FOUNDRY_CHAT_DEPLOYMENT`) | `minimal` | Ordinary Copilot chat turns and the knowledge extraction agent. |
| High reasoning | `gpt-5.5` (`FOUNDRY_REASONING_DEPLOYMENT`) | `high` | The Copilot chat "high reasoning" toggle. |

The effort levels are not interchangeable between these models. `gpt-5.4-mini`
accepts `minimal`; `gpt-5.5` rejects it and supports only `none`, `low`,
`medium`, `high` and `xhigh`, returning HTTP 400 otherwise. The extraction
adapter therefore exposes `FOUNDRY_EXTRACTION_REASONING_EFFORT`, which must be
raised from its `minimal` default if `FOUNDRY_CHAT_DEPLOYMENT` is repointed at a
larger model.

Both are Global Standard deployments; neither model is offered on regional
`Standard` in Sweden Central or West Europe, which is why `modelDeploymentSku`
defaults to `GlobalStandard` in Bicep. The 5-series chat-completions API requires
`max_completion_tokens` (never `max_tokens`) — the request builder in
`copilot/agents.py` emits the correct field and a per-tier budget, since a
high-effort request that runs out of budget mid-reasoning returns an empty
completion rather than an error.

## Procedure storage (Azure AI Search)

`search_store.py` indexes APPROVED procedures into an AI Search index
(`novasteel-procedures`) with integrated vectorization, a semantic configuration
and hybrid (vector + keyword + semantic reranker) retrieval. The **APPROVED-only**
invariant is enforced at the store boundary as well as in the workflow: `index()`
refuses anything else, so a draft cannot become retrievable even if a caller
misbehaves. `search()` returns the same `RetrievalResult` shape the local corpus
returns, so grounding and citation enforcement are unchanged.

Search document keys may not contain `#`, so chunk identifiers are encoded
`PROC-X-0001#c2` → `PROC-X-0001_c2`. The mapping is reversible, so a chunk found in
the portal can still be traced back to its procedure.

With no `AI_SEARCH_ENDPOINT` (or with `PROCEDURE_STORE_MODE=local`) the service uses
an in-memory store built from the approved-corpus fixture, so tests and the demo
run fully offline.

## Hosted agents (Foundry Agent Service) and Foundry IQ

`agent_service.py` creates the **procedure agent** in Agent Service against the
project endpoint. There is no ARM type for an agent definition, so this is a
data-plane operation performed at startup with the container app's managed
identity; Bicep supplies the project, the connections, the capability host and the
RBAC.

The agent reaches the procedure corpus through a **Foundry IQ knowledge base**
rather than a raw search tool. `foundry_iq.py` provisions a knowledge base over the
procedure index (plus, optionally, a web knowledge source), and the agent is given
it as an MCP tool pointing at
`<search-endpoint>/knowledgebases/<kb>/mcp`, restricted to `knowledge_base_retrieve`
with approval disabled. The API version is pinned explicitly: the GA
`2026-04-01` surface is extractive-only, while answer synthesis and LLM query
planning need `2026-05-01-preview`.

The hosted agent's instructions embed the *canonical* decline sentence produced by
`build_decline_answer(...)`. That is deliberate — hosted answers pass through the
same `enforce_answer_citations` check as local ones, and a paraphrased refusal
would be rejected as an ungrounded answer.

## Online search (Web IQ / web search)

When the Copilot chat "Online Search" toggle is on, `copilot/online_provider.py`
selects a backend in this order:

1. `ONLINE_SEARCH_MODE=web_iq` — a Foundry IQ **web knowledge source**, which pulls
   live results into the same agentic-retrieval pipeline as the procedures, so
   results arrive already reranked and citable.
2. `ONLINE_SEARCH_MODE=web_search` — the Agent Service `web_search` tool.
3. Anything else, including unset or an unrecognised value — the curated offline
   corpus.

Resolution **fails closed**: an unrecognised mode degrades to `offline` rather than
guessing at a network-touching backend. Web knowledge sources are a First Party
Consumption Service — the Microsoft DPA does not apply, data leaves the Azure
compliance and geo boundary, and they are unavailable in sovereign clouds — so
against NovaSteel's EU-residency posture they are off by default and, when enabled,
domain-restricted via `ONLINE_SEARCH_ALLOWED_DOMAINS` (defaulting to standards
bodies such as `iso.org`, `eur-lex.europa.eu` and `echa.europa.eu`). Which backend
actually served a turn is recorded in the chat trace.

## Observability

`telemetry.py` configures Azure Monitor OpenTelemetry plus GenAI instrumentation, so
agent runs, model calls and retrievals appear in the same Application Insights
component as the rest of the platform. `agent_span()` and `retrieval_span()` wrap
the orchestrator's own operations with GenAI semantic-convention attributes.

Message content capture is **off** by default and must be opted into with
`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`: transcripts and chat
turns are `HighlyConfidential`, and traces are not an approved store for them.

On the infrastructure side, the Foundry account carries an `AppInsights` connection
to the same component, which is what makes agent runs visible in the Foundry
portal's Tracing and Monitoring blades.

## Environment variables

| Variable | Default | Effect |
|---|---|---|
| `FOUNDRY_ENDPOINT` | *(unset)* | Foundry account endpoint for inference. Unset ⇒ local fixture agent. |
| `FOUNDRY_PROJECT_ENDPOINT` | *(unset)* | Project endpoint for Agent Service. Unset ⇒ agents are not hosted. |
| `FOUNDRY_CHAT_DEPLOYMENT` | `gpt-5.4-mini` | Standard-tier chat/extraction deployment. |
| `FOUNDRY_REASONING_DEPLOYMENT` | `gpt-5.5` | High-reasoning-tier deployment. |
| `FOUNDRY_EMBED_DEPLOYMENT` | `text-embedding-3-large` | Deployment used for integrated vectorization. |
| `FOUNDRY_KNOWLEDGE_BASE` | `novasteel-procedures-kb` | Foundry IQ knowledge base name. |
| `FOUNDRY_API_VERSION` | *(pinned in code)* | Override the Agent Service API version. |
| `AI_SEARCH_ENDPOINT` | *(unset)* | AI Search endpoint. Unset ⇒ in-memory procedure store. |
| `AI_SEARCH_INDEX` | `novasteel-procedures` | Procedure index name. |
| `PROCEDURE_STORE_MODE` | *(unset)* | `local` forces the in-memory store even if an endpoint is set. |
| `FOUNDRY_AGENT_SERVICE_MODE` | *(unset)* | `local` forces the local agent; `azure` opts in to hosting. |
| `KNOWLEDGE_AGENT_MODE` | *(unset)* | `local` forces fixture extraction; `azure` opts in. |
| `COPILOT_CHAT_MODE` | *(unset)* | `local` forces the offline chat agent; `azure` opts in. |
| `ONLINE_SEARCH_MODE` | `offline` | `web_iq`, `web_search`, or `offline`. Unrecognised ⇒ `offline`. |
| `ONLINE_SEARCH_ALLOWED_DOMAINS` | standards bodies | Comma-separated allow-list for web grounding. |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | `false` | Opt in to capturing prompt/completion content in traces. |

Every `*_MODE` variable is checked **before** the corresponding endpoint, so the
shipped image is offline-safe by default and a deployed environment has to opt in
explicitly. When an Azure path is configured but unavailable (SDK missing,
endpoint unreachable, preview surface mismatch), each adapter logs a warning and
degrades to its deterministic local fallback rather than raising.

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
