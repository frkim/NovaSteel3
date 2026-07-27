# 08 — Knowledge Hub

**Audience:** complete beginners to steel operations, generative AI, and privacy governance  
**Reading time:** 12 minutes  
**Persona:** Pieter Claes — Knowledge Engineer / Admin  
**Routes covered:** `/{site}/knowledge-hub/procedures`, `/{site}/knowledge-hub/capture-status`  
**Last updated:** 2026-07-27  
[🇫🇷 Version française](../fr/08-knowledge-hub.md)

The Knowledge Hub is NovaSteel's most human AI area. It addresses the use-case problem that "Skilled operators" are retiring and "knowledge" is disappearing faster than it can be captured, and it implements the third AI infusion point: a "GenAI knowledge-capture system" that interviews operators and structures expertise into searchable procedure libraries (`docs\usecase\usecase.md`).

## Newcomer basics

Experienced steel operators often know things that are never written down: what a furnace sounds like before trouble, which temperature pattern means a sensor is lying, or when to call maintenance early. This is **tacit knowledge**, and Pieter's persona exists to capture it safely before it disappears (`docs\personas\personas-and-journeys.md`).

NovaSteel's flow is consent → speech-to-text → grounded extraction → critic review → human review → approved searchable procedure. Those stages are implemented in the orchestrator, critic loop, and workflow service (`services\knowledge-orchestrator\src\knowledge_orchestrator\orchestrator.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\critic.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`).

**Retrieval-augmented generation (RAG)** means the AI retrieves approved source text before it answers. NovaSteel combines BM25 lexical search with cosine similarity, fuses rankings with reciprocal rank fusion (RRF), and declines if no approved source grounds the answer (`services\knowledge-orchestrator\src\knowledge_orchestrator\retrieval.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\orchestrator.py`). "No citation ⇒ no answer" matters because an unsafe, invented procedure is worse than a clear refusal (`services\knowledge-orchestrator\src\knowledge_orchestrator\grounding.py`, `docs\demo\demo-runbook.md`).

The safety and privacy pipeline requires consent before capture, redacts or pseudonymises personally identifiable information (PII), screens both input and output with content-safety checks, and forbids agents from publish/approve/delete/schedule tools (`services\knowledge-orchestrator\src\knowledge_orchestrator\consent.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\pii.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\content_safety.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\tools.py`).

## Procedures — `/{site}/knowledge-hub/procedures`

![Knowledge Hub procedures screen](../screenshots/knowledge-hub-procedures.png)

**In one sentence.** The screen lets Pieter search captured expertise, review procedure cards, and publish only human-approved knowledge.

**Background for newcomers.** A procedure is a trusted instruction set for plant work. In NovaSteel a procedure can be `DRAFT`, `IN_REVIEW`, `APPROVED`, or `REJECTED`; only approved procedures are generally retrievable, and approval requires the `Knowledge.Publisher` role (`services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`, `docs\implementation\api-contracts.md`).

**What you see on screen.**  
1. The header says **Knowledge Hub** and the subtitle says it searches approved procedures and governs consent-bound capture and review, matching the UX purpose for Pieter (`docs\ux\dashboard-specification.md`).
2. KPI cards show **Approved procedures 1**, **In review 1**, **Coverage 70%**, and **Capture sessions 0**; good means approved knowledge and topic coverage are rising, bad means too much knowledge is stuck in review or missing (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`).
3. The **Search procedures & captured expertise...** box filters the library; entered text calls `client.searchKnowledge()`, while an empty search calls `client.getProcedures()` (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `apps\analytics-mfe\src\api\dataClient.ts`).
4. The **Procedure cards** panel carries badges `CHL-05`, `OBJ-04`, and `AI-03`, plus **New entry**, **Seed samples**, and **Reset demo** buttons wired to knowledge routes (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `apps\analytics-mfe\src\api\knowledgeClient.ts`).
5. The first card is **Approved cooling-circuit inspection procedure**, labelled `APPROVED`, `v2`, and `source: interview`; approved means it can be retrieved as published knowledge (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`).
6. The second card is **Hearth sector over-temperature verification**, labelled `IN_REVIEW`, `v1`, and `source: interview`, with **Approve** and **Reject** buttons; this is the human gate before operators can rely on the draft (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `docs\personas\personas-and-journeys.md`).
7. **Capture completeness** shows Blast furnace 82%, Reheat furnace 64%, Hot strip mill 71%, Energy & utilities 58%, and Quality lab 77%; lower bars show topics where more retiring-expert interviews are needed (`apps\analytics-mfe\src\api\fixtures.ts`, `apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`).
8. **Workflow pipeline — 2 procedures** shows one in review and one approved, followed by **Human-in-the-loop gate**, which states that no procedure is published until a domain expert with `Knowledge.Publisher` approves it (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`).
9. The lower **Procedures table** has searchable columns such as Title, Session, Observation, Review status, and Version; the table is for review/export, while status rules are enforced server-side (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`).
10. The grounded-answer response is not visible in this static screenshot. It is implemented through `POST /v1/knowledge/query`, which returns inline `[[chunk-id]]` citations or a structured decline such as `no_grounded_source` when approved content cannot support an answer (`services\bff-api\src\bff_api\routes.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\orchestrator.py`, `docs\demo\demo-runbook.md`).
11. The header **Copilot** button opens a separate contextual assistant; this guide mentions it only briefly because guide 14 covers cross-cutting features (`apps\analytics-mfe\src\components\copilot\CopilotPanel.tsx`, `docs\demo\demo-runbook.md`).

**Why this component was implemented.** The use case says "Skilled operators retiring, with knowledge disappearing faster than it can be captured" and calls for a "GenAI knowledge-capture system" that interviews operators and structures expertise into searchable procedure libraries (`docs\usecase\usecase.md`). Pieter's persona owns review, publication, and coverage gaps (`docs\personas\personas-and-journeys.md`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Retiring operators, knowledge disappearing | `CHL-05` | Badges and interview-sourced procedure cards. | `GET /v1/knowledge/procedures`, `GET /v1/knowledge/search`; `apps\analytics-mfe\src\api\dataClient.ts`, `services\bff-api\src\bff_api\routes.py`, `services\bff-api\src\bff_api\knowledge_adapter.py`. |
| Capture and structure expertise | `OBJ-04` | Draft/review/approved lifecycle, versions, approval buttons. | `POST /v1/knowledge/interviews`, `POST /v1/knowledge/procedures/{id}:submit`, `:approve`, `:reject`; `services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`. |
| GenAI knowledge capture | `AI-03` | Grounded extraction, critic loop, approved-only retrieval, structured decline. | `POST /v1/knowledge/query`; `services\knowledge-orchestrator\src\knowledge_orchestrator\retrieval.py`, `grounding.py`, `critic.py`, `orchestrator.py`. |
| GDPR lawful/minimised capture | `REG-01` | New entry requires consent; PII is redacted. | `POST /v1/knowledge/interviews`; `apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `services\knowledge-orchestrator\src\knowledge_orchestrator\consent.py`, `pii.py`. |

**How the data reaches this screen.** `KnowledgeHub.tsx` calls `client.getProcedures()` or `client.searchKnowledge()` through `DataClient`; the BFF exposes `GET /v1/knowledge/procedures` and `GET /v1/knowledge/search`; `KnowledgeAdapter` delegates to `KnowledgeOrchestrator`; offline fallback uses `fixtures.procedures()` and `knowledgeCoverage()` (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `apps\analytics-mfe\src\api\dataClient.ts`, `services\bff-api\src\bff_api\routes.py`, `services\bff-api\src\bff_api\knowledge_adapter.py`, `apps\analytics-mfe\src\api\fixtures.ts`).

**Honesty & caveats.** The screenshot proves the visible search/cards/review/coverage UI, not a displayed answer panel. The RAG answer and decline behaviour are documented from the BFF/orchestrator code and demo runbook (`services\bff-api\src\bff_api\routes.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\orchestrator.py`, `docs\demo\demo-runbook.md`). Offline demo mode uses deterministic local adapters; Azure Foundry GPT-4o is wired but needs a deployed model (`services\bff-api\src\bff_api\knowledge_adapter.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\adapters\azure_foundry.py`, `docs\presentation\proof_of_execution.md`).

**Try it yourself.** Open `http://localhost:5266/LU/knowledge-hub/procedures`, search for `cooling` or `hearth`, and compare approved versus in-review cards (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `apps\analytics-mfe\src\api\fixtures.ts`).

## Capture Status — `/{site}/knowledge-hub/capture-status`

![Knowledge Hub capture status screen](../screenshots/knowledge-hub-capture-status.png)

**In one sentence.** The screen shows whether knowledge capture is consent-bound, reviewed, approved, and broad enough across critical topics.

**Background for newcomers.** Capture status is governance: consent is recorded, interviews are transcribed, drafts are extracted, review happens, and only approved versions are published (`services\knowledge-orchestrator\src\knowledge_orchestrator\consent.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\orchestrator.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`).

**What you see on screen.**  
1. The active tab is **Capture Status**, but the docked layout still shows KPI cards, search, procedure cards, capture completeness, workflow pipeline, and table (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`).
2. **Capture sessions 0** has the target **consent-bound**, reflecting that consent must be granted for `knowledge-capture` with a positive retention period before recording (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `services\bff-api\src\bff_api\routes.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\consent.py`).
3. **New entry** opens fields for title, domain, operator reference, retention days, a consent notice, and a checkbox confirming explicit consent under GDPR Article 6(1)(a); the button stays disabled until required fields and consent are present (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`).
4. The lifecycle is **draft → in review → approved**: `DRAFT` can be submitted, `IN_REVIEW` can be approved or rejected, and `APPROVED`/`REJECTED` are terminal (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`).
5. **Coverage 70%** targets 80%; good means important domains are covered, bad means expertise is still undocumented (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `apps\analytics-mfe\src\api\fixtures.ts`).
6. **Human-in-the-loop gate** confirms no procedure reaches operators without a domain expert's `Knowledge.Publisher` approval, which supports EU AI Act oversight evidence (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `apps\analytics-mfe\src\proof\proofCatalog.ts`).
7. GDPR Article 17 erasure is not visible on the screenshot, but the backend hard-deletes interview transcripts and Copilot conversations, pseudonymises procedure attribution, and appends an `erasure.executed` tombstone while preserving the audit hash chain (`services\knowledge-orchestrator\src\knowledge_orchestrator\erasure.py`, `docs\security\security-governance-and-threat-model.md`).

**Why this component was implemented.** The proof says the pipeline turns a spoken interview into a structured, cited, reviewed, versioned procedure, and nothing reaches the library without a named human publisher and full audit trail (`docs\presentation\proof_of_execution.md`). Pieter's persona is accountable for that publication gate (`docs\personas\personas-and-journeys.md`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Capture expertise before it is lost | `OBJ-04` | Coverage KPI, completeness bars, pipeline, human gate. | `knowledgeCoverage()` and procedure statuses; `apps\analytics-mfe\src\api\fixtures.ts`, `apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`. |
| GenAI capture system | `AI-03` | Consent → STT → extraction → critic → review → approved procedure. | `POST /v1/knowledge/interviews`; `services\knowledge-orchestrator\src\knowledge_orchestrator\orchestrator.py`, `critic.py`, `adapters\local_speech.py`, `adapters\local_foundry.py`, `adapters\azure_foundry.py`. |
| GDPR lawful, minimised, erasable capture | `REG-01` | Consent dialog, retention, PII redaction, Article 17 erasure. | `services\knowledge-orchestrator\src\knowledge_orchestrator\consent.py`, `pii.py`, `erasure.py`; privacy route in `services\bff-api\src\bff_api\routes.py`. |
| Human AI oversight | `REG-02` | `Knowledge.Publisher` gate and forbidden agent tools. | `services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`, `tools.py`, `apps\analytics-mfe\src\proof\proofCatalog.ts`. |

**How the data reaches this screen.** `KnowledgeHub.tsx` computes counts from `proceduresState.data`, gets coverage from `knowledgeCoverage()`, and uses `KnowledgeClient` for create, submit, approve, reject, seed, and reset actions. `KnowledgeClient` maps those to BFF routes such as `POST /v1/knowledge/interviews`, `POST /v1/knowledge/procedures/{id}:submit`, `:approve`, and `:reject`; `KnowledgeAdapter` wraps `KnowledgeOrchestrator` (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `apps\analytics-mfe\src\api\knowledgeClient.ts`, `services\bff-api\src\bff_api\routes.py`, `services\bff-api\src\bff_api\knowledge_adapter.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\orchestrator.py`).

**Honesty & caveats.** The screenshot shows zero current capture sessions and two baseline procedures; it does not prove live microphone or production consent. Demo mode seeds synthetic fixture audio and local deterministic extraction; production Azure Speech, Azure Content Safety, and Azure Foundry adapters require cloud configuration (`services\bff-api\src\bff_api\knowledge_adapter.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\adapters\azure_speech.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\adapters\azure_content_safety.py`, `services\knowledge-orchestrator\src\knowledge_orchestrator\adapters\azure_foundry.py`).

**Try it yourself.** Open `http://localhost:5266/LU/knowledge-hub/capture-status`, press **New entry** to inspect the consent fields, then cancel unless you want a synthetic capture session (`apps\analytics-mfe\src\components\screens\KnowledgeHub.tsx`, `apps\analytics-mfe\src\api\knowledgeClient.ts`).

## Why grounding, decline, and GDPR matter together

| Control | Plain-language reason | Repository evidence |
|---|---|---|
| Grounding | Answers must cite approved text or transcript segments. | `services\knowledge-orchestrator\src\knowledge_orchestrator\grounding.py`, `retrieval.py`. |
| Approved-only RAG | Drafts cannot become official answers. | `services\knowledge-orchestrator\src\knowledge_orchestrator\procedure_workflow.py`, `retrieval.py`. |
| Structured decline | If no approved source grounds an answer, the system refuses instead of inventing. | `services\knowledge-orchestrator\src\knowledge_orchestrator\retrieval.py`, `docs\demo\demo-runbook.md`. |
| PII redaction | Personal names, emails, phone numbers, employee IDs, and similar data are minimised. | `services\knowledge-orchestrator\src\knowledge_orchestrator\pii.py`. |
| Dual content safety | User input and model output are screened. | `services\knowledge-orchestrator\src\knowledge_orchestrator\content_safety.py`, `adapters\azure_content_safety.py`. |
| Article 17 erasure | Personal data can be deleted or pseudonymised while the audit hash chain remains intact. | `services\knowledge-orchestrator\src\knowledge_orchestrator\erasure.py`, `docs\security\security-governance-and-threat-model.md`. |

---

[◀ Previous: 07 — Sustainability and Compliance](07-sustainability-and-compliance.md) | [▲ Index](README.md) | [Next ▶: 09 — Executive Overview](09-executive-overview.md)
