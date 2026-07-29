# Real-Time Intelligence setup

## Automatable

- Eventhouse and `kql-ns-operations` database creation/update.
- KQL table, mapping, retention, function, and materialized-view definition.
- `es-ns-telemetry-v1` Custom Endpoint source plus KQL/Lakehouse destination
  topology.
- Definition existence and KQL schema validation through the deployment scripts.

## Portal/tenant gates

1. Ensure the Fabric capacity is running.
2. Verify the tenant allows the selected managed identity/service principal to
   use Fabric APIs.
3. Assign the Eventstream publisher identity **Contributor only** on
   `NS-<env>-RTI-Ingress` (or `NS-DEMO-RTI-Ingress`). Do not assign it to
   DataCore, ML, Analytics, or production from a demo identity.
4. Open the deployed Eventstream and retrieve its generated Custom Endpoint
   connection details. Do not commit them. Configure the relay to obtain an
   Entra token and prove publish, retry, duplicate, late, and replay behavior.
5. Verify all five KQL destinations and immutable
   `bronze_event_envelope` delivery before enabling a sustained publisher.
6. Build/import a Real-Time dashboard using `dashboard-spec.json` and the
   read-only queries in `..\kql\dashboard-queries.kql`. Check the current
   tenant-exported `KQLDashboard` definition into source control before adding
   it to automated deployment.
7. Configure Activator from `activator-rules.template.json` only after Teams,
   email, or Power Automate connections pass DLP/licensing review.

Fabric RTI and Activator are operational-awareness/business-workflow features,
not hard real-time safety controls. No rule here pauses a Fabric capacity or
writes to OT.

## Live real-time path runbook (deploy → publish → verify → tear down)

This is the end-to-end procedure that makes the dynamic data stream actually
flow: the simulator publishes synthetic envelopes into the Eventstream Custom
Endpoint, the `route-hot-schemas` operator fans them out on `schema_name`, and
`DirectIngestion` destinations land them in the KQL hot tables while a Lakehouse
destination writes the immutable `bronze_event_envelope` Delta table.

All helper scripts live in `fabric/scripts/`. State and secrets are written to
`fabric/deployment-state/` which is git-ignored (`*` except `.gitignore`).

### 0. Authenticate and resume the capacity

`frkim@microsoft.com` is a **guest** and gets 403s from Fabric. Use the
tenant-native account:

```powershell
az login --tenant MngEnvMCAP336722.onmicrosoft.com --use-device-code
$cap = "/subscriptions/3377065c-bf76-4767-a982-32bce4ffb592/resourceGroups/rg-novasteelv3-demo-sc/providers/Microsoft.Fabric/capacities/novasteelv3fabric"
az resource invoke-action --action resume --ids $cap
```

The F2 capacity is normally **Paused** for cost control. Resume before working
and **suspend again after** (step 5). Never leave it running.

### 1. Deploy (or update) the Eventstream

```powershell
pwsh fabric/scripts/Deploy-FabricEventstream.ps1
```

`Deploy-FabricEventstream.ps1` targets the live **single-workspace**
`NovaSteelV3-Demo` topology (the older `Deploy-FabricAssets.ps1` assumes a
four-workspace `rtiIngress/dataCore/ml/analytics` layout that does not exist
here — that mismatch is why the Eventstream was never deployed). It renders
`items/es-ns-telemetry-v1.Eventstream/eventstream.json`, resolving the
placeholders from `deployment-parameters/novasteelv3.parameters.json`:

- `{{workspace.rtiIngress.id}}` → the one live workspace id.
- `{{item.landingLakehouse.id}}` → landing Lakehouse item id.
- `{{item.kqlOperations.id}}` / `{{item.kqlOperations.displayName}}` → the KQL
  **database** item that holds the hot tables.

**Naming reconciliation.** The definition originally referenced a database
`kql-ns-operations`, but the deployed database is `kql-novasteelv3-operations`.
This is resolved by tokenising the destination `databaseName` to
`{{item.kqlOperations.displayName}}` so the parameters file is the single source
of truth.

**Ingestion mode.** The five Eventhouse destinations use `DirectIngestion` with
an explicit `mappingRuleName` (the named JSON mapping defined in
`items/kql-ns-operations.KQLDatabase/DatabaseSchema.kql`) and a unique
`connectionName`. `ProcessedIngestion` without an inline schema silently ingests
nothing — events reach bronze but every hot table stays empty. `itemId` points
at the **KQL database** item id (not the Eventhouse item id), because the hot
tables live in the non-default database; targeting the Eventhouse item would
resolve to the empty default database.

The deployed item id is recorded in
`deployment-state/novasteelv3-demo-eventstream.json`.

### 2. Retrieve the Custom Endpoint connection (no secrets in source)

```powershell
pwsh fabric/scripts/Get-FabricEventstreamEndpoint.ps1
```

A Custom Endpoint is an **Event Hubs-compatible** ingress that authenticates
with a **SAS key**, not a bearer token. The script fetches the connection and
caches it to the git-ignored
`deployment-state/novasteelv3-demo-eventstream-endpoint.local.json`
(namespace, entity, SAS key name/value). The SAS key is never printed unless you
pass `-ShowSecret`, and never committed. Re-run this after every (re)deploy — a
redeploy rotates the source and its SAS key.

### 3. Publish synthetic events

The simulator's own `simulator publish` sub-command performs a **bearer** POST
aimed at the BFF relay, so it cannot talk to the SAS-authenticated Custom
Endpoint directly. `publish_to_eventstream.py` is the thin transport adapter
that carries the *same* simulator NDJSON envelopes over the Event Hubs REST
`/messages` API using an HMAC-SHA256 SAS token (standard library only):

```powershell
# generate a run first, e.g. `python -m simulator.cli demo --out-dir output\es-verify`
python fabric/scripts/publish_to_eventstream.py `
  --run-dir "output\es-verify" `
  --datasets telemetry alarm_event model_inference `
  --settings-file "fabric\deployment-state\novasteelv3-demo-eventstream-endpoint.local.json" `
  --rate 50
```

The simulator emits `telemetry.v1`, `alarm.v1` and `model-inference.v1`. It does
**not** currently emit `gateway-health.v1` or `quarantine.v1`. To prove those two
routes, generate hand-crafted synthetic envelopes (honouring the
`SYNTHETIC` / `DEMO-NONPERSONAL` / `NS-DEMO-` guardrails):

```powershell
python fabric/scripts/emit_synthetic_edge_envelopes.py --out-dir "output\es-edge"
python fabric/scripts/publish_to_eventstream.py `
  --run-dir "output\es-edge" --datasets gateway_health quarantine `
  --settings-file "fabric\deployment-state\novasteelv3-demo-eventstream-endpoint.local.json"
```

Credentials can also come from `NS_EVENTSTREAM_NAMESPACE`,
`NS_EVENTSTREAM_ENTITY`, `NS_EVENTSTREAM_KEY_NAME` and `NS_EVENTSTREAM_KEY`
environment variables instead of the settings file.

### 4. Verify ingestion

**KQL hot tables** — `POST {clusterUri}/v1/rest/query`. Critically, the
`--resource` for the token **must be the cluster URL itself**; using
`https://kusto.fabric.microsoft.com` fails with `AADSTS500011`. Because several
databases can share the pretty name, pass the **database GUID** in the request
body, not the display name.

```powershell
$cluster = "https://<cluster>.kusto.fabric.microsoft.com"   # from the Eventhouse
$db      = "<kql-database-guid>"                             # items.kqlOperations.id
$tok = az account get-access-token --resource $cluster --query accessToken -o tsv
$h = @{ Authorization = "Bearer $tok"; "Content-Type" = "application/json" }
foreach ($t in "telemetry_hot","alarm_hot","gateway_health_hot","model_inference_hot","ingest_quarantine_hot") {
    $b = @{ db = $db; csl = "$t | count" } | ConvertTo-Json
    (Invoke-RestMethod -Method Post -Uri "$cluster/v1/rest/query" -Headers $h -Body $b).Tables[0].Rows[0][0]
}
```

Allow up to ~5 minutes for queued ingestion. Check
`.show ingestion failures | where FailedOn > ago(30m)` if a table stays empty.

**Lakehouse bronze** — the `landing-bronze-envelope` destination flushes every
30 s. Confirm rows in `bronze_event_envelope` via the Lakehouse SQL endpoint or
by reading the Delta table's active parquet files from OneLake
(`GET https://onelake.dfs.fabric.microsoft.com/{workspaceId}?resource=filesystem&recursive=true&directory={landingLakehouseId}/Tables/bronze_event_envelope`,
token `--resource https://storage.azure.com`).

### 5. Tear down (cost discipline)

```powershell
az resource invoke-action --action suspend --ids $cap
az resource show --ids $cap --query "properties.state" -o tsv   # expect: Paused
```

Always confirm the final state is **Paused**.

### Offline checks (no capacity required)

- `pwsh fabric/scripts/Test-FabricAssetsLocal.ps1` validates the routing
  contract: DirectIngestion mode, `mappingRuleName`/`connectionName`, the
  routing operator's `schema_name` fan-out, and that each named JSON mapping
  exists in the KQL schema.
- `python -m pytest tests/infra/test_fabric_eventstream.py` cross-checks
  placeholder resolution and the KQL-mapping ↔ simulator-envelope alignment
  (including the `model_inference` `$.payload.*` regression guard).
