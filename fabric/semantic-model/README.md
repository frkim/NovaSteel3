# `sm-ns-operations` Direct Lake semantic model

The TMDL project contains the portable table/relationship/measure metadata for
the documented NovaSteel KPIs. `measures/kpi-measures.json` is the requirements
traceability catalog and `measures/measures.dax` is the readable authoritative
measure pack.

## Deployment gate

The catalog disables semantic-model deployment until
`deploymentOptions.semanticModelBindingValidated` is `true`. Before enabling it:

1. Create or validate the Direct Lake binding to `lh-ns-core` in the Analytics
   workspace and export the tenant definition.
2. Compare the exported partition/source metadata with these TMDL entity
   partitions and update only tenant identifiers/endpoint bindings.
3. Validate every relationship and measure against a fixed synthetic cue set.
4. Configure RLS/OneLake roles with test Entra groups. The application persona
   selector is not an authorization boundary.
5. Apply sensitivity labels and test report export restrictions.
6. Confirm Pro/PPU/trial licensing for every consumer below F64.

The model intentionally excludes 1–10 second raw telemetry. RTI/KQL owns that
surface; this model reads gold Delta facts only.

## KPI conventions

- Ratios use `DIVIDE` and return blank when the denominator is zero.
- Energy and CO2 targets are relative to the effective target row in
  `dim_kpi_target`.
- Predicted and observed values have distinct measures.
- All time calculations use UTC fact timestamps; site-local display is a report
  concern via `dim_calendar`.
- “OEE” is a supporting operational measure and must not be presented as a
  contractual KPI until operations signs off the planned-time and ideal-rate
  definitions.
