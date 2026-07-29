# Microsoft Foundry and Azure Speech regional research

> **Research date:** 2026-07-25  
> **Authority:** This research informs, but does not override, the [solution architecture](../architecture/solution-architecture.md) and [deployment topology](../architecture/deployment-topology.md). Regional availability, quotas, models, networking, and preview status are rechecked in the target tenant before deployment.

## Decision summary

NovaSteel’s primary EU placement is **Sweden Central** for the Foundry project, Azure Speech, application services, Event Hubs, and Fabric capacity. Normal Foundry inference uses a **Data Zone (EU)** deployment: data at rest remains in the designated region and inference stays within the EU data zone, not necessarily Sweden Central. If a legal or DPO decision requires single-region inference, use a regional deployment in Sweden Central after model and quota validation.

Use **Microsoft Foundry Agent Service** only as a constrained dialogue, retrieval, explanation, and draft-workflow layer. Python services remain authoritative for RUL, quality, and energy calculations. Azure Speech **Fast Transcription** is the interview path for recorded consent-aware sessions; a manual text and approved replay fallback remains mandatory.

## Regional posture

| Capability | Sweden Central | West Europe | North Europe | France Central |
|---|---|---|---|---|
| Foundry Agent Service | Primary target; confirm project, agent, tool, quota, and private-network support in tenant | EU contingency candidate; requires a separate recovery/data-transfer design | **Not an Agent Service anchor**; do not base the architecture on it | Viable only after the same tenant/model/tool validation |
| Foundry model deployment | Data Zone (EU) by default; regional only for a confirmed single-region requirement | Not an implicit replica | Not used for the Agent Service path | Optional only when a separately validated requirement justifies it |
| Speech Fast Transcription | Primary interview target; recheck the required language/diarization features | Separately approved alternative for specialized speech needs | Speech-only consideration, not an agent anchor | Alternative subject to feature validation |
| Recovery | Source-controlled definitions and approved data restoration first | Tested EU recovery target, never automatic Fabric failover | Not selected | Not selected by default |

The Foundry Agent Service regional-support table accessed on the research date lists Sweden Central, West Europe, and France Central for Responses API and Agents; it does not list North Europe. This is a current-service fact, not a guarantee of tenant quota or tool/model availability.

## Capability boundaries

1. **Identity:** use Microsoft Entra ID/RBAC and managed identities for supported Azure-to-Azure flows. Do not use production model API keys in application configuration.
2. **Agent tools:** permit only named read, forecast, simulate, and draft/propose operations. The energy agent cannot call a commit endpoint; a human approval route is independently policy-gated. The knowledge agent cannot publish a procedure.
3. **Knowledge capture:** obtain and record consent, language, speaker role, retention deadline, and deletion-request linkage before sending audio for transcription. Raw audio and unapproved transcripts are Highly Confidential.
4. **Retrieval:** query approved procedures only for general answers. Drafts and raw transcripts are never a generally accessible source corpus.
5. **Safety:** use Prompt Shields/content controls where supported; treat retrieved text and market payloads as untrusted data, not instructions. Log tool outcome and safety state without logging sensitive audio, transcript, or prompt payloads.
6. **Preview exclusion:** no preview tool, model, feature, or SDK is on the demonstration critical path. Do not select a model family, version, tool feature, or API route from this document.

## Deployment validation gate

Immediately before deployment, capture evidence for all of the following:

- Foundry project creation, Agent Service availability, supported agent/tool type, required model, quota, and private-network behavior in Sweden Central;
- the Data Zone (EU) or regional deployment type required by the applicable residency decision;
- Speech Fast Transcription language identification, speaker separation, file limits, consent/retention flow, and fallback behavior;
- managed-identity/RBAC assignments for Foundry tools, storage/search, Speech, and the FastAPI BFF;
- safety controls, tracing/evaluation behavior, throttling/retry limits, and no-sensitive-content logging;
- any West Europe recovery copy, which requires DPO approval, retention/encryption controls, and a tested restore.

## Official sources rechecked

| Source | Use | Accessed |
|---|---|---|
| [Foundry Agent Service limits, quotas, and regions](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions) | Agent/Responses regional support; quota and tool caveats | 2026-07-25 |
| [Foundry deployment types](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types) | Global, Data Zone, and regional processing/residency distinctions | 2026-07-25 |
| [Foundry authentication and authorization](https://learn.microsoft.com/azure/foundry/concepts/authentication-authorization-foundry) | Entra/RBAC authentication pattern | 2026-07-25 |
| [Foundry Agent Service tools](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-catalog) | Tool availability must be validated per region/model | 2026-07-25 |
| [Azure Speech fast transcription](https://learn.microsoft.com/azure/ai-services/speech-service/fast-transcription-create) | Recorded-audio transcription behavior | 2026-07-25 |
| [Azure Speech regional support](https://learn.microsoft.com/azure/ai-services/speech-service/regions) | Speech feature and regional validation | 2026-07-25 |
| [Fabric regional availability](https://learn.microsoft.com/fabric/admin/region-availability) | Sweden Central and recovery-context caveats | 2026-07-25 |

See the [security governance](../security/security-governance-and-threat-model.md) for consent, identity, threat-model, and audit controls, and the [API contracts](../implementation/api-contracts.md) for the constrained Foundry and Speech integration surface.
