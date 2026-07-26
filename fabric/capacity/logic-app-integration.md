# Capacity lifecycle and Logic App integration contract

## Scope

The lifecycle contract applies only to allow-listed `dev`, `test`, and `demo`
Fabric F capacities. `prod` is rejected before any ARM request. The default
01:00 Europe/Luxembourg policy is an orderly **suspend check**, not an
unconditional shutdown.

The ARM operations are:

```text
GET  {capacityResourceId}?api-version=2023-11-01
POST {capacityResourceId}/resume?api-version=2023-11-01
POST {capacityResourceId}/suspend?api-version=2023-11-01
```

A `202 Accepted` response is in progress. Poll `Azure-AsyncOperation` or
`Location`, respect `Retry-After`, and report success only after a terminal
success/readiness result.

## Identity

Use the dedicated user-assigned/system managed identity that has only these
actions on the exact non-production capacity:

- `Microsoft.Fabric/capacities/read`
- `Microsoft.Fabric/capacities/write`
- `Microsoft.Fabric/capacities/suspend/action`
- `Microsoft.Fabric/capacities/resume/action`

It receives no Fabric workspace, OneLake, Key Vault-secret, Foundry, or broad
resource-group/subscription Contributor role.

## Logic App integration sequence

1. A recurrence trigger runs daily at `01:00` using the
   **Europe/Luxembourg** time-zone setting. Test both DST transitions.
2. Generate one correlation ID and read the capacity state.
3. Verify the exact resource ID is on the workflow allow-list and the
   environment tag/name is not `prod`.
4. Call the network-restricted internal BFF operation
   `POST /internal/v1/platform/capacity/lifecycle-check`. It returns an object
   conforming to `precondition-evidence.schema.json`.
5. Validate that evidence is fresh and that:
   - simulator is stopped;
   - relay is drained or an explicit replay checkpoint exists;
   - no protected rehearsal is active;
   - no pipeline/notebook/semantic refresh is in a critical phase;
   - no approved consumer operation is active;
   - no budget/policy block exists.
6. If any check fails, persist `SKIPPED_BUSY`, notify Platform Ops, and leave
   the capacity running.
7. If safe, call ARM suspend with the Logic App managed identity and poll the
   long-running operation.
8. Persist the lifecycle result fields from `lifecycle-result.schema.json` to
   the append-only audit path/Log Analytics and alert once on terminal failure.

`scripts/Invoke-FabricCapacityLifecycle.ps1` implements the same contract for
Azure Automation/runbook use and for integration testing. A Logic App can call
the script through an approved Automation job or implement the same HTTP steps;
the script is not a reason to store a credential in a workflow.

## Resume/readiness

A human GUI request is mediated by the BFF, not the browser calling ARM.
Resume uses the same allow-list and LRO polling, then the BFF verifies:

- Fabric workspaces are available;
- Eventstream/Eventhouse query succeeds;
- Lakehouse and semantic model are reachable;
- required application APIs and budget checks are healthy;
- the demo simulator remains stopped.

Only then does application state become `Running`. Resume never starts a
scenario automatically.

## Explicit non-integrations

- Activator rules never suspend/resume capacity.
- No production capacity ID is accepted by the schedule, script, or BFF.
- No Logic App action writes to OT, a production setpoint, or a schedule.
- Bicep may deploy the Logic App Azure resource, but does not deploy the Fabric
  SaaS items controlled by this folder.
