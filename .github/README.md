# GitHub configuration required by the workflows

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
| `ci-build-services.yml` | PR / push touching `services/**` | Builds every `services/*/Dockerfile` and, on `main`, pushes to ACR via OIDC |
| `cd-infra.yml` | Manual dispatch per environment | `bicep build` → what-if → `az deployment sub create` |
| `cd-services.yml` | Manual dispatch per environment | Rolls the built images onto the Container Apps |
| `cd-fabric-items.yml` | Manual dispatch per environment | Synchronises Fabric SaaS items through the Fabric REST API |
| `presentation.yml` | PR / push touching `docs/presentation/**` | Builds the Marp oral-defense deck and best-effort publishes it to GitHub Pages |

`ci-build-services.yml` needs `ACR_LOGIN_SERVER` in addition to the variables
above. Every `services/*/Dockerfile` writes `/etc/pip.conf` with the protected
index as its only source, so no public registry is contacted during the build.

`tests/workflows/` validates these workflows themselves (trigger filters,
`needs` graph, SHA pins, `persist-credentials: false`, and the ban on splicing
`inputs.*` or `github.event.*` into `run:` scripts). It runs in the `ci.yml`
`workflow-lint` job on every pull request and push.
