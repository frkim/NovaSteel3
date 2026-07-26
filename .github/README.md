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
- `NPM_PROTECTED_REGISTRY` for React CI

The federation subject must match the exact repository and environment. No
client-secret JSON, static cloud credential, or broad subscription role is
accepted by the deployment workflows.
