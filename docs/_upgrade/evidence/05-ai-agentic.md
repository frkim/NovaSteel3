# AI / ML / Agentic Evaluation — NovaSteel jury rubric (criteria 1–4)

Weight: 4 of 12 criteria (≈20 of 60 points). This is the single most decisive area.

- **PROJECT A** = `D:\work\20260507 - NovaSteel\NovaSteel`
- **PROJECT B** = `D:\work\20260724 - Novasteel 3`

---

## 1. Executive verdict

| Dimension | Project A | Project B |
|---|---|---|
| Physics-informed RUL | Feature-based **linear extrapolation on heat-flux slope** with a documented Fabric MLflow **GradientBoostingRegressor uplift path**. Not a PINN, but *labelled* "physics-informed" honestly (heat-flux domain features, thresholds, wear rate). | Formula-based: `p50 = (thickness − 300) / degradationRate` with a hard-coded per-sector rate and a "demo" p10/p90 fan. Fabric notebook literally hard-codes `demo_warning` risk = 0.87 / RUL = 21 days for one asset+seed. No PIML, no training, no MLflow. |
| Energy optimizer | **Two solvers**: a greedy "greenest window" heuristic (`dispatch_model.py`) **and** a real **PuLP/CBC MILP** (`milp.py`) with binary start-slot variables, single-heat-per-furnace constraints, weighted CO₂+cost objective. | **Bounded enumeration** over ±maxShift slots + tie-break; CO₂ % is *capped/scaled* (`min(15.0, savings*0.84)`) and peak reduction is clamped to `[0.03, 0.07]`. No LP/MILP. Explicit "deterministic demo" naming (`energy-dispatch-deterministic:1.0.0`). |
| GenAI knowledge capture | Real Foundry client (Azure OpenAI **GPT-5 + text-embedding-3-large**) with Entra auth, RAG (lexical fallback + cosine over embeddings), citation regex enforcement, decline-on-no-source, Content Safety gate, plus a live smoke test that hits GPT-5. | Real **Foundry Agent Service** adapter *scaffolded* with `azure-ai-projects` + `DefaultAzureCredential`, but the extraction path is `NotImplementedError` — the working extractor is a deterministic keyword-bucket classifier. **Real Speech Fast Transcription** adapter, similarly scaffolded but not called in the demo (fixture used instead). Extensive Prompt-Injection defense, grounding enforcement, draft→review→approve workflow. |
| LLM/model deployment IaC | Bicep provisions Foundry `AIServices` + project + **actual model deployments** (`gpt-5` `2025-08-07`, `text-embedding-3-large`) — but public-network `Enabled` and `disableLocalAuth: false`. | Bicep provisions Foundry `AIServices` + Speech account with **`publicNetworkAccess: 'Disabled'`, `disableLocalAuth: true`, private endpoints, private DNS zones, diagnostic settings**, but **does not deploy any model** — model & Agent Service are a deferred manual gate. |
| Runtime agents | None. Everything is deterministic Python + a single grounded chat call for P4. Multi-agent story is *dev-time only* (`.github\agents\*`). | Formal **agent identity** (`knowledge-capture`) with a **tool allow-list registry** (`ToolRegistry`), spotlighting, safety meta-prompt, `AgentResult(refused/trace)`, injection-scan → refuse. But the runtime agent behaviour is a Python fake honouring the same policies. |
| Responsible AI evaluation | Azure Content Safety wrapper (`AzureContentSafety`) + assistant-level citation check + decline behaviour tested. No formal eval harness. | **Formal offline evaluation harness** (`evaluation.py`) producing a scorecard (injection block-rate, grounding coverage, safe-prompt success) + prompt-injection unit fixtures + explicit `AGENT_TOOL_ALLOWLIST` + `FORBIDDEN_TOOL_NAMES`. |
| Multi-agent coordination | **Dev-time only**: 10 Copilot subagents in `.github\agents\*` with an `orchestrator.md` that decomposes/handoffs. Zero runtime multi-agent. | **Two runtime agent identities defined** (`knowledge-capture`, `energy-dispatch`) with separated tool allow-lists and a shared prompt-defense/grounding contract — but they do not converse. No planner/executor, no reflection loop. |

**Bottom line.** Project A delivers *more real AI plumbing* (live GPT-5, real MILP, real embeddings) but *less agentic scaffolding* — its "agents" are `.github\agents\*` used to build the repo, not runtime tool-calling agents. Project B delivers *less real AI* (deterministic scoring, deterministic extractor, no live model call in the demo path) but *far more agentic and Responsible-AI discipline* (agent identity, tool allow-list, spotlighting, prompt-injection scanner, offline eval harness, private-endpoint IaC, draft→review→approve state machine with optimistic concurrency).

---

## 2. AI infusion point coverage matrix

### 2.1 Point 1 — Physics-informed furnace-lining RUL (target ≥ 21-day lead)

| | Project A | Project B |
|---|---|---|
| Runtime file | `workloads\p1_predictive_maintenance\physics_features.py`, `rul_model.py` | `services\scoring-worker\src\scoring_worker\service.py` (`score_lining`) + `fabric\notebooks\ns-deterministic-demo-scoring.Notebook\notebook-content.py` |
| Algorithm | Extract heat-flux, thermocouple, vibration from telemetry window; least-squares linear fit on heat-flux slope (`_metric_fit`); compute wear rate + recent-acceleration + `normalized_health_index = (threshold − current)/(threshold − baseline)`; project TTF = `(threshold − current) / slope` (`rul_model.py:120-123`). Suppresses non-actionable windows (`observed_days < 10`, `slope < 0.2`); flags escalated review if TTF < 21 days. | `p50 = (thickness − 300) / degradationRate` where `degradationRate = 3.0 if sector=="07" else 0.02` (`service.py:34-37`); p10=p50*0.8, p90=p50*1.31. Fabric notebook adds a Spark risk-score of weighted temp/heat-flux excesses and then **hard-codes `demo_warning` = seed 240726 + `LUX-BF-01` → risk 0.87, p50 21.0** (`notebook-content.py:96-110`). |
| Physics content | Yes, modest: heat flux, thermal gradient, vibration corroboration, unit-consistent thresholds; documented as "physics-lite / feature-based". Also ships a Fabric MLflow `GradientBoostingRegressor` training scaffold (`train_rul.py`) as the ML uplift path with a `meets_sc003_target` tag for holdout MAE ≤ 5 days. | Naming (`lining-rul-piml:1.3.0-demo`) claims PIML; algorithm is a **linear thickness→days formula with a per-sector constant and a demo hard-code**. No Arrhenius, thermal-diffusion, residual-physics loss, or training pipeline. |
| Lead-time target | Explicit constant `MIN_ADVANCE_WARNING_DAYS = 21.0` used in escalation logic (`rul_model.py:28`); model returns `Prediction` with `time_to_failure_days`. | Demo asset is **wired to return exactly 21.0 days**. Realistic assets use `p50 = (thickness − 300)/rate`, which produces plausible days but is not learned or physics-derived. |
| Realness verdict | **Real (feature-engineered ML with linear-fit head) + roadmap to gradient boosting.** Honest labelling of "physics-informed = physics-based features". | **Deterministic simulated.** Model version string implies more than the code delivers. |

### 2.2 Point 2 — Energy dispatch optimization (target −14 % energy/t, −22 % CO₂)

| | Project A | Project B |
|---|---|---|
| Runtime file | `workloads\p2_energy_dispatch\dispatch_model.py` (heuristic), `milp.py` (MILP) | `services\optimizer-worker\src\optimizer_worker\service.py` |
| Algorithm | (a) Heuristic: batches all heats per furnace, picks the lowest-carbon contiguous window (`_greenest_window`) respecting readiness + deadlines. (b) **PuLP/CBC MILP**: binary `x[j,s]` start-slot vars, single-heat-per-furnace-slot no-overlap constraints, weighted `co2_weight*carbon + cost_weight*price` objective, solved with `PULP_CBC_CMD` (`milp.py:44-116`). | Bounded enumeration over `[planned − maxShiftSlots, planned + maxShiftSlots]` with a stable tie-break `(price, |shift|, slot)` (`service.py:76-97`). Then **manually caps CO₂ savings** at `min(15.0, savings*0.84)` and peak reduction to `[0.03, 0.07]` (`service.py:131-143`). Auxiliary load is added as 2× flexible cost for optical realism. |
| Constraints modelled | Ready-slot, deadline-slot, per-furnace no-overlap, per-heat unique start, warm-up energy per campaign; heuristic falls back to baseline on infeasible batches (records `deadline_breaches`). | maxShiftMinutes, maxConcurrentBatches, minSoakMinutes, maxHoldMinutes, urgent = fixed slot, equal-tonnage identity check. |
| Baseline comparison | Deterministic naive baseline (`baseline_dispatch`) run alongside optimized to compute % savings honestly. | Reports raw + capped savings side-by-side — good transparency, but the headline number is the capped one. |
| Solver library | `pulp` (lazy import, `SolverUnavailableError` if absent) → CBC. | None — plain Python enumeration; explicit "solves the small demo problem with a bounded enumeration". |
| Realness verdict | **Real optimizer** (MILP + heuristic both wired). | **Deterministic simulated / rule-based.** Would need a real LP for the claimed savings percentages to be defensible. |

### 2.3 Point 3 — GenAI knowledge capture (interview → structured procedure library)

| | Project A | Project B |
|---|---|---|
| Runtime files | `workloads\p4_knowledge_capture\{capture,retrieval,assistant,foundry_client,knowledge_library}.py`, `content_safety.py`, `live_smoke.py` | `services\knowledge-orchestrator\src\knowledge_orchestrator\{orchestrator,grounding,prompt_defense,procedure_workflow,tools,evaluation}.py` + `adapters\{azure,local}_{foundry,speech}.py` |
| LLM path | `FoundryClient` posts to `openai/deployments/gpt-5/chat/completions?api-version=2025-01-01-preview` using an Entra bearer token (`foundry_client.py:52-64`). Embeddings via `text-embedding-3-large`. `KnowledgeAssistant.ask` retrieves top-k, builds a SOURCES block with `[S1]` tags, sends to GPT-5, then parses `[S\d+]` citations and refuses if missing (`assistant.py:66-110`). | `AzureFoundryKnowledgeAgent.extract_draft` builds a spotlighted grounded prompt and would call `AIProjectClient.agents.create_and_process_run(...)` — but raises `NotImplementedError` at the mapping step (`azure_foundry.py:66-68`). The actual extraction used by tests/demo is `LocalFoundryKnowledgeAgent` (`local_foundry.py`), which does **keyword-bucket classification** into safety / check / observation / rationale with transcript-segment citations. |
| RAG | Lexical scorer (`retrieval.py`) with optional cosine over live embeddings. Explicit `min_score` threshold → decline. | No retrieval-augmented answering runtime; only a `search_procedures` over APPROVED procedures (title/observation substring match). |
| Citation enforcement | `_CITE = re.compile(r"\[S(\d+)\]")`; answer with no citations = declined (`assistant.py:84-89`). | `enforce_extraction_grounding` requires every citation to be a real transcript-segment id; `enforce_retrieval_grounding` requires every citation to be an APPROVED procedure id (`grounding.py`). Stronger contract. |
| Prompt injection | System prompt tells GPT-5 to decline; nothing else. | Full defense module: `SAFETY_META_PROMPT`, `spotlight()` with sentinel-defanging, `scan_for_injection()` with a documented HIGH/LOW pattern taxonomy (`prompt_defense.py:63-94`), and unit tests over attack fixtures. Injected transcript segments are ignored and traced. |
| Content Safety | `AzureContentSafety` wrapper hits `contentsafety/text:analyze` with severity gate (`content_safety.py:44-76`); `AllowAll` / `BlockAll` for tests. | Not integrated (relies on documented Prompt Shields on the Foundry deployment); local `prompt_defense` covers the offline story. |
| Workflow / HITL | Assistant returns `Recommendation(status=Proposed)` — one-shot handoff to a human, no explicit approval state machine. | Formal DRAFT → IN_REVIEW → APPROVED / REJECTED state machine with `Knowledge.Publisher` RBAC gate, optimistic-concurrency `expectedVersion` (409 STALE_APPROVAL), idempotency key, immutable append-only `AuditLog` (`procedure_workflow.py`, `orchestrator.py:265-301`). |
| PII / GDPR | `capture.redact_pii` (email/phone/name regex) + `RawCapture` kept separate for right-to-erasure. | `consent.py` (create/grant/deny/withdraw + `require_capture_allowed`) + audio metadata validation + Art. 17 propagation (delete transcript on withdraw, `orchestrator.py:325-352`). |
| Live path proof | `workloads\p4_knowledge_capture\live_smoke.py` — grounded question + hallucinatory question against **deployed GPT-5** (`aif-novastee-dev-ox26fi`). | No live smoke; production adapter is `NotImplementedError` at the mapping step. |
| Realness verdict | **Real GenAI + RAG** with live GPT-5 + embeddings + Content Safety. | **Deterministic simulated GenAI** with real Speech/Foundry *scaffolding* and much stronger security/governance around it. |

---

## 3. Model selection & deployment comparison

| Concern | Project A | Project B |
|---|---|---|
| Chat model | **GPT-5** (`gpt-5`, version `2025-08-07`), `GlobalStandard`, capacity 20 (`infrastructure\modules\foundry.bicep:22-29`). | Not deployed by IaC. Solution doc says: "Select a model only after the release gate verifies model, tool, quota, and Data Zone (EU) availability… Data Zone Standard (EU) preferred." (`solution-architecture.md:252-254`). |
| Embeddings | **`text-embedding-3-large`** (Standard, capacity 50) — deployed and consumed by `FoundryClient.embed`. | Not deployed / not used. |
| Speech | Not used (P4 works from typed transcripts). | Bicep provisions a dedicated `SpeechServices` account with private endpoint (`foundry-speech.bicep:63-82`). `AzureSpeechFastTranscriptionAdapter` uses Fast Transcription REST API `2024-11-15`, diarization, profanity filter, Entra token. |
| Foundry Agent Service | Not used — solution is direct chat completions. Foundry project resource is provisioned (`account/projects@2025-10-01-preview`) but no agent identity is created. | Explicitly designed for it; `AzureFoundryKnowledgeAgent` uses `azure-ai-projects.AIProjectClient` + `agents.create_and_process_run`. **However** the deployment is gated by `foundryAgentServiceManuallyValidated` — no agent is provisioned by Bicep. |
| Auth | `DefaultAzureCredential` → bearer token for `https://cognitiveservices.azure.com/.default`. No account keys in source. **But Foundry account has `disableLocalAuth: false` and `publicNetworkAccess: 'Enabled'`.** | `DefaultAzureCredential` for Foundry (`https://ai.azure.com/.default`) and Speech (`https://cognitiveservices.azure.com/.default`). **Foundry and Speech both `disableLocalAuth: true` and `publicNetworkAccess: 'Disabled'`.** |
| Networking | Public endpoint on Foundry (dev posture). | Private endpoints + private DNS zones for both `privatelink.cognitiveservices.azure.com` and `privatelink.openai.azure.com`, plus Log Analytics diagnostic settings (`foundry-speech.bicep:108-226`). |
| Region / EU residency | Region parameterised (`param location string`); no explicit Data Zone / residency logic. | Explicit **Sweden Central primary**, West Europe only after documented recovery review (`foundry-speech.bicep:12`, `deployment-topology.md`). `docs\research\azure-ai-regions.md` documents Data Zone Standard (EU) decision. |
| Model versioning / drift | `MODEL_VERSION = "rul-linear-v1"` / `"quality-rules-v1"` / `"p2-dispatch-heuristic-v1"` / `"p2-dispatch-milp-v1"` per algorithm; every `Prediction` and `EnergyPlan` carries it; MLflow `log_model` for the RUL uplift. | `lining-rul-piml:1.3.0-demo`, `energy-dispatch-deterministic:1.0.0`, `quality-risk:1.0.0-demo`, `knowledge-capture` agent name; captured on every scored record. `fact_model_evaluation` semantic-model table exists. |
| Content Safety | Runtime Python client `AzureContentSafety` (severity threshold configurable). | Documented Prompt Shields on the Foundry deployment; local `prompt_defense` module is the defense-in-depth. |
| Fallbacks | Content Safety → `AllowAll` if unconfigured (explicit "no accidental unchecked" comment); MILP → `SolverUnavailableError` if PuLP missing; retrieval → lexical if no embed_client. | Local adapters everywhere (`LocalFoundryKnowledgeAgent`, `LocalSpeechTranscriptionAdapter`) so demo has zero cloud dependency. |

**Deployment strategy score**: Project B's IaC is *more secure and more Responsible-AI-aware* (private endpoints, local-auth disabled, region policy, agent-service gate); Project A actually *deploys and uses* a real chat + embedding model.

---

## 4. Agentic behaviour deep dive

### 4.1 Runtime agents in the delivered product

**Project A — no runtime agent.** Everything is a Python function call. `KnowledgeAssistant.ask` is a single-turn RAG chat completion; there is no planner/executor loop, no tool calling, no state graph, no reflection, no agent framework (`semantic-kernel`, `langchain`, `langgraph`, `autogen`, `azure-ai-projects`) imported anywhere in `workloads/*`.

**Project B — Foundry Agent Service is the target pattern, executed as a policy-shaped local fake.**
- `AzureFoundryKnowledgeAgent` (`adapters\azure_foundry.py:25-68`) uses `azure.ai.projects.AIProjectClient` and `agents.create_and_process_run` — this is the Foundry Agent Service SDK call. The mapping of structured tool output → `ExtractedKnowledge` is intentionally left as `NotImplementedError` "at the integration gate" — so the *product* runs on `LocalFoundryKnowledgeAgent` which honours the same governance rules (`agent_name`, spotlighting, injection scan, refuse-if-no-citation, `AgentResult(trace)`).
- Tool allow-list is *codified*: `KNOWLEDGE_AGENT_TOOLS = {search_approved_procedures, write_draft_procedure}`, `ENERGY_AGENT_TOOLS = {read_energy_context, forecast_demand, simulate_schedule, propose_recommendation}`, and a `FORBIDDEN_TOOL_NAMES` set (`approve_procedure`, `commit_schedule`, `delete_audio` …) — a `ToolRegistry` refuses any dispatch outside the allow-list (`tools.py:66-125`).
- Human-in-the-loop is enforced via the procedure workflow's role check (`Knowledge.Publisher`) and optimistic concurrency (`procedure_workflow.py:70-99`) — a *real* HITL gate rather than a status flag.
- The tool registry + role check together are the Responsible-AI equivalent of an approval-gate handoff pattern.

### 4.2 Dev-time (build-time) agents — clearly outside the delivered runtime

**Project A `.github\agents\*`** (10 files: orchestrator, solution-architect, data-platform-engineer, azure-data-expert, ai-ml-engineer, quality-engineer, compliance-officer, business-value-cfo, presentation-storyteller, demo-implementation). `orchestrator.md` is explicit: "You are the Lead Orchestrator … You do not do the deep specialist work yourself. Instead you understand the request, decompose it, route each part to the right expert agent, and integrate the results". This is an authentic Copilot **multi-agent-with-handoffs** pattern — but for **building** the repo, not for **running** the plant. **It should be counted as excellent *engineering practice*, not as delivered agentic AI.**

**Project B `.github`** has zero agent definitions (only workflows + dependabot). Dev-time agent story is absent.

### 4.3 Cross-cutting agentic pattern inventory

| Pattern | Project A (runtime) | Project A (dev-time) | Project B (runtime) | Project B (dev-time) |
|---|---|---|---|---|
| Planner / decomposer | — | ✅ `orchestrator.md` | — | — |
| Handoffs between agents | — | ✅ 9 specialist routes | — | — |
| Tool/function calling | — | ✅ (edit/search/runSubagent) | ⚠️ *scaffolded* via `azure-ai-projects`, *codified* via `ToolRegistry`, but the demo does not exercise a live tool-call loop | — |
| Tool allow-list / least privilege | — | — | ✅ `AGENT_TOOL_ALLOWLIST` + `FORBIDDEN_TOOL_NAMES` (`tools.py`) | — |
| Reflection / critique loop | — | — | — | — |
| State graph / state machine | — | — | ✅ Procedure workflow (`DRAFT→IN_REVIEW→APPROVED/REJECTED`) with optimistic concurrency & idempotency (`procedure_workflow.py`) | — |
| Human-in-the-loop approval gate | ✅ `Recommendation(status=Proposed)`, decision service | — | ✅ RBAC role check + expected-version + idempotency-key + audit chain | — |
| Guardrails: content safety | ✅ Live Azure Content Safety client | — | ✅ Prompt Shields (documented on Foundry) + local `prompt_defense` | — |
| Guardrails: prompt-injection defense | ⚠️ System-prompt-only | — | ✅ Spotlighting + safety meta-prompt + regex scanner + attack fixtures + eval harness | — |
| Grounding / citation enforcement | ✅ Regex `[S\d+]` + decline-on-empty + `min_score` retrieval floor | — | ✅ Segment-id and approved-procedure-id validation with `GroundingError` | — |
| Multi-agent conversation | — | ✅ | — | — |
| Agent framework in use | — | ✅ GitHub Copilot subagent framework | ⚠️ `azure-ai-projects` SDK imported but not exercised end-to-end | — |

---

## 5. Multi-agent coordination assessment

**Project A — Dev-time only.** The `orchestrator` agent decomposes work and hands off to nine specialists whose roles map 1:1 to documents in `docs\usecase\First_Proposal\*`. This is a genuine planner+specialists pattern with explicit handoff routing rules. **Runtime coordination is single-service; there is no multi-agent behaviour in the delivered product.**

**Project B — Two runtime "agent identities" defined but they do not talk to each other.**
- The registry knows about `knowledge-capture` and `energy-dispatch` agents, each with a disjoint tool allow-list, sharing the same `prompt_defense` and grounding contract, and interacting with the plant only through BFF-mediated `Proposed` recommendations that a human approves.
- The end-to-end coordination pattern is closer to *policy-shared micro-services* than to a multi-agent conversation. There is no agent-to-agent handoff, no critique/refine loop, no LangGraph/AutoGen state graph.
- The `KnowledgeOrchestrator` class is a workflow coordinator, not a multi-agent orchestrator; it sequences Speech → Foundry agent → grounding gate → workflow transition → audit — a real orchestration pattern but with only one AI participant per session.

Neither project ships a genuine **multi-agent conversation / reflection loop / state-graph orchestrator** in the runtime. Project B is one refactor away (add a critic agent that reviews the DRAFT against the transcript before submitting for human review). Project A would need to add tool calling + agent framework from scratch.

---

## 6. Responsible-AI / evaluation assessment

| | Project A | Project B |
|---|---|---|
| Model evaluation harness | Assistant unit tests + MLflow logging for the RUL uplift (holdout MAE, `meets_sc003_target` tag); no cross-workload eval scorecard. | **`evaluation.py`** produces a scorecard: injection block-rate, grounding coverage on clean + injected transcripts, safe-prompt success. Backed by JSON attack fixtures. |
| Groundedness / relevance | Retrieval `min_score` floor + citation regex + decline. | Two-sided grounding contract (transcript segments for extraction, approved procedure ids for retrieval) with `GroundingError`. |
| Content safety | Live Azure AI Content Safety client with configurable max severity per category. | Documented on the Foundry deployment (Prompt Shields); code-level `prompt_defense` scanner. |
| Prompt-injection controls | System-prompt only. | Multi-layer: spotlight sentinel-defanged data blocks, safety meta-prompt, `_HIGH_PATTERNS` regex library (ignore-previous, disregard, override-system, reveal-prompt, role-hijack, dev-mode, exfiltrate, force-tool, act-as), silent-ignore + trace log for injected transcript segments, tool allow-list with `FORBIDDEN_TOOL_NAMES`, and evaluation coverage. |
| Immutable audit | `AuditLog(Sequence)` overrides `__setitem__/pop/clear` to raise `ImmutableAuditError`; every prediction + human decision appended with model_or_logic_version + retention class. | `AuditLog` with record-hash chain + query-by-domain (`audit.py`), used by `KnowledgeOrchestrator` on every transition (create/transcribe/draft/approve/reject/withdraw). |
| GDPR | `redact_pii` regex + `RawCapture` erasable separately; `RetentionClass` enum. | Full consent lifecycle (create/grant/deny/withdraw) + Art. 17 propagation deletes transcripts + audio validation gates. |
| EU AI Act posture | Documented in solution docs; solution built around "AI proposes, human decides" (Constitution I). | Documented "high-risk-adjacent" posture in `security-governance-and-threat-model.md §16.2` with explicit conformity checklist and RAI review board sign-off gate. |
| Region / EU residency in code | Not enforced in IaC. | Sweden-Central-primary hard-baked; West-Europe requires separate design review; Data Zone (EU) preference documented. |

Project B is materially ahead on Responsible-AI, evaluation harness, and prompt-injection controls. Project A is materially ahead on *actually calling the AI* and having a working Content Safety wrapper on live traffic.

---

## 7. Proposed scores (1 = Needs Improvement, 5 = Excellent)

### Criterion 1 — Use of AI technologies

- **Project A → 4 (Good).** Real GPT-5 + `text-embedding-3-large` deployed and consumed; live smoke test proves grounding + decline against the deployed model; real PuLP/CBC MILP; documented MLflow uplift for RUL; Content Safety wired. What holds it back from 5: the RUL model is a linear extrapolation (honestly labelled), the Foundry project resource is deployed with public endpoint + local-auth-enabled, and there is no agent-framework runtime.
- **Project B → 3 (Satisfactory).** IaC provisions Foundry AIServices + Speech with private endpoints, no keys, region policy — but *no model deployment* and no live model call in the demo path. The Foundry Agent Service adapter is `NotImplementedError`; the extractor that actually runs is a keyword-bucket classifier. Speech is scaffolded, not called. This is real *AI security engineering*, but the AI itself is simulated.

### Criterion 2 — AI model selection and deployment

- **Project A → 3 (Satisfactory).** Correct model choices (GPT-5 chat, `text-embedding-3-large`) with Entra auth and MI. But the Foundry account is deployed `publicNetworkAccess: 'Enabled'` and `disableLocalAuth: false` — that is not a secure deployment strategy for a GDPR / EU AI Act workload. No region/residency policy in IaC.
- **Project B → 4 (Good).** No model is deployed *at all*, which is a real gap. But everything else is best-practice: `disableLocalAuth: true`, `publicNetworkAccess: 'Disabled'`, private endpoints with private DNS zones for both cognitiveservices and openai FQDNs, diagnostic settings to Log Analytics, Sweden-Central-first region policy with a documented manual Agent-Service quota/tool/model validation gate, `azure-ai-regions.md` research doc. If a model were deployed, this would be a clear 5.

### Criterion 3 — Autonomy and orchestration

- **Project A → 2 (Needs Improvement) for runtime autonomy; add +1 for the dev-time orchestrator = 3 (Satisfactory).** The delivered product has no autonomous agent — everything is deterministic Python with a single grounded chat call. The Copilot dev-time orchestrator is genuinely well-crafted but is *not* the deliverable being graded.
- **Project B → 3 (Satisfactory).** Has an agent identity, a tool allow-list registry, a state-machine workflow, spotlighting, and injection defense — this is orchestration discipline. But the agent is not actually executing planner/executor loops against live tools; the runtime is a policy-shaped fake. Solid framework, thin execution.

### Criterion 4 — Multi-agent coordination

- **Project A → 2 (Needs Improvement) runtime; but the dev-time orchestrator + 9 specialists with routing + handoffs is a real pattern; jury credit is a judgement call. Netted → 2.** Runtime deliverable has zero multi-agent behaviour. Mention the dev-time pattern as engineering practice, do not claim it as product feature.
- **Project B → 3 (Satisfactory).** Two agent identities are formally defined with disjoint tool allow-lists and a shared prompt-defense/grounding/audit backbone; the `KnowledgeOrchestrator` sequences Speech → Foundry agent → grounding gate → workflow → audit; DRAFT→IN_REVIEW→APPROVED is a real state machine with RBAC + optimistic concurrency + idempotency. Missing: agent-to-agent handoff, reflection/critique loop, LangGraph/AutoGen-style state graph across agents.

### Summary score table (out of 5)

| Criterion | Project A | Project B |
|---|---|---|
| 1. Use of AI technologies | **4** | **3** |
| 2. AI model selection & deployment | **3** | **4** |
| 3. Autonomy & orchestration | **3** | **3** |
| 4. Multi-agent coordination | **2** | **3** |
| **Subtotal (of 20)** | **12** | **13** |

Project B edges out Project A on this axis primarily because of its formal agent-identity discipline, tool allow-list, evaluation harness, and security-hardened IaC. Project A's Achilles' heel is a *runtime with no agent*; its dev-time orchestrator is impressive engineering but not the product being scored.

---

## 8. Top 5 AI fixes — prioritized by jury-score gain

### Project A (target: +3–4 points)

1. **Move to Foundry Agent Service and expose real tools.** Wrap `KnowledgeAssistant` behind an `AIProjectClient` agent with two tools: `search_procedures(query)` and `write_draft(structured_fields)`. Immediately lifts Criterion 3 from 3→4 and Criterion 4 from 2→3. (Effort: ~1 day using `azure-ai-projects`.)
2. **Harden the Foundry Bicep deployment.** Set `disableLocalAuth: true`, `publicNetworkAccess: 'Disabled'`, add private endpoint + `privatelink.openai.azure.com` DNS zone, add diagnostic settings, and pin `location = 'swedencentral'` with a documented Data-Zone-Standard EU rationale. Lifts Criterion 2 from 3→4.
3. **Add a critic/reflection loop before the human review.** Have the assistant answer, then have a second GPT-5 call verify every citation is quoted verbatim from the referenced source and refuse if not. Lifts Criterion 4 further and hardens grounding.
4. **Add an evaluation scorecard.** A `platform/eval/*.py` runner that iterates {grounded, ungrounded, injected, safety-sensitive} question fixtures against a mocked `ChatClient` and prints pass-rates for citation coverage, decline correctness, injection block. Cheap; lifts Responsible-AI narrative for the jury.
5. **Replace the linear RUL extrapolation with the already-scaffolded gradient-boosting model** (`train_rul.py`) or add a residual-physics-loss term (`loss = MSE(y_true, y_pred) + λ * physics_residual`). Even a small notebook run makes "physics-informed" more defensible.

### Project B (target: +3–4 points)

1. **Actually deploy a model and finish the Foundry Agent Service adapter.** Add a `deployment` block to `foundry-speech.bicep` (or a sibling module) for `gpt-4o-mini` or `gpt-4o` in `swedencentral` (Data Zone Standard), then implement the missing `ExtractedKnowledge` mapping in `AzureFoundryKnowledgeAgent.extract_draft` (currently `NotImplementedError`). Single biggest lift — moves Criterion 1 from 3→4.
2. **Replace the deterministic optimizer with a real MILP.** Even a small `pulp` / `ortools` model with the existing `_Interval` / `_Batch` structures would let you drop the manual `co2Pct = min(15.0, savings*0.84)` cap that reads as "we know the numbers aren't from optimization". Lifts Criterion 1 and defends the −22 % CO₂ headline.
3. **Add real physics to the RUL model.** Replace `p50 = (thickness − 300)/rate` with an Arrhenius wear-rate + heat-flux integral over the telemetry window, and remove the `demo_warning` hard-code in `ns-deterministic-demo-scoring.Notebook`. Currently the notebook literally short-circuits to `risk 0.87 / RUL 21` for `seed 240726` + `LUX-BF-01` — a jury with a technical member will flag this.
4. **Ship one live end-to-end demo path.** A `demo_live.py` in `knowledge-orchestrator` that hits real Speech Fast Transcription on a 20-second consented wav and drives the real Foundry agent through DRAFT → IN_REVIEW → APPROVED. This is the missing "AI actually runs" evidence.
5. **Add a second runtime agent that reflects on the first.** A `knowledge-critic` identity with its own tool allow-list (`search_approved_procedures` only) that reviews the DRAFT and can add a `reviewer_note` before the human sees it. This is the cheapest way to earn Criterion 4 = 4 because it is a genuine multi-agent handoff + reflection pattern using the existing tool-registry primitives.

---
