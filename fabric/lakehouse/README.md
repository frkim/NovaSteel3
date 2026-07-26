# Lakehouse medallion contract

`schema/medallion-catalog.json` is the logical source of truth for table grain,
columns, keys, idempotency, and partitioning. The Spark SQL files are executable
DDL when run with the correct default Lakehouse:

- `sql/00_bronze.sql` on `lh-ns-landing`
- `sql/10_silver.sql` and `sql/20_gold.sql` on `lh-ns-core`

The notebooks use explicit OneLake table roots so the same source can be
parameterized across `dev`, `test`, `demo`, and `prod`.

## Contract rules

- Bronze is append-only and preserves original event/source metadata.
- Silver is the single authoritative deduplication, canonical-unit, event-time
  SCD lookup, and late-data contract for both streaming and batch paths.
- Gold is a star/reporting projection only; reports do not read bronze.
- Historical partitioning is by `event_date`/`date_key`, plant, and dataset.
  Sensor-level partitioning is deliberately prohibited.
- Every unexplained bronze-to-silver discrepancy fails the quality gate.
  Intentional rejects have a closed quarantine reason and retain the original
  payload.
- `fact_ai_decision_audit` is a reporting projection. The application append
  API plus immutable evidence export remains the tamper-evidence boundary.

## Schema evolution

Additive nullable columns are allowed within a major contract version. Required
field removal, key changes, unit semantics, or grain changes require a new major
contract and a replay/migration plan. Never hand-patch gold to hide a source or
silver defect; reprocess from retained bronze.
