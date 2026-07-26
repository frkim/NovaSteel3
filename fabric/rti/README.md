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
