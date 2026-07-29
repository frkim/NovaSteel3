# NovaSteel Fabric data — generate & load

This folder loads the **static** NovaSteel data into Microsoft Fabric. It is the
counterpart to the dynamic (simulator → Eventstream → Eventhouse) stream owned by
another workstream.

## Two layers, one lakehouse (`lh_novasteelv3_core`)

Both layers are deterministic, fully synthetic, and land in the already-deployed
**`lh_novasteelv3_core`** lakehouse — but they serve **different consumers** and
are **different grains**:

| Layer | Tables | Grain | Who reads it |
| --- | --- | --- | --- |
| **Operational envelopes** | `telemetry`, `energy_interval`, `heat_batch`, `quality_measurement`, `model_inference`, `alarm_event`, `maintenance_event`, `operator_knowledge`, `truth_ledger`, `manifest` | Raw simulator **event envelopes** | The **application** — the BFF reads these when `BFF_DATA_SOURCE=fabric` (`services/bff-api/src/bff_api/fabric_source.py`) and reshapes them into exactly the structure `DemoRepository` already serves, so every route keeps working. |
| **Analytical gold** | the eight `fact_*` tables | Daily/shift **star-schema facts** (`contracts/data/gold.v2.json`) | The **semantic model, Power BI and KPI trends** — the −14 % / −22 % / +8 pts / 21-day programme story. |

If you only load the gold layer, switching `BFF_DATA_SOURCE=fabric` finds none of
the tables the app needs and silently falls back to the committed fixture pack —
the application never reads from Fabric. **Load the operational layer to close
that loop; load the gold layer for the analytics.** Both are wanted.

### Operational envelope table shape (why the JSON-document column)

`bff_api.fabric_source._reconstruct_envelope` accepts either a flat row or a
single column carrying the whole envelope as a JSON document. Because these
envelopes carry nested, per-schema-typed `payload` objects, a flat row would be a
lossy, per-dataset column mapping. We use the **JSON-document shape**: each row is
`{event_id, envelope}` where `envelope` is the full envelope serialized as a JSON
**string**, giving a byte-exact `json.loads` round trip that preserves the
guardrail fields (`data_classification` / `privacy_label` / `plant_id`) so
`fabric_source._ensure_fabric_safe` passes. The `event_id` column is only the
MERGE idempotency key (a content hash for the few datasets without an `event_id`);
the BFF ignores it and reconstructs from `envelope`. This round trip is proven
offline by `tests/integration/test_fabric_operational_round_trip.py`.

---

# Analytical (static) gold data — generate & load

The analytical data is a deterministic, reproducible, **24-month** programme dataset
at daily/shift grain that conforms to `contracts/data/gold.v2.json` and lands in the
already-deployed **`lh_novasteelv3_core`** lakehouse as Delta tables.

## 1. Generate the dataset (local, deterministic)

```powershell
# from the repository root
python -m simulator generate-analytics --scenario analytical-programme-24m
# optional: also emit Parquet next to the canonical CSV
python -m simulator generate-analytics --scenario analytical-programme-24m --parquet
```

Output lands in `output\analytical-programme-24m\` (eight `fact_*.csv` files plus
`manifest.json` and `checksums.json`). Validate it:

```powershell
python -m simulator validate-analytics --run-dir output\analytical-programme-24m
```

The validators recompute the headline KPIs **from the rows** (not from the summary)
and assert them against the manifest targets/tolerances:

| KPI | Target | How it is proven |
| --- | --- | --- |
| Energy per ton | −14 % | `Σ energy_gj / Σ crude_steel_tons` after ÷ before |
| Specific CO₂ | −22 % | `Σ total_co2e_t / Σ crude_steel_tons` after ÷ before |
| High-grade first-pass yield | +8 pts | `Σ first_pass_good_tons / Σ attempted_tons` (high-grade) |
| Furnace-lining advance warning | 21 days | first `fact_furnace_rul` alert: `predicted_failure_date − scored_date` |

The lining alert fires exactly when `rul_days_p50 <= 21` **and** `risk_score >= 0.80`,
and those two conditions coincide at 21 days — so the 21-day claim genuinely falls out
of the data and cannot be an arithmetic contradiction (unlike a "High = 7–20 days" band).

## 2. Load into Fabric

The idiomatic Fabric shape is a thin upload to OneLake `Files/` plus a Spark notebook
that MERGEs Delta `Tables/`. Both are provided:

* **`fabric/notebooks/ns-load-analytical-gold.Notebook`** — reads the uploaded CSVs,
  casts them to the deployed core Delta schema, and idempotently MERGEs each fact by
  its idempotency key (re-running is a no-op; a recomputed dataset updates in place).
* **`tools/fabric/Load-AnalyticalGold.ps1`** — resumes the capacity, uploads the CSVs
  to `Files/analytical-gold/analytical-programme-24m/`, optionally triggers the
  notebook, and suspends the capacity again.

```powershell
# End-to-end: resume capacity, upload, run the loader notebook, suspend again.
tools\fabric\Load-AnalyticalGold.ps1 -ResumeCapacity -RunNotebook -SuspendAfter
```

Authentication is **Azure AD only** — the deployment managed identity when it runs in
Azure, otherwise your signed-in `az` context (`az login`). No secrets are stored or read.

## 2b. Load the operational envelope layer (what the app reads)

This is the layer that makes `BFF_DATA_SOURCE=fabric` actually serve from Fabric.

```powershell
# Generate the operational tables from the committed demo-full pack:
python -m simulator generate-operational
# -> output\operational-envelopes\{telemetry,...,truth_ledger,manifest}.ndjson

# Upload + load them with the same tool, selecting the operational layer:
tools\fabric\Load-AnalyticalGold.ps1 -Layer operational -ResumeCapacity -RunNotebook -SuspendAfter
```

The `-Layer operational` switch uploads to `Files/operational-envelopes/` and runs
`fabric/notebooks/ns-load-operational-envelopes.Notebook`, which writes each dataset
as a Delta table named exactly as the BFF expects and MERGEs on `event_id`
(the `manifest` table is overwritten wholesale). Once loaded, set on the BFF:

```
BFF_DATA_SOURCE=fabric
BFF_FABRIC_LAKEHOUSE=lh_novasteelv3_core
BFF_FABRIC_SQL_ENDPOINT=<core lakehouse SQL analytics endpoint>
```

and the application reads its demo data from Fabric, falling back to the committed
fixture pack only if the capacity is asleep or unreachable.

### Capacity resume / suspend (cost control)

The F2 capacity is paused most of the time. Resume it before a load and suspend it
after:

```powershell
$armId = (Get-Content fabric\deployment-parameters\novasteelv3.parameters.json | ConvertFrom-Json).capacity.armResourceId

az resource invoke-action --action resume  --ids $armId   # before the load
az resource invoke-action --action suspend --ids $armId   # after the load
```

> **F2 throttles Spark.** For a one-shot backfill of the full 24-month dataset you can
> temporarily scale up, run the load, then scale back down and suspend:
>
> ```powershell
> az resource update --ids $armId --set sku.name=F8   # temporary headroom
> # ... run Load-AnalyticalGold.ps1 -RunNotebook ...
> az resource update --ids $armId --set sku.name=F2   # back to F2
> az resource invoke-action --action suspend --ids $armId
> ```

### Manual notebook run

If `items.notebookLoadAnalyticalGold.id` is not yet present in the parameters file
(the notebook has not been deployed through `fabric/scripts/Deploy-FabricAssets.ps1`),
upload with `Load-AnalyticalGold.ps1` (omit `-RunNotebook`) and run
**ns-load-analytical-gold** manually from the workspace. The notebook derives the
`Files/` URI from the deployment `{{onelake.coreTablesUri}}` token, so no extra
parameters are required beyond `ENVIRONMENT` and the folder default
(`FILES_SUBPATH = "analytical-gold/analytical-programme-24m"`).

## 3. Idempotency & keys (natural keys, contract v2)

The gold facts use **natural business keys**, not surrogate `*_key` dimension keys.
`contracts/data/gold.v2.json` is **contractVersion 2**: its `keyDesign` block records
that surrogate keys were dropped because this demo runs **no SCD2 dimension load**, so a
`plant_key`/`grade_key`/`asset_key` would reference a dimension row nothing produces. The
contract, the deployed `lh_novasteelv3_core` Delta DDL, the generator
(`simulator/analytics.py::IDEMPOTENCY_KEYS`) and the loader notebook all key on the same
natural columns:

| Table | primaryKey / idempotencyKey |
| --- | --- |
| `fact_energy_daily` | `date_key, plant_id` |
| `fact_emissions_daily` | `date_key, plant_id` |
| `fact_production_shift` | `shift_id` |
| `fact_quality_yield` | `date_key, plant_id, grade_code` |
| `fact_furnace_rul` | `inference_id` |
| `fact_dispatch_recommendation` | `recommendation_id` |
| `fact_knowledge_procedure` | `procedure_id, version` |
| `fact_ai_decision_audit` | `audit_id` (append-only) |

The loader MERGEs on those keys, so uploading the same dataset twice does not duplicate
rows. `simulator/validators/gold_contract.py::validate_gold_contract` asserts the produced
tables against this contract — declared columns and order, key columns present, primary and
idempotency keys unique, and the generator's key matching the contract — so the two can
never silently drift.

## Package feeds

Per repository policy, neither the notebook nor this tooling installs packages from
public registries. If a package is ever required, use the Microsoft-protected feeds
(`https://packagefeedproxy.microsoft.io/pypi/simple`) configured in the repo `pip.conf`.
