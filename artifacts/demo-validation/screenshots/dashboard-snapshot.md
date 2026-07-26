# NovaSteel demo - on-screen value snapshot (rendered from live BFF responses)

> Text render of the six demo moments as the presenter reads them on screen.
> Pixel screenshots require the presenter browser (Playwright not available offline).
> Source: live HTTP responses captured under artifacts/demo-validation/http.

## DM-1 Command Center (Plant Manager)
- Banner: Synthetic demo data — not for operational control
- Site: NS-DEMO-LUX-01
  - plannedTonnage: 960.0
  - energyConsumptionMwh: 1016.38
  - energyDispatchSavingsTargetPct: 10.4
  - scope2KgCo2e: 165879.67
  - qualityPredictedFirstPassYieldPct: 88.0
  - liningRulDaysP50: 21.0
  - openAlerts: 1

## DM-3 Furnace lining RUL (Reliability Engineer)
- LUX-BF-01 / HEARTH-SECTOR-07: P50 **21.0 d**, P10 16.8 / P90 27.5, risk 0.87 (HIGH)
- Work order WO-DEMO-LUX-1042 - status PLANNED_INSPECTION (synthetic, advisory)

## DM-2 Energy dispatch (Energy Manager)
- Recommendation REC-EB7A0DEDE29F  status PENDING_APPROVAL
- Baseline EUR 37109.1 -> Optimized EUR 33419.12
- Savings: cost 9.94%  peak -5.16%  CO2 8.35%
- Tonnage 960.0 = 960.0 | hard violations 0

## DM-4 Quality what-if (Quality Engineer)
- Predicted first-pass yield 88.0% -> 95.0% (operationalWrite=False)

## DM-6 Sustainability
- {"site": "NS-DEMO-LUX-01", "energyConsumptionMwh": 1016.38, "scope1KgCo2e": 1368000.0, "scope2KgCo2e": 165879.67, "etsAllowancePriceEurTonne": 86.0, "modeledDispatchCo2ReductionPct": 8.7, "synthetic": true, "dataClassification": "SYNTHETIC"}

## DM-5 Operator knowledge
- Transcript keys: ['classification', 'language', 'segments', 'status']

## Audit evidence
- Append-only decisions total: 7