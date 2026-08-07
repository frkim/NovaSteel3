# GitHub configuration required by the workflows

> Renamed from `.github/README.md` so that the repository landing page renders
> the project [`README.md`](../README.md) instead of this operations note.
> GitHub gives `.github/README.md` precedence over the root file.

Configure protected branches so `verify-protected-feeds`, `security-gates`,
`CodeQL Python and TypeScript`, and `CodeQL CSharp` are required before merge.
Require code-owner review for `contracts/`, `fabric/`, and `infra/`.

Create GitHub Environments named `dev`, `test`, `demo`, and `prod`. Require
reviewers for `demo` and `prod`; only permit production dispatches from `main`.
Each environment needs its own federated Entra identity scoped to its resource
group and these non-secret GitHub variables:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `CONTAINER_RESOURCE_GROUP` and the applicable `*_CONTAINER_APP` variables
- `FABRIC_PARAMETER_FILE` for the Fabric item synchronization workflow
- `NPM_PROTECTED_REGISTRY` (optional) to override the npm feed for React CI; when
  unset, the workflow falls back to the protected default
  `https://packagefeedproxy.microsoft.io/npm/`

The federation subject must match the exact repository and environment. No
client-secret JSON, static cloud credential, or broad subscription role is
accepted by the deployment workflows.

### Repository-level variables for `ci-build-services.yml`

`ci-build-services.yml` runs on `main` (and `workflow_dispatch`) rather than in a
GitHub Environment, so it reads **repository** variables:

| Variable | Current value |
|---|---|
| `AZURE_CLIENT_ID` | client ID of the `novasteelv3-github-oidc` user-assigned managed identity |
| `AZURE_TENANT_ID` | tenant of that identity |
| `AZURE_SUBSCRIPTION_ID` | subscription hosting the demo estate |
| `ACR_LOGIN_SERVER` | `novasteelv3acrnofkol6a.azurecr.io` |

The identity lives in `rg-novasteelv3-demo-sc`, holds **AcrPush** scoped to that
one registry, and trusts a single federated subject:
`repo:frkim/NovaSteel3:ref:refs/heads/main`. It has no other role, and the
registry keeps `adminUserEnabled: false` so RBAC is the only way in.

Recreate it with:

```bash
az identity create -n novasteelv3-github-oidc -g rg-novasteelv3-demo-sc -l swedencentral
az identity federated-credential create -n github-main \
  --identity-name novasteelv3-github-oidc -g rg-novasteelv3-demo-sc \
  --issuer https://token.actions.githubusercontent.com \
  --subject repo:frkim/NovaSteel3:ref:refs/heads/main \
  --audiences api://AzureADTokenExchange
az role assignment create --assignee-object-id <principalId> \
  --assignee-principal-type ServicePrincipal --role AcrPush --scope <acr-resource-id>
```

Pull requests never authenticate to Azure: the login, ACR login, and push steps
are all gated on `github.event_name != 'pull_request'`, so a fork PR still builds
every image but cannot reach the registry. The `changes` job fails fast with an
explicit `::error::` naming any variable that is missing.
## Workflows in this repository

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | PR / push | Lint, pytest, C# build, protected-feed verification, security gates |
| `codeql.yml` | PR / schedule | CodeQL for Python, TypeScript and C# |
| `ci-build-services.yml` | PR / push touching `services/**` | Builds every `services/*/Dockerfile` and, on `main`, pushes to ACR via OIDC and deploys to `demo` |
| `cd-infra.yml` | Manual dispatch per environment | `bicep build` → what-if → `az deployment sub create` |
| `cd-services.yml` | Merge to `main` for `demo`; manual dispatch for `dev`/`test`/`prod` | Rolls the built images onto the Container Apps |
| `cd-fabric-items.yml` | Manual dispatch per environment | Synchronises Fabric SaaS items through the Fabric REST API |
| `presentation.yml` | PR / push touching `docs/presentation/**` | Builds the Marp oral-defense deck and best-effort publishes it to GitHub Pages |

`ci-build-services.yml` needs `ACR_LOGIN_SERVER` in addition to the variables
above. Every `services/*/Dockerfile` writes `/etc/pip.conf` with the protected
index as its only source, so no public registry is contacted during the build.

### How far a merge deploys

A merge to `main` builds the services whose sources changed, pushes them to ACR,
and then calls `cd-services.yml` for `bff-api` and `portal-shell` with
`environment: demo`. The image is passed as the `@sha256:` digest that the build
just produced, never as a tag, so what runs in `demo` is exactly what was built
from that commit.

Only those two services are deployed because only they have a Container App
(`novasteelv3-bff` and `novasteelv3-portal`). The `bff-api` image already
carries `optimizer-worker`, `scoring-worker`, `knowledge-orchestrator` and the
device simulator as build contexts, which is why the change filter routes all of
those paths to it — they ship inside that one image.

The run is not unattended. The `demo` GitHub Environment carries a **required
reviewer**, so a merge queues a deployment that waits for one click. That is the
human sign-off the release gates in
[`security-governance-and-threat-model.md`](../docs/tech/security-governance-and-threat-model.md)
§21 ask for. `dev`, `test` and `prod` still need a manual dispatch of
`cd-services.yml`; the reusable workflow refuses a non-`workflow_dispatch` call
for any environment other than `demo`, so the policy cannot be bypassed by
editing the caller alone.

### Environment configuration behind CD

`cd-services.yml` reads these from the **`demo` GitHub Environment** (the
`AZURE_*` values fall back to the repository variables above):

| Variable | Value |
|---|---|
| `CONTAINER_RESOURCE_GROUP` | `rg-novasteelv3-demo-sc` |
| `BFF_CONTAINER_APP` | `novasteelv3-bff` |
| `PORTAL_CONTAINER_APP` | `novasteelv3-portal` |

A job that declares `environment:` gets an OIDC subject scoped to the
environment rather than to the branch, so `novasteelv3-github-oidc` needs its own
federated credential for it. This repository has GitHub's **immutable-ID** OIDC
subjects enabled, which means the token presents numeric owner and repository IDs
instead of names:

```
repo:frkim@74252080/NovaSteel3@1312557916:environment:demo
```

Both spellings are registered (`github-env-demo` and `github-env-demo-immutable`)
so the login keeps working whichever format GitHub issues, matching the existing
`github-main` / `github-main-immutable` pair used by the branch-scoped jobs. If
`azure/login` fails with `AADSTS700213: No matching federated identity record`,
compare the `subject claim` line in the job log against the credential subjects on
the identity - the name-based form alone is not enough here.

The identity holds `AcrPush` on the registry for the build and `Container Apps
Contributor` on `rg-novasteelv3-demo-sc` for the deployment.

`tests/workflows/` validates these workflows themselves (trigger filters,
`needs` graph, SHA pins, `persist-credentials: false`, and the ban on splicing
`inputs.*` or `github.event.*` into `run:` scripts). It runs in the `ci.yml`
`workflow-lint` job on every pull request and push.
