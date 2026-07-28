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
## Workflows in this repository

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | PR / push | Lint, pytest, C# build, protected-feed verification, security gates |
| `codeql.yml` | PR / schedule | CodeQL for Python, TypeScript and C# |
| `ci-build-services.yml` | PR / push touching `services/**` | Builds every `services/*/Dockerfile` and, on `main`, pushes to ACR via OIDC |
| `cd-infra.yml` | Manual dispatch per environment | `bicep build` → what-if → `az deployment sub create` |
| `cd-services.yml` | Manual dispatch per environment | Rolls the built images onto the Container Apps |
| `cd-fabric-items.yml` | Manual dispatch per environment | Synchronises Fabric SaaS items through the Fabric REST API |

`ci-build-services.yml` needs `ACR_LOGIN_SERVER` in addition to the variables
above, and builds with `--build-arg PIP_INDEX_URL` pointing at the protected
feed so no public registry is contacted.
