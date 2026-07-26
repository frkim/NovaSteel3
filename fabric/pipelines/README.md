# Fabric Data Pipeline assets

## Deployable definitions

- `pl-ns-medallion.DataPipeline` runs initialization, bronze→silver,
  silver→gold, and the data-quality gate in dependency order.
- `pl-ns-demo-scoring.DataPipeline` runs the synthetic deterministic scorer and
  then the same quality gate.

Notebook and workspace IDs are rendered from deployment state. A schedule is
not embedded because it must be coordinated with the 01:00 capacity pause
window and protected rehearsal windows.

## Batch source template

`batch-ingestion.template.json` is a connection contract, not a claim that
tenant connections can be created from source control. Data owners must create
Fabric connections using managed/workspace identity or an approved credential
boundary, put only connection GUIDs in environment parameters, and export the
resulting Copy activity definition before enabling automated deployment.

Every incremental copy lands immutable records in a `bronze_batch_*` table and
records the source watermark. Repeated full extracts are not the default.
