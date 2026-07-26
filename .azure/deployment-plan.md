# NovaSteel v3 Azure Deployment Plan

> **Status:** Deployed
>
> Generated: 2026-07-25
>
> Resource prefix: `novasteelv3`

---

## 1. Project overview

**Goal:** Deploy the complete NovaSteel deterministic demonstration to Azure,
publish HTTPS portal/API endpoints, provision the Fabric-centered EU demo
platform, verify the six oral-defense scenarios, and capture screenshots.

**Path:** Add Azure deployment packaging to an implemented application.

The deployment is a separate v3 demo estate. It will not reuse or modify the
existing `rg-novasteel-dev` resources in the Contoso Fx subscription.

---

## 2. Requirements

| Attribute | Value |
|---|---|
| Classification | Demonstration / non-production |
| Data | Synthetic and non-personal only |
| Scale | Small |
| Budget | Cost-optimized |
| Subscription | **Contoso Fx** (`3377065c-bf76-4767-a982-32bce4ffb592`) |
| Tenant | `9d94eb6e-d45e-4f05-bc1b-d0bbd2421561` |
| Primary location | **Sweden Central** |
| Contingency location | West Europe |
| Prefix | `novasteelv3` |
| Expiry | 2026-12-31 |

Sweden Central is permitted by the enforced EU-location policies and already
hosts the existing NovaSteel estate. West Europe is the only automatic
contingency considered by this plan. Every deployment command must include the
explicit subscription ID because the shared CLI environment can change its
ambient default subscription.

---

## 3. Components detected

| Component | Type | Technology | Path |
|---|---|---|---|
| Portal shell | Frontend | C# / Blazor WebAssembly | `apps/portal-shell` |
| Analytics microfrontend | Frontend bundle | React / TypeScript / MUI / D3 | `apps/analytics-mfe` |
| BFF/API | Public API | Python / FastAPI | `services/bff-api` |
| Knowledge orchestration | Internal workflow | Python | `services/knowledge-orchestrator` |
| Deterministic simulator | Job / fixture generator | Python | `simulator` |
| Fabric assets | SaaS-plane definitions | KQL, Lakehouse, notebooks, semantic model | `fabric` |
| Azure infrastructure | Control-plane IaC | Bicep / PowerShell | `infra` |

The React bundle is compiled into the Blazor `wwwroot` and is deployed as one
portal artifact.

---

## 4. Recipe selection

**Selected:** Standalone **Bicep + Azure CLI**.

**Rationale:**

- The repository already contains extensive Bicep and deployment scripts.
- There is no `azure.yaml`; introducing azd adds no deployment advantage here.
- The application requires ACR cloud resources, image promotion, Fabric REST
  automation, and explicit phased orchestration.
- Direct commands can pin the subscription ID and avoid shared-context drift.

No resource deletion or reuse is planned.

---

## 5. Target architecture

**Stack:** Azure Container Apps plus managed Azure/Fabric services.

| Component | Azure service | Demo sizing |
|---|---|---|
| Portal (Blazor + React/MUI/D3) | Azure Container Apps, external HTTPS ingress | 0.25 CPU / 0.5 GiB, 1–2 replicas |
| FastAPI BFF | Azure Container Apps, external HTTPS ingress | 0.5 CPU / 1 GiB, 1–3 replicas |
| Knowledge workflow | BFF-integrated deterministic adapter; cloud service assets prepared | Scale to zero |
| Container images | Azure Container Registry | Basic |
| Telemetry buffer | Event Hubs | Standard, one namespace/hub |
| Fabric analytics core | Microsoft Fabric capacity | F2 |
| Fabric SaaS items | Fabric REST/CLI assets | Isolated `novasteelv3` demo workspace/items |
| AI account | Azure AI Services / Microsoft Foundry account | S0, subject to tenant model availability |
| Speech | Azure AI Speech | S0 |
| Secrets/config | Key Vault + managed identities | Standard |
| Monitoring | Log Analytics + Application Insights | 30-day demo retention |
| Demo artifacts | Storage account | LRS |
| Nightly Fabric pause | Logic App / managed identity | 01:00 Europe/Luxembourg |

### Public boundary

- Portal and BFF receive Azure-managed HTTPS Container Apps endpoints.
- BFF CORS is restricted to the deployed portal origin.
- The browser never receives a workload identity or Azure credential.
- All mutations remain simulated; no PLC, furnace, schedule, CMMS, or production
  Fabric capacity is controlled.

### Build and image flow

1. Build React MFE, then publish the Blazor static artifact.
2. Build portal and BFF images locally after starting Docker Desktop.
3. Push immutable images to the new `novasteelv3` ACR.
4. Container Apps pull by managed identity with `AcrPull`.

If local Docker cannot be started, ACR Tasks are the fallback only after
protected-feed reachability is proven.

---

## 6. Provisioning limit checklist

Read-only checks were run against Contoso Fx on 2026-07-25. The subscription
principal is Owner and User Access Administrator. Required providers are
registered. Enforced policy permits Sweden Central, West Europe,
Germany West Central, and France Central only.

| Resource type | Deploy | Total after | Limit/quota | Evidence / result |
|---|---:|---:|---:|---|
| `Microsoft.Resources/resourceGroups` | 1 | Existing + 1 | 980/subscription | Fixed Azure limit; within limit |
| `Microsoft.App/managedEnvironments` | 1 | 8 | 50/region | Quota usage: 7/50 in Sweden Central |
| `Microsoft.App/containerApps` | 2 | Existing + 2 | No limiting count found for this deployment | Provider registered; managed-environment quota healthy |
| `Microsoft.ContainerRegistry/registries` | 1 | Existing + 1 | 100/subscription | Official service limit; `novasteelv3acr*` name available |
| `Microsoft.Fabric/capacities` | 1 F2 | 4 CU | 512 CU | Fabric CapacityQuota currently 2/512; F2 adds 2 CU |
| `Microsoft.CognitiveServices/accounts` | 2 | Existing + 2 | SKU/service quotas available | Sweden Central AIServices S0 and Speech availability checked |
| `Microsoft.EventHub/namespaces` | 1 | Existing + 1 | 1000/subscription | Official service limit; provider registered |
| `Microsoft.Storage/storageAccounts` | 1 | Existing + 1 | 250/region/subscription | Official service limit |
| `Microsoft.KeyVault/vaults` | 1 | Existing + 1 | 5000/subscription | Official service limit; `novasteelv3kv*` available |
| `Microsoft.OperationalInsights/workspaces` | 1 | Existing + 1 | 1,000/subscription/region | Official service limit |
| `Microsoft.Insights/components` | 1 | Existing + 1 | Not deployment-constraining | Provider registered |
| `Microsoft.Logic/workflows` | 1 | Existing + 1 | Not deployment-constraining | Provider registered |
| `Microsoft.ManagedIdentity/userAssignedIdentities` | 3 | Existing + 3 | Not deployment-constraining | Provider registered; RBAC rights confirmed |
| `Microsoft.Network/virtualNetworks` | 1 | Existing + 1 | 1,000/region/subscription | Official service limit |

**Capacity status:** All planned resources are within known limits. GPU quota is
0, but this deployment does not use GPU Container Apps.

---

## 7. Existing estate and isolation

Contoso Fx already contains `rg-novasteel-dev`, an F2 Fabric capacity, ACR,
Event Hubs, Foundry, Container Apps, and related governance resources.

This plan:

- creates a distinct `rg-novasteelv3-demo-sc` resource group;
- generates a fresh deterministic uniqueness suffix;
- uses names beginning with `novasteelv3` wherever Azure naming permits;
- does not alter `rg-novasteel-dev`, `rg-novasteel-governance`, or their managed
  resources;
- validates every target name and resource ID before deployment.

---

## 8. Preparation changes

| Change | Purpose |
|---|---|
| Add portal and BFF Dockerfiles | Produce deployable application images |
| Add deployment-focused Bicep entry point | Isolate the cost-optimized demo deployment from the broader production blueprint |
| Add ACR and managed `AcrPull` wiring | Remove placeholder public images |
| Standardize BFF port on 8080 | Align image, health probes, and ingress |
| Configure external HTTPS ingress | Make portal/API reachable for the oral defense |
| Inject portal BFF URL and BFF CORS origin | Wire browser traffic correctly |
| Configure deterministic cloud demo mode | Preserve the validated six-moment evidence |
| Wire capacity identity and nightly pause | Enable authorized start/status/pause and 01:00 shutdown |
| Add explicit subscription arguments | Prevent accidental deployment to another subscription |
| Add deployment/verification/screenshot scripts | Repeatable handoff and evidence |

---

## 9. Execution checklist

### Phase 1: Planning

- [x] Analyze workspace
- [x] Gather requirements
- [x] Confirm subscription: Contoso Fx
- [x] Select Sweden Central under enforced EU policy
- [x] Prepare resource inventory
- [x] Fetch quotas and validate capacity
- [x] Scan codebase
- [x] Select Bicep/Azure CLI recipe
- [x] Plan architecture
- [x] Approval recorded from the user's explicit deployment request and
  subsequent selection of the Contoso Fx subscription; unattended execution
  was requested when the approval prompt could not be answered interactively.

### Phase 2: Preparation

- [x] Generate Dockerfiles and deployment scripts
- [x] Generate deployment-focused Bicep
- [x] Apply managed identity/RBAC/security configuration
- [x] Build and test images locally
- [x] Run local functional verification
- [x] Set status to `Ready for Validation`

### Phase 3: Validation

- [x] Invoke `azure-validate`
- [x] Run Bicep build and subscription what-if
- [x] Validate image builds and application probes
- [x] Validate names, providers, policies, quotas, and RBAC
- [x] Populate validation proof
- [x] Set status to `Validated` through `azure-validate`
- [x] All validation checks pass
  - [x] Bicep build/lint and PowerShell parser checks
  - [x] Explicit-subscription bootstrap and full `validate`/what-if
  - [x] Provider, policy, location, name, and least-privilege RBAC checks
  - [x] Image and Fabric validation evidence

### Phase 4: Deployment

- [x] Invoke `azure-deploy`
- [x] Provision Azure resources
- [x] Push immutable images and update Container Apps
- [x] Deploy Fabric SaaS assets where tenant APIs permit
- [x] Verify live RBAC
- [x] Set status to `Deployed`

### Phase 5: Verification and evidence

- [x] Test portal/API HTTPS endpoints
- [x] Run deterministic demo driver against Azure
- [x] Verify persona routes and table behavior
- [x] Verify Fabric capacity state control
- [x] Capture screenshots
- [x] Produce URL/resource/region recap

---

## 10. Validation proof

Validation is complete. Full, command-level evidence is in:

- [IaC and RBAC validation](validation/iac.md)
- [Image build validation](validation/images.md)
- [Fabric preparation validation](validation/fabric.md)

| Check | Command run | Result | Timestamp |
|---|---|---|---|
| IaC / RBAC | `az bicep build`/`lint`, PowerShell parser, explicit subscription `validate` + what-if | PASS: bootstrap 22 creates and full 24 creates; 0 modify/delete; Sweden Central only | 2026-07-25 |
| Images | `pwsh .\.azure\scripts\build-images.ps1`; `test-images.ps1` | PASS: 13 smoke checks, no push/deploy | 2026-07-25 |
| Fabric prep | isolated validators and `-DryRun` scripts | PASS: no live Azure/Fabric mutation | 2026-07-25 |

**Validated by:** `azure-validate`

---

## 11. Deployment proof

Deployment and final verification completed on 2026-07-25.

| Attribute | Deployed value |
|---|---|
| Subscription | Contoso Fx (`3377065c-bf76-4767-a982-32bce4ffb592`) |
| Resource group | `rg-novasteelv3-demo-sc` |
| Primary region | Sweden Central |
| Portal | `https://novasteelv3-portal.calmbeach-dbad72b1.swedencentral.azurecontainerapps.io` |
| BFF | `https://novasteelv3-bff.calmbeach-dbad72b1.swedencentral.azurecontainerapps.io` |
| Fabric workspace | `https://app.fabric.microsoft.com/groups/3d9c0b49-5201-4914-8149-06071b529918/list` |
| Portal image | `novasteelv3acrnofkol6a.azurecr.io/novasteelv3/portal@sha256:b75dd6d04b9c600f1ede5a07b6cc9d31debfb5b408b2c4477e2a780fb4a83913` |
| BFF image | `novasteelv3acrnofkol6a.azurecr.io/novasteelv3/bff@sha256:71c24c2d3604e27f78b33c3ba62133eee89f34bf2d724cbc1ff34bccab56e5bd` |
| Active revisions | Portal `0000007`; BFF `0000003` |

### Verification evidence

| Check | Result | Evidence |
|---|---|---|
| Public health | PASS | Portal `/healthz`, BFF `/health/live`, and BFF `/health/ready` returned HTTP 200 |
| Complete live demo | PASS | 66/66 checks in 18.222 seconds |
| Browser routes | PASS | Seven persona routes rendered with zero fallback, React, console, or network errors |
| Screenshots | PASS | `artifacts/azure-deployment/screenshots/01-command-center.png` through `07-platform-capacity.png` |
| Fabric capacity | PASS | `novasteelv3fabric`, F2, Active, Sweden Central |
| Fabric SaaS deployment | PASS | `NovaSteelV3-Demo` workspace with 11 deployed items |
| Managed identity | PASS | BFF identity has least-privilege ACR, Event Hubs, Storage, Key Vault, AI Services, and Speech roles |
| Fabric administration | PASS | BFF principal `9b0d0210-a0ab-4970-a4c2-f053e155ac4b` is a capacity administrator |
| Workspace user access | PASS | `frkim@microsoft.com` (`bc35700d-1461-4116-aa62-1d28021eea67`) has the Fabric workspace `Admin` role |
| Nightly pause | PASS | Enabled daily recurrence at 01:00, W. Europe Standard Time |

The deployed Fabric inventory contains one Eventhouse, one KQL database, two
Lakehouses, five notebooks, and two pipelines. Semantic model binding,
Eventstream, RTI dashboard, Activator, Power BI reports, and OneLake security
remain explicit tenant/manual gates.

## 12. Files to generate

| File/artifact | Purpose | Status |
|---|---|---|
| `.azure/deployment-plan.md` | Deployment source of truth | Deployed |
| `services/bff-api/Dockerfile` | BFF image | Complete; validated in `validation/images.md` |
| `apps/portal-shell/Dockerfile` | Portal static image | Complete; validated in `validation/images.md` |
| `.azure/infra/main.bicep` and modules | Deployment-focused infrastructure | Complete |
| `.azure/scripts/*.ps1` | Subscription-pinned build, what-if, and phased deployment orchestration | Complete |

---

## 13. Cost and production caveats

- This creates billable resources, notably Fabric F2, Container Apps, ACR,
  Event Hubs, monitoring, storage, Speech, and AI Services.
- The F2 capacity is configured for nightly pause; pause does not remove all
  storage/monitoring costs.
- The deployment is a synthetic demonstration, not a production OT system.
- Private endpoints/WAF, production Entra authorization, DPO/legal approval,
  tenant model deployment, and full DR/performance work remain production gates.

---

## 13. Next step

Run `azure-deploy` only when explicitly requested; this validation phase did not
deploy any resources.
