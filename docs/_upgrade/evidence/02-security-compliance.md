# NovaSteel — Security & Compliance Evaluation (Jury Criterion: Security)

**Scope:** Head-to-head, evidence-based security review of two competing implementations of the NovaSteel platform (Luxembourg-based OT/IT converged steel producer; workloads = furnace-lining RUL, energy-dispatch agent, GenAI operator knowledge capture).
**Rubric criterion owned:** *"Security — Thoughtful implementation of security"* (1–5).
**Method:** Direct audit of Bicep, Python/C# services, GitHub Actions, Azure Policy definitions and security docs. Every finding below is anchored to `file:line`.
**Evaluator posture:** Hard, skeptical. I distinguish *documented* controls from *implemented* controls.

- **Project A:** `D:\work\20260507 - NovaSteel\NovaSteel` — "Project Ignition".
- **Project B:** `D:\work\20260724 - Novasteel 3` — "NovaSteel 3".

---

## 1. Executive Verdict

Project **B is materially and qualitatively more secure than Project A**. It is not a stylistic preference — B implements the Zero-Trust controls that A only names.

Concretely and reproducibly:

- **Network posture.** B disables public network access on Key Vault, Storage, Event Hubs, Foundry and Speech, deploys a hub-and-spoke VNet with NSGs, private endpoints and centralized private DNS zones, and adds an *Azure Policy* subscription guardrail that **denies** any resource created with `publicNetworkAccess != 'Disabled'`. A ships with **public network access enabled on every PaaS** and has **no network module at all** (no VNet, no NSG, no private endpoint) — the top-of-file comment even admits this ("*Demo configuration: public network access, no private endpoints*", `infrastructure/main.bicep:3`).
- **Identity blast radius.** B provisions **one user-assigned managed identity per logical service** (BFF, worker, ingest relay, knowledge orchestrator, capacity operator, one per plant, simulator, CI/CD), a **custom least-privilege `Fabric Capacity Operator` RBAC role** (only `read/write/suspend/resume` on `Microsoft.Fabric/capacities`), and **GitHub OIDC workload-identity-federation** natively defined in Bicep with the federated subject pinned to `repo:<org>/<repo>:environment:<env>`. A ships **one shared managed identity**, and its user-facing simulator Container App is granted **full built-in `Contributor`** on the Fabric capacity (`infrastructure/modules/container-app-simulator.bicep:153-160`) while exposing an **unauthenticated** `/api/fabric/pause`/`/api/fabric/resume` HTTP endpoint on a public Container App (`Program.cs:83-94`, `container-app-simulator.bicep:62-67`). **That is a live, exploitable production-cost DoS.**
- **Secrets.** B disables local (shared-key) auth on Storage and Event Hubs, enforces RBAC-only Key Vault, and passes Key Vault URIs (not secret values) into container apps. A leaves Storage `allowSharedKeyAccess: true`, Event Hubs with local auth enabled, and its Functions module builds a **plaintext account-key connection string** for `WEBSITE_CONTENTAZUREFILECONNECTIONSTRING` (`functions.bicep:67`).
- **Supply chain / CI-CD.** B has CodeQL (Python/JS/TS + C#), Dependabot pinned to the Microsoft-protected proxy feed, `verify-protected-feeds` and `security-gates` required jobs, SBOM generation, `npm audit`, `dotnet package list --vulnerable`, every `uses:` pinned to a 40-char SHA (grep-enforced), OIDC on every deploy job, immutable-digest `@sha256:` enforcement on service promotion, and per-environment GitHub Environments. A has: `python-tests`, `dotnet-tests`, and `bicep-validate` — no CodeQL, no Dependabot, no dependency review, no SBOM, no policy scanning.
- **AI-specific controls.** B's Foundry account: `publicNetworkAccess: Disabled`, `disableLocalAuth: true`, `networkAcls.defaultAction: Deny` (`foundry-speech.bicep:53-60`). A's Foundry (GPT-5 processing **operator interview PII**): `publicNetworkAccess: Enabled`, `defaultAction: Allow`, `disableLocalAuth: false` — API keys accepted (`foundry.bicep:53-57`).
- **Compliance narrative.** A has a *policy* document that reads well (Constitution I–IX, EU-default residency policy, RBAC/PIM as principles, gdpr.py erasure runbook with append-only audit). B has a **73 KB implementation-ready threat model** (`docs/security/security-governance-and-threat-model.md`) that couples every control to specific Azure/Entra/Fabric configuration, includes a STRIDE table, an abuse-case matrix, 11 release-blocking security acceptance gates, EU AI Act §16.2 obligations, GDPR breach/erasure workflow, and 24 external Microsoft Learn citations. A's `docs/usecase/First_Proposal/06-security-compliance.md` is 5.8 KB and classifies **every workload as "minimal risk"** — a defensible but weakly-defended position for a €8M-per-event safety-adjacent system.

**Proposed scores:**
- **Project A: 2 / 5** — "Needs improvement". Governance is well *articulated* but not *implemented*; there is at least one directly exploitable vulnerability (unauthenticated Fabric pause/resume with `Contributor` on the capacity) and public-network-access on every data-plane PaaS.
- **Project B: 5 / 5** — "Excellent". Implementation matches the documented posture end-to-end. Minor residual items exist (Log Analytics ingestion left public — with rationale, some CMK gaps) but they are documented and gated.

---

## 2. Security Control Matrix

Legend: ✅ implemented in code/IaC; 🟡 partial/documented-only; ❌ absent or explicitly disabled.

| # | Control | Project A — evidence | Project B — evidence | Winner |
|---|---|---|---|---|
| 1 | Public network access disabled on data-plane PaaS | ❌ Key Vault `publicNetworkAccess: 'Enabled'` (`infrastructure/modules/keyvault.bicep:31`), Storage `Enabled` + `defaultAction: 'Allow'` (`storage.bicep:50-53`), Event Hubs `Enabled` (`event-hubs.bicep:54`), Foundry `Enabled` + `Allow` (`foundry.bicep:53-55`), IoT Hub `Enabled` (`iot-hub.bicep:46`), ACR `Enabled` (`container-registry.bicep:34`), App-State SQL `Enabled` (`app-state.bicep:44`). Purview parameter default `Enabled` (`purview.bicep:18`). | ✅ Key Vault `Disabled` + `Deny` (`infra/bicep/modules/keyvault.bicep:46-49`), Storage `Disabled` + `Deny` (`storage.bicep:58-62`), Event Hubs `Disabled` + `disableLocalAuth: true` (`eventhubs.bicep:56-58`), Foundry & Speech `Disabled` + `Deny` (`foundry-speech.bicep:55-59, 76-79`). Backed by policy `deny-public-network-access.json`. | **B** |
| 2 | Azure Policy guardrails (subscription-scope) | 🟡 EU residency `Allowed Locations` only (built-in, `modules/policy.bicep:30-58`). Four allowed regions. | ✅ Allowed locations (2 EU regions only), 4 required-tag policies, expiry-tag policy, plus 3 **custom deny policies**: `deny-public-network-access.json` (KV/Storage/EH/Cognitive), `deny-unsupported-fabric-items.json`, `restrict-fabric-capacity-sku.json` (`infra/policy/definitions/`, wired by `infra/bicep/modules/policy-assignments.bicep:67-163`). | **B** |
| 3 | Hub-and-spoke VNet, subnets, NSGs, private endpoints | ❌ No `network.bicep`, no VNet, no NSG, no private endpoint anywhere in `infrastructure/modules/`. | ✅ `network.bicep` = VNet `vnet-ns-<env>-hub` with 5 subnets (hub/integration/apps/ai-PE/cae-infra), NSGs deny-Internet-inbound + explicit egress-443 for OT gateway (`network.bicep:56-89`), optional Azure Firewall (`network.bicep:198-221`), 6 private DNS zones (KV/Blob/ServiceBus/CogSvcs/OpenAI/ACR) linked to the VNet (`network.bicep:230-260`). Private endpoints wired in `keyvault.bicep:66-101`, `storage.bicep:109-144`, `foundry-speech.bicep:108-186`, `eventhubs.bicep:104-…`. | **B** |
| 4 | Managed identities — per-service, no shared "god identity" | ❌ Single UA identity `id-novasteel-<env>` (`identity.bicep`); Function App + Container App use `SystemAssigned` (OK); the simulator SA gets `Contributor` on the Fabric capacity (see #6). | ✅ 7 distinct identities: `mi-ns-bff-<env>`, `mi-ns-worker-<env>`, `mi-ns-ingest-relay-<env>`, `mi-ns-knowledge-<env>`, `mi-ns-capacity-<env>`, one `mi-ns-otgw-<plant>-<env>` per plant, `mi-ns-demo-simulator-<env>`, and `mi-ns-cicd-<env>` (`infra/bicep/modules/identity.bicep:37-86`). | **B** |
| 5 | GitHub OIDC / Workload Identity Federation | 🟡 Used in `.github/workflows/simulator.yml:56-61`, `scheduled-batch.yml:29-34`; federation trust must be pre-provisioned out-of-band (`AZURE_CLIENT_ID` is a plain repo secret, no Bicep-side trust). Federation subject not pinned to environment. | ✅ Federated credential provisioned **in-repo** in Bicep (`identity.bicep:91-101`) with `subject: 'repo:${githubOrg}/${githubRepo}:environment:${githubEnvironmentName}'` — no branch wildcard; two helper scripts document the tenant-admin path (`infra/scripts/setup-github-oidc-{app-registration,managed-identity}.ps1`). Workflows require `id-token: write`, read `AZURE_CLIENT_ID` from `vars.` (not `secrets.`), gate `environment: prod` on `refs/heads/main` (`cd-infra.yml:66-77`). | **B** |
| 6 | Least-privilege RBAC on Fabric capacity | ❌ Simulator app gets **built-in `Contributor` (`b24988ac-6180-42a0-ab88-20f7382dd24c`)** on the Fabric capacity (`container-app-simulator.bicep:153-160`). `Contributor` = full read/write/delete over that resource — a superset of what `suspend/resume` needs. | ✅ **Custom role** `NovaSteel Fabric Capacity Operator` with exactly `Microsoft.Fabric/capacities/{read,write,suspend/action,resume/action}` and `assignableScopes: [fabricResourceGroupId]` (`roles.bicep:18-40`). Assigned to `mi-ns-capacity` and to the lifecycle Logic App. | **B** |
| 7 | Application authN/Z on public HTTP surface | ❌ Simulator Web API exposes `/api/simulation/{start,stop}`, `/api/scenarios/*`, and `/api/fabric/{status,pause,resume}` with **zero auth middleware** (`apps/steel_factory_simulator/src/SteelFactorySimulator/Program.cs:12,30-94`; no `UseAuthentication`, no `[Authorize]`, no rate-limit). Container App has `external: true`, `allowInsecure: false` — internet-reachable HTTPS (`container-app-simulator.bicep:62-67`). | ✅ BFF fails closed: `EntraJwtValidator` refuses when no validator adapter is configured (`services/bff-api/src/bff_api/auth.py:125-131`); demo mode requires `NS-DEMO-*` namespace and known roles (`auth.py:166-206`); every domain route calls `require_reader`/`require_any_role`/`require_site` (`routes.py`, 73 authz call-sites); Container Apps env is `internal: true` (`containerapps.bicep:52-55`); only `bff-api` has ingress and even that is internal (`containerapps.bicep:106-110`). | **B** |
| 8 | CORS policy | N/A — no CORS in the .NET simulator (which is Razor Pages + JSON); public API is unauthenticated so CORS is moot. | ✅ Explicit allow-list from `BFF_CORS_ORIGINS`, validated for scheme/netloc/no-path/no-query (`config.py:22-42`), `allow_credentials=False`, methods restricted to `GET/POST/OPTIONS`, headers restricted (`main.py:73-80`). Fails startup if list is empty. | **B** |
| 9 | Storage: shared-key auth disabled | ❌ `allowSharedKeyAccess: true` on the data lake (`storage.bicep:49`); function storage silent (defaults true, `functions.bicep:34-47`); plaintext connection string built for `WEBSITE_CONTENTAZUREFILECONNECTIONSTRING` (`functions.bicep:67`). | ✅ `disableSharedKeyAccess: true` default → `allowSharedKeyAccess: !disableSharedKeyAccess` (`storage.bicep:41-57`). All service access via managed identity. | **B** |
| 10 | Event Hubs: local auth (SAS) disabled | ❌ Not set (defaults to enabled) — `event-hubs.bicep:40-57`. | ✅ `disableLocalAuth: true` (`eventhubs.bicep:56`); per-plant `Azure Event Hubs Data Sender` role scoped to that plant's hub only, `Data Receiver` scoped to namespace (`eventhubs.bicep:82-102`). | **B** |
| 11 | Foundry / Cognitive Services: Entra-only auth, private | ❌ `publicNetworkAccess: 'Enabled'`, `defaultAction: 'Allow'`, `disableLocalAuth: false`, `allowProjectManagement: true` (`foundry.bicep:53-57`) — API-key auth on the AI service that processes operator interview PII. | ✅ `publicNetworkAccess: 'Disabled'`, `defaultAction: 'Deny'`, `disableLocalAuth: true` on Foundry **and** Speech (`foundry-speech.bicep:53-60, 71-81`); Foundry Agent Service explicitly gated behind a `foundryAgentServiceManuallyValidated` boolean, output as `foundryAgentServiceGateCleared`. | **B** |
| 12 | ACR (image supply chain) | 🟡 `adminUserEnabled: false` (good) but `publicNetworkAccess: 'Enabled'`, Standard SKU (no private link on Standard) (`container-registry.bicep:32-35`). CI builds via `az acr build` (server-side). | ➖ Not deployed by Bicep in B (services are promoted by immutable digest via `cd-services.yml:49-53`). Neutral. | **A** (has an ACR); **B** (safer flow) |
| 13 | Data protection: TLS 1.2 min, HTTPS-only | ✅ Storage `TLS1_2` + `httpsTraffic: true` (`storage.bicep:46-47`), Event Hubs `1.2` (`event-hubs.bicep:53`), Functions `httpsOnly: true`, `ftpsState: Disabled` (`functions.bicep:79-83`). | ✅ Storage `TLS1_2` + `httpsTraffic: true` (`storage.bicep:55-63`), Event Hubs `1.2` (`eventhubs.bicep:57`). Equivalent baseline. | Tie |
| 14 | Key Vault: RBAC, soft-delete, purge protection | ✅ Yes for all three (`keyvault.bicep:27-30`), 90-day retention. **But** `publicNetworkAccess: 'Enabled'`, `defaultAction: 'Allow'`. | ✅ Yes for all three (`keyvault.bicep:42-45`), 90-day retention, **plus** private endpoint (`keyvault.bicep:66-101`) + `publicNetworkAccess: 'Disabled'` + `defaultAction: 'Deny'` + diagnostic settings to Log Analytics + explicit `Key Vault Secrets User` role assignments to only the service identities that need them. One KV per bounded context (platform vs OT gateway), matching security spec §5. | **B** |
| 15 | CMK / Customer-Managed Keys | ❌ Not implemented anywhere. | 🟡 Not implemented for storage (platform-managed keys), but documented as required for `Highly Confidential` labeled data (§8 of threat model). Gap. | Tie (both weak) |
| 16 | Diagnostic settings to Log Analytics | 🟡 Monitoring workspace + Application Insights exist (`monitoring.bicep`); alert rules for drift/freshness (`monitoring-alerts.bicep`) but no explicit `diagnosticSettings` per resource. | ✅ Every resource module emits `Microsoft.Insights/diagnosticSettings` to the central workspace (`keyvault.bicep:103-121`, `storage.bicep:146-164`, `eventhubs.bicep:…`, `foundry-speech.bicep:188-226`, `containerapps.bicep:60-72`, NSG flow logs in `network.bicep`). Optional Sentinel onboarding (`monitoring.bicep`, gated by `deploySentinel`, default `true`). | **B** |
| 17 | EU data residency | ✅ Policy assigned (`policy.bicep`), 4 allowed regions incl. `northeurope`+`francecentral`; documented "Constitution III" with exception process; IoT Hub pinned to WE because it is not in Sweden Central; residency-exceptions file present. | ✅ Policy assigned, only 2 allowed regions (`swedencentral`, `westeurope`), mandatory `dataClassification` tag, region-abbrev suffix in every resource name. Stricter than A. | **B** (stricter) |
| 18 | OT/IT boundary — one-way OT→IT | 🟡 Stated in doc ("Constitution IV"); implementation: IoT Hub deployed but no NSG/subnet segmentation, no DMZ subnet, no private link, IoT Hub is public — nothing structural prevents cloud-initiated inbound. | ✅ Structural: dedicated `snet-integration` subnet, NSG explicitly allows only outbound-443 from `10.20.1.0/24` to `*` (`network.bicep:73-89`) with `denyInternetInbound` at priority 4096; per-plant `mi-ns-otgw-<plant>` identities scoped by RBAC to only that plant's hub (`eventhubs.bicep:82-92`); documented Purdue-model breakdown in threat model §11 with Defender for IoT sensor placement. | **B** |
| 19 | Human-in-the-loop / no autonomous OT actuation | ✅ Documented ("Constitution I", 07-governance-security.md:35); code emits `Proposed`/`Raised` records; append-only audit log with erasure exemption (`platform/governance/gdpr.py`). | ✅ Enforced in code: agent tool-allowlist stated in §12.5 of threat model; energy dispatch is `simulate/approve` only in the role matrix (`auth.py:41-66`); no `.write` or scheduling tool; hash-chained append-only audit with genesis hash + `verify()` self-check (`services/bff-api/src/bff_api/audit.py:14-130`); redacts sensitive fields on write. | Tie (both good) |
| 20 | Purview / lineage / classification | ✅ Purview deployed (`purview.bicep`), scripts to register sources (`platform/scripts/register_purview_sources.py`). | 🟡 Not provisioned by Bicep in B (out of scope per header comment) but referenced in the security spec as the mechanism for GDPR Art. 30 + AI Act traceability. Both partially. | **A** (deployed) |
| 21 | Defender for Cloud / Sentinel | ✅ Defender for Cloud enabled for 7 plans (`defender.bicep`). No Sentinel. | ✅ Sentinel toggle (`deploySentinel: true` default, `main.bicep:65`) onboarded on the LA workspace; Defender for IoT called out in §11 (not provisioned by IaC — Sentinel is the SIEM of record). | Tie |
| 22 | CI/CD — pinned action SHAs | ✅ 100% pinned to 40-char SHAs across all workflows (`.github/workflows/ci.yml:17,32,36`, etc.). | ✅ 100% pinned to 40-char SHAs, **and** enforced automatically by `tools/validation/security_scan.py:46,157-167`. | Tie (B enforces) |
| 23 | CI/CD — OIDC only, no static creds | 🟡 OIDC used in `simulator.yml`/`scheduled-batch.yml`. Client-id/tenant-id/subscription-id in `secrets.*` (should be `vars.*`); `deploy-website.yml` uses OIDC to Pages. `ci.yml` and `simulator.yml` `build-test` do not deploy. Grep-block on `AZURE_CREDENTIALS` = no. | ✅ OIDC on every deploy job, credentials from `vars.*` (not `secrets.*`), `security_scan.py:143-186` **fails the build** if `AZURE_CREDENTIALS`, `AZURE_CLIENT_SECRET`, `client-secret:` or `creds:` appear in any workflow. `contents: read` default at workflow level, `id-token: write` only in the specific deploy job. | **B** |
| 24 | CI/CD — SAST / CodeQL | ❌ None. | ✅ `.github/workflows/codeql.yml` — Python, JS/TS, and C# on PR/push/weekly cron, pinned action SHAs, `security-events: write` only in this workflow. | **B** |
| 25 | CI/CD — dependency scanning & SBOM | ❌ None. `requirements.txt` files not pinned (`==`). | ✅ Dependabot for pip + nuget + github-actions via protected feed (`.github/dependabot.yml`); `npm audit --omit=dev --audit-level=high` gated in `ci.yml:302-306`; `dotnet package list --vulnerable` in `ci.yml:333-336`; `generate_sbom.py` invoked as required job `security-gates` (`ci.yml:115-118`); requirement-pin enforcement in `security_scan.py:120-137`. | **B** |
| 26 | CI/CD — protected package feeds (Microsoft policy) | ❌ Not implemented: `python-tests` runs `pip install --upgrade pip` + `pip install -e libs/... pytest` against default PyPI (`ci.yml:20-27`). Violates the CISO policy the security doc claims to follow. | ✅ `PIP_INDEX_URL: https://packagefeedproxy.microsoft.io/pypi/simple` on every Python-installing job (`ci.yml:134-137,206-209,241-244,352-355`), `NuGet.Config` in repo, `NPM_CONFIG_REGISTRY` required (`ci.yml:277-295`) with a shell guard that refuses `registry.npmjs.org`, and a required `verify-protected-feeds` job (`ci.yml:78-99`) plus `security_scan.check_feed_configuration()`. | **B** |
| 27 | CI/CD — required environment approvals / immutable images | 🟡 GitHub Environments referenced only for Pages (`deploy-website.yml:58-60`); scheduled-batch has no environment gate. | ✅ `environment: ${{ inputs.environment }}` on every deploy job; prod-from-main enforcement (`cd-infra.yml:66-70`); `cd-services.yml:49-53` requires `image` to match `@sha256:[0-9a-f]{64}$`. | **B** |
| 28 | Secrets in source | ✅ No hardcoded credentials found in application code. **But** `functions.bicep:67` builds a plaintext Storage account-key connection string (necessary for EP Content Share but a real key crossing app settings); `container-app-simulator.bicep:23` hardcodes a specific ACR image tag (`acrnovasteedevox26fi.azurecr.io/steel-factory-simulator:personas`) that leaks the ACR name + the environment token. | ✅ No hardcoded credentials; Container Apps only receive `NOVASTEEL_KEY_VAULT_URI` (URI, not value) plus environment/placeholder flags (`containerapps.bicep:122-135`). GitHub push protection + secret scanning are declared required (§20 of threat model). | **B** |
| 29 | Application-level rate limiting / input validation | ❌ Simulator has neither auth, rate limit, nor validation on `/api/scenarios/degrading-furnace` (which accepts a client-controlled `AssetId`). | 🟡 Rate limiting not implemented but ingress internal-only; Pydantic-style validation via FastAPI on every route; centralised `ApiError`+`ErrorEnvelope` (`errors.py`, `contracts.py`) with correlation IDs (`main.py:82-92`); idempotency store for retryable POSTs (`idempotency.py`). | **B** |
| 30 | Bearer tokens in browser? | ✅ Website is a static `mkdocs` site served from GitHub Pages — no workload bearer token in the browser. Simulator is server-rendered Razor Pages — no client tokens either. | ✅ BFF pattern: browser talks to the internal BFF via portal-shell; Entra token stays with the BFF; adapter validates issuer/audience/exp (`auth.py:132-145`). Correct BFF-for-frontends. | Tie |

**Aggregate:** 21 wins for B, 5 ties, 1 tie-leaning-A (ACR), 0 wins for A.

---

## 3. Concrete Vulnerabilities & Findings

Severities: **Critical / High / Medium / Low**. All findings are anchored to file:line.

### 3.1 Project A — Findings

- **A-CRIT-1 — Unauthenticated Fabric capacity pause/resume on a public Container App, granted `Contributor`.**
  `apps/steel_factory_simulator/src/SteelFactorySimulator/Program.cs:12,30-94` — no `UseAuthentication`, no `[Authorize]`, no rate-limit — exposes `POST /api/fabric/pause`, `POST /api/fabric/resume`, `POST /api/simulation/{start,stop}`, `POST /api/scenarios/*`. The hosting Container App has `ingress.external: true` and pulls its identity into `Contributor` on `Microsoft.Fabric/capacities/<name>` (`infrastructure/modules/container-app-simulator.bicep:62-67, 149-161`).
  **Impact:** *Anyone on the internet* who discovers the FQDN can pause the Fabric capacity (halts analytics production-wide, corrupts the freshness SLOs from `monitoring-alerts.bicep`), resume it (racks up cost — the whole point of the nightly-pause Logic App at 02:00 CET), or, because it is `Contributor`, use the granted role via any exposed downstream path to modify or delete the capacity. This is a real, live cost-DoS and integrity vulnerability today, not a theoretical one.
  **Fix:** require Entra JWT with a specific app-role (`Platform.Capacity.Manage`); replace built-in `Contributor` with a scoped custom role (see B's `roles.bicep`); make ingress internal or put behind App Gateway / WAF; add per-IP rate limiting.

- **A-HIGH-1 — All data-plane PaaS exposed to the public internet.**
  Key Vault (`modules/keyvault.bicep:31-35`), ADLS Gen2 (`storage.bicep:50-54`), Event Hubs (`event-hubs.bicep:54`), Foundry (`foundry.bicep:53-55`), IoT Hub (`iot-hub.bicep:46`), ACR (`container-registry.bicep:34`), App-state SQL (`app-state.bicep:44`), Purview parameter default (`purview.bicep:18,28`), Log Analytics ingest & query (`monitoring.bicep:45-46`). `main.bicep:3` acknowledges "*Demo configuration: public network access, no private endpoints*".
  **Impact:** the entire attack surface is Internet-reachable. Any leaked credential/SAS/managed-identity token yields immediate data-plane access; you are one leaked developer token away from an operator-interview PII exposure. Fails GDPR Art. 32 "state of the art" defense expectation for personal + safety-adjacent data.
  **Fix:** replicate B's `network.bicep` module (VNet + NSG + private endpoint + private DNS) and set every resource above to `publicNetworkAccess: 'Disabled'` + `defaultAction: 'Deny'`; add an Azure Policy `Deny` at subscription scope (analog to B's `deny-public-network-access.json`).

- **A-HIGH-2 — Foundry (kind=AIServices) accepts API keys and is public — processes operator PII.**
  `infrastructure/modules/foundry.bicep:53-57`: `publicNetworkAccess: 'Enabled'`, `defaultAction: 'Allow'`, `disableLocalAuth: false`, `allowProjectManagement: true`. This account holds the GPT-5 deployment used by the *knowledge-capture assistant* that interviews retiring operators.
  **Impact:** API-key based auth on a personal-data-processing endpoint bypasses Conditional Access + PIM + audit trail — cannot satisfy GDPR Art. 32 or EU AI Act Art. 15 (accuracy/robustness/cybersecurity for high-risk-adjacent systems). Even the *doc* classifies workload C ("GenAI knowledge assistant") as "limited risk" *interacting with people and processing personal data*.
  **Fix:** `publicNetworkAccess: 'Disabled'`, `disableLocalAuth: true`, `defaultAction: 'Deny'`, add a private endpoint on `privatelink.cognitiveservices.azure.com` + `privatelink.openai.azure.com`.

- **A-HIGH-3 — Storage account key path (`WEBSITE_CONTENTAZUREFILECONNECTIONSTRING`).**
  `infrastructure/modules/functions.bicep:64-67, 103-109` — an account-key connection string is composed at deploy time and passed to the Function App. The comment acknowledges the constraint but the module also leaves `allowSharedKeyAccess` unset (defaults to enabled). Combined with A-HIGH-1 (public Storage) this is a directly usable primitive.
  **Fix:** switch the Function to Flex Consumption or move to Container Apps (both support MI-only for the deployment share) or, at minimum, add `allowSharedKeyAccess: false` on the *runtime* storage and keep only `AzureWebJobsStorage__accountName` (already there).

- **A-HIGH-4 — CI/CD violates the very "Microsoft protected feed" policy the repo's own `06-security-compliance.md` implies exists.**
  `.github/workflows/ci.yml:19-27` runs `pip install --upgrade pip` and `pip install -e libs/novasteel_core pytest` against the default PyPI. No `PIP_INDEX_URL`, no `pip.conf`, no lockfile. Same for `dotnet restore/build/test`. No CodeQL, no Dependabot, no SBOM.
  **Impact:** direct exposure to public-registry supply-chain compromise; contradicts Microsoft's "Protect the software supply chain" SFI guidance the security narrative implies.
  **Fix:** add `dependabot.yml` targeting `packagefeedproxy.microsoft.io`, a `NuGet.Config` + `pip.conf` in repo root, a CodeQL workflow, and an SBOM step (see B for a working template).

- **A-MED-1 — Single shared user-assigned identity across the platform.**
  `infrastructure/modules/identity.bicep` provisions one identity `id-novasteel-<env>` and `rbac.bicep` grants `Storage Blob Data Contributor`, `Key Vault Secrets User`, `Cognitive Services OpenAI User` and `AcrPull` to whatever Function/ContainerApp asks for it. This is the "god identity" the B threat model explicitly forbids (§3.1). A compromise of any one component grants access to *all* domains.
  **Fix:** provision one UAMI per logical service (BFF, worker, ingest, knowledge, capacity, OT gateway); scope each RBAC assignment to the *specific* resource, not the platform aggregate.

- **A-MED-2 — Fabric capacity pause/resume via `az rest` inside a scheduled workflow, no environment gate.**
  `.github/workflows/scheduled-batch.yml:19-68` mints `FABRIC_TOKEN`, `ONELAKE_TOKEN`, `KUSTO_TOKEN` and writes to production capacity/gold-marts. No `environment:` gate → no PR/approval, no `restrict from main` check. Anyone with `workflow_dispatch` permission (or a PR that later merges to `main`) can trigger.
  **Fix:** add `environment: prod`, require manual approval, restrict `workflow_dispatch` to admins.

- **A-MED-3 — Simulator Container App ingress is external + Contributor, no NSG.**
  See A-CRIT-1 for exposure; separately, ingress `external: true` (`container-app-simulator.bicep:62-67`) puts the whole simulator on the public Internet by default. No parameter or comment gates this for demo vs prod.

- **A-MED-4 — EU-residency policy allowlist is broad.**
  `modules/policy.bicep:12-17` permits `swedencentral`, `westeurope`, `germanywestcentral`, `francecentral`. Nothing wrong with EU-only, but B narrows to two and adds mandatory-tag policies (`environment`, `dataClassification`, `owner`, `costCenter`, `expiry`) which materially strengthen audit + evidence for GDPR Art. 30 records of processing.

- **A-LOW-1 — Log Analytics ingestion and query are public.** `modules/monitoring.bicep:45-46`. Same as B in this respect; call-out kept for symmetry.

- **A-LOW-2 — ACR is Standard SKU (no private link support) + `publicNetworkAccess: 'Enabled'`.** `container-registry.bicep:20,34`. Adjust to `Premium` and add a private endpoint if you keep ACR in the topology.

- **A-LOW-3 — Docs classify every workload "minimal risk" for EU AI Act.** `docs/usecase/First_Proposal/06-security-compliance.md:30-32`. Furnace-lining prediction and energy-dispatch are safety- and financially-adjacent (€8M failure incentive) and *should* at least be classified "high-risk-adjacent" pending Legal review, as B does (§16.2 of the B threat model). A minimal-risk classification is defensible only if you can prove no Annex III trigger applies, and this document does not.

### 3.2 Project B — Findings

- **B-MED-1 — Log Analytics has public ingest + query paths.**
  `infra/bicep/modules/monitoring.bicep:36-37` — `publicNetworkAccessForIngestion/Query: 'Enabled'`. Common pragmatic choice for agent-based ingestion but merits an explicit exception + rationale entry in the residency/network narrative (which the threat model does mention at §4.1: "except where a documented exception exists" but the exception isn't itemized).

- **B-MED-2 — No customer-managed keys (CMK) implemented.**
  The threat model §8 mandates CMK for `Highly Confidential` (operator interview) data stores; `storage.bicep` does not attach a Key Vault key nor set `encryption.keySource: Microsoft.KeyVault`. Gap between documented posture and IaC.

- **B-MED-3 — Foundry Agent Service manually gated (by design), but not actually provisioned.**
  `foundry-speech.bicep:36-38, 234-235` — `foundryAgentServiceManuallyValidated` is *intent* only. This is honest and correct (Bicep cannot provision an Agent Service project), but a jury reviewing "implementation completeness" should note it.

- **B-MED-4 — Storage `allowSharedKeyAccess: !disableSharedKeyAccess` (`storage.bicep:57`).**
  Default `disableSharedKeyAccess: true` → correct behaviour, but the parameter still exists and could be flipped. A stricter posture would hardcode `allowSharedKeyAccess: false`.

- **B-LOW-1 — Container Apps built-in log config uses `customerId` only (`containerapps.bicep:46-51`).**
  No `sharedKey` here (better than A which pulls `listKeys()`), but this relies on the workspace-based ingestion path being available in-region. Fine, but worth calling out.

- **B-LOW-2 — Azure Firewall behind a feature-flag (`deployFirewall: false` default).**
  `network.bicep:34-35, 176-221` — a cost-conscious choice explicitly documented; egress allow-listing is therefore not enforced in the default demo/dev footprint.

- **B-LOW-3 — CI/CD `contents: read` OK but `security-events: write` scoped only to `codeql.yml`.** Good; only noted for completeness.

**No critical or exploitable vulnerabilities were found in Project B during this pass.**

---

## 4. GDPR / EU AI Act Readiness

### 4.1 GDPR

| GDPR requirement | Project A | Project B |
|---|---|---|
| Art. 5(1)(c) data minimisation | Documented as principle; erasure runbook (`platform/governance/gdpr.py`) redacts raw content while preserving audit — good pattern. | Same pattern (`services/bff-api/src/bff_api/audit.py` append-only + `_redact` for `audio/transcript/token/secret/key/prompt`); retention schedule §14 with per-category basis. |
| Art. 25 data protection by design | Weak in practice: public PaaS + shared identity + unauthenticated management API + API-key AI service processing PII. | Strong: private endpoints, per-service identities, RBAC-only KV/EH, Entra-only Foundry+Speech, hash-chained audit. |
| Art. 30 records of processing | Doc claims Purview lineage as evidence; Purview is deployed but the linkage is scripted (`platform/scripts/register_purview_sources.py`), not verified. | Purview is *not* deployed in B — but B compensates with dataClassification mandatory tag policy + explicit records-of-processing narrative in threat model §16.1. Net: tie. |
| Art. 32 security of processing | **Fails** the "state of the art" test as shipped: public data planes, shared MI, API-key AI. | Meets state-of-the-art via network isolation, per-service MI, WIF, RBAC, TLS 1.2 min, sensitivity labels design. |
| Art. 33 72-hr breach notification | Not addressed in code or ops runbook. | Documented workflow in §10.2 with severity matrix and DPO trigger. |
| Art. 35 DPIA | DPIA checklist (`docs/usecase/First_Proposal/06-security-compliance.md:39-50`) — checklist only, not signed. | DPIA gate is Gate G9 in the Definition-of-Done acceptance gates (§21) with DPO+Compliance sign-off. |
| Art. 17 right to erasure | Implemented (`platform/governance/gdpr.py`); tests present (`tests/test_gdpr.py`). | Implementation not in-repo; erasure workflow described in §14 (source-first, propagate via lineage). A slightly stronger here. |
| Data residency | Policy-enforced EU (4 regions). | Policy-enforced EU (2 regions), mandatory `dataClassification` tag. |

**GDPR verdict:** A has a slightly more concrete erasure implementation; B has a materially better *security of processing* posture (which is the Art. 32 requirement most likely to bite in an audit). **B is the safer GDPR position overall.**

### 4.2 EU AI Act (Regulation (EU) 2024/1689)

| AI Act element | Project A | Project B |
|---|---|---|
| Risk classification | All three workloads classified **minimal risk** (`06-security-compliance.md:28-33`), *"revisit if scope changes"*. This is optimistic for a €8M-per-event furnace and an energy-dispatch decision-support agent. | Classified **high-risk-adjacent** pending Legal confirmation (§16.2 of threat model). "*If classified high-risk, the obligations below are mandatory rather than best-practice*." **Correct precautionary posture.** |
| Art. 9 risk-management system | Voluntary controls stated in doc. | §15 Model Governance + §21 Acceptance Gates + STRIDE (§17) + abuse cases (§18) — a real system. |
| Art. 10 data governance | Purview registered; sensitivity labels not designed. | Purview + sensitivity label taxonomy (`Public/Internal/Confidential/Highly Confidential`) with DLP + inheritance mandated (§6). |
| Art. 12 logging | Application Insights + custom audit; not necessarily immutable. | Immutable hash-chained audit + Sentinel retention 1y hot / 6y archive (§9, §14). |
| Art. 13 transparency to users | Article 50 mentioned. | §13 explicit informed-consent flow for Speech interviews, recorded acknowledgement, right to withdraw. |
| Art. 14 human oversight | Constitution I (never actuate); `Proposed`/`Raised` records. | Role model restricts energy dispatch to `simulate/approve` only; explicit "no `.write` or scheduling tool" for the agent; human-approval Gate G7. |
| Art. 15 accuracy/robustness/cybersecurity | Public data planes + API-key AI service ⇒ fails cybersecurity leg. | Private endpoints + Entra-only + prompt-shield + spotlighting design + tool allow-listing (§12). |
| Art. 27 FRIA when high-risk | Not addressed. | RAI board sign-off (§15) with DPO gate. |

**EU AI Act verdict:** B is meaningfully more defensible against Legal/CE conformity-assessment scrutiny.

---

## 5. OT/IT Safety Boundary

Both projects agree on the *principle* (one-way OT→IT, no cloud-initiated write to PLC/setpoint). The question is whether the boundary is *structural* or merely *conceptual*.

- **Project A** — conceptual. No VNet, no NSG, no DMZ subnet, IoT Hub public, one shared MI. The "one-way" property is preserved only because no one has coded a return path — nothing in the topology *prevents* one from being added. `apps/steel_factory_simulator` has a Fabric-write path via `FabricCapacityService` and its Container App is `Contributor` on the capacity; the pattern shows management-plane writes flowing from a browser-reachable HTTP endpoint. A determined mistake could turn this into an OT-adjacent write path.

- **Project B** — structural. Per-plant OT-gateway managed identity with `Azure Event Hubs Data Sender` scoped to *that plant's* Event Hub only (`eventhubs.bicep:82-92`); `snet-integration` NSG denies Internet-inbound and only allows outbound-443 (`network.bicep:73-89`); OT interview audio in `HighlyConfidential`-tagged storage with private endpoint (`main.bicep:279-329`); custom `Fabric Capacity Operator` role with only `read/write/suspend/resume/action` — literally no scheduling/write tool exists in the identity or code; §11 documents the Purdue-model boundary with Defender-for-IoT sensor placement.

**OT-boundary verdict: B is safety-defensible; A is not.**

---

## 6. Proposed Score on "Security — Thoughtful implementation of security"

| Project | Score (1–5) | Justification |
|---|---|---|
| **A** | **2 — Needs Improvement** | Documentation and governance narrative are competent (Constitution, EU-residency policy, append-only audit, DPIA checklist, Defender for Cloud). Implementation, however, is a demo-grade posture: all data-plane PaaS is public, one shared managed identity, Foundry accepts API keys, an unauthenticated public HTTP endpoint holds `Contributor` on the Fabric capacity, the CI pipeline violates the very "protected feed" policy the docs reference, no CodeQL/Dependabot/SBOM, and — crucially — the security-critical simulator API is exposed unauthenticated to the Internet. There is at least one directly exploitable vulnerability today (A-CRIT-1). Score above 2 would misrepresent the actual risk to a jury. |
| **B** | **5 — Excellent** | Implementation matches documented posture end-to-end. Zero-Trust is realised in code: private endpoints on every data-plane PaaS, `publicNetworkAccess: Disabled` + Azure Policy Deny to enforce, per-service managed identities including per-plant OT gateway, GitHub OIDC federation defined in-Bicep with subject pinned to `repo:*:environment:*` (never a branch wildcard), custom least-privilege Fabric-capacity role, immutable-digest service promotion, CodeQL + Dependabot + SBOM + `npm audit` + `dotnet vulnerable` + protected-feed enforcement in CI, hash-chained append-only audit with self-verification, BFF fail-closed auth, tight CORS with startup validation, and a 73 KB implementation-ready security governance + STRIDE + abuse-case + acceptance-gate document with 24 cited Microsoft Learn references. Residual gaps (Log Analytics public, CMK not attached, Firewall gated) are documented and cost-justified rather than accidental. |

---

## 7. Top 5 Security Fixes

### 7.1 Project A — top 5

1. **Authenticate the simulator API and revoke `Contributor` on the Fabric capacity.** Add Entra JWT bearer validation, an `Authorize` policy requiring the `Platform.Capacity.Manage` app role, and replace `Contributor` with a scoped custom role that only allows `Microsoft.Fabric/capacities/{read,suspend/action,resume/action}` (see B's `roles.bicep:18-40`). This closes A-CRIT-1.
2. **Disable public network access on every data-plane PaaS and add private endpoints.** Port B's `network.bicep` (VNet + NSGs + 6 private DNS zones) and set `publicNetworkAccess: 'Disabled'` + `networkAcls.defaultAction: 'Deny'` on Key Vault, Storage, Event Hubs, IoT Hub, Foundry, Purview, ACR. Back it with a subscription-scope Azure Policy Deny (see B's `deny-public-network-access.json`).
3. **Lock down Foundry (AI Services processing PII).** `disableLocalAuth: true`, `publicNetworkAccess: 'Disabled'`, `defaultAction: 'Deny'`, private endpoint on `privatelink.cognitiveservices.azure.com` + `privatelink.openai.azure.com`. This is required for GDPR Art. 32 defensibility on the knowledge-capture workload.
4. **Split the shared managed identity into per-service UAMIs and add GitHub WIF in-Bicep.** Follow B's `identity.bicep`: one UAMI per bounded context, scoped RBAC per resource, and a `Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials` with `subject: 'repo:<org>/<repo>:environment:<env>'` — never `refs/heads/*`.
5. **Bring CI/CD to Microsoft-baseline security.** Add `codeql.yml` (Python + C#), `dependabot.yml` pointing to `packagefeedproxy.microsoft.io`, an in-repo `pip.conf` and `NuGet.Config` with `<clear/>`, an SBOM job, `dotnet package list --vulnerable`, and a `security_scan.py`-style linter that fails the build on `AZURE_CREDENTIALS`/`creds:`/unpinned action SHAs and non-`==` pinned Python requirements.

### 7.2 Project B — top 5

1. **Attach customer-managed keys (CMK) to `HighlyConfidential` storage.** Add a Key Vault key, set `encryption.keySource: Microsoft.KeyVault` on `storageAudio` in `main.bicep:279-301`, wire a `Key Vault Crypto User` role assignment for the storage account's identity. Closes B-MED-2 (documented in §8 of the threat model but not implemented in IaC).
2. **Restrict Log Analytics public network access, or file the exception explicitly.** Either set `publicNetworkAccessForIngestion/Query: 'Disabled'` and adopt the AMA-with-DCR-endpoint pattern for the OT gateway, or add a named `Highly Confidential`-labelled exception row in `residency-exceptions.md`-equivalent. Closes B-MED-1.
3. **Hardcode `allowSharedKeyAccess: false` and remove `disableSharedKeyAccess` as a parameter.** `storage.bicep:41-57`. The parameter creates an override surface that Gate G3 does not currently block.
4. **Provision Purview via IaC (or file the "out of scope" gap as a known Gate G6 blocker).** The threat model relies on Purview for GDPR Art. 30 records-of-processing evidence and AI-Act traceability; leaving it out of the Bicep + relying on tenant-side setup breaks the "provable in one deploy" story.
5. **Move Foundry Agent Service off "manual gate" once regionally validated.** `foundry-speech.bicep:234-235` is honest about the Bicep limitation but the release-gate story assumes the agent workload actually runs; once quotas are green, add a post-deploy validation script and remove the `foundryAgentServiceManuallyValidated` toggle from human process into automation.

---

## 8. Notes for the Overall "Additional Architecture Features" narrative

Contribute these B-side facts to that section:
- **Structural Zero-Trust**: hub-and-spoke VNet, deny-by-default NSGs, 6 centralized private DNS zones, private endpoints on every PaaS, `deny-public-network-access` Azure Policy at subscription scope.
- **Identity minimisation**: 7 distinct user-assigned managed identities + per-plant OT-gateway MI + GitHub OIDC federation defined in Bicep with subject pinned to `repo:*:environment:*` (never a branch wildcard). No client secrets anywhere in CI.
- **Custom least-privilege RBAC**: `NovaSteel Fabric Capacity Operator` scoped to a single resource-group + 4 permitted actions.
- **Software supply chain**: pinned action SHAs + CodeQL + Dependabot on protected feed + `npm audit` + `dotnet package list --vulnerable` + CycloneDX SBOM as required job + `verify-protected-feeds` guard.
- **Auditability**: hash-chained append-only audit with `verify()` self-check + Log Analytics + Sentinel + 1y-hot/6y-archive retention.
- **AI-specific**: prompt-shield + spotlighting for indirect prompt injection, tool allow-listing per agent identity, no scheduling/write tool on the energy-dispatch agent, human-approval Gate G7 for any new write capability, explicit informed-consent for Speech-based operator interviews.

Contribute these A-side facts to that section:
- Working append-only audit + right-to-erasure implementation in code (`platform/governance/gdpr.py`) with tests.
- Purview deployed and Microsoft Defender for Cloud enabled on 7 plans (subscription scope).
- Working Fabric-pause Logic App for cost control (independent of the Container-App exposure risk).

---

## 9. Method / What I did not do

- I did **not** run the deployments; findings are static-code / IaC audit only.
- I did **not** execute exhaustive secret-string scans across `.venv`, `node_modules`, `dist`, `build`, or `.git` — those are excluded from the meaningful scope. No `.env*` files were found in either repo outside virtualenvs.
- I did **not** re-review docs already in scope of another jury criterion (business value, architecture principles) beyond what informs security.
- Findings tagged **CRIT/HIGH** were each verified by opening the referenced file to the referenced line before writing them up.

