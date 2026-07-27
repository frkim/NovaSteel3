# 11 · Collections de tableaux de bord

**Audience :** débutant complet dans l'acier et NovaSteel  
**Temps de lecture :** 12 minutes  
**Persona :** tous les personas  
**Parcours couverts :** `/{site}/dashboards/collections`  
**Dernière mise à jour :** 2026-07-27  
**Langue :** 🇬🇧 [English version](../en/11-dashboard-collections.md)

---

## Collections (Dashboard Collections) — `/{site}/dashboards/collections`
![Collections](../screenshots/dashboards-collections.png)

**En une phrase.** Un lanceur guidé : six ensembles de dashboards par rôle, chacun organisé autour d'une question (`apps\analytics-mfe\src\components\screens\DashboardCollections.tsx`; `apps\analytics-mfe\src\components\screens\dashboardCollectionCatalog.ts`).

**Contexte pour débutants.** NovaSteel a beaucoup d'écrans car les décisions acier croisent énergie, dioxyde de carbone (CO₂), santé des fours, qualité, savoir-faire, capteurs et opérations cloud (`docs\ux\dashboard-specification.md`). Un débutant ne sait pas spontanément quelle vue ouvrir après une alerte. Les collections réduisent le coût de navigation, accélèrent l'onboarding par persona et fiabilisent la démo (`DashboardCollections.tsx`; `docs\README.md`).

**Ce que vous voyez à l'écran.**
1. Le titre explique que les collections sont des ensembles prêts à ouvrir, groupés par question (`DashboardCollections.tsx`).
2. La recherche filtre titre, question, persona, tags, narration et cartes (`DashboardCollections.tsx`).
3. Les tags `audit`, `compliance`, `cost`, `daily`, `energy`, `platform`, `quality`, `reliability`, `root-cause` filtrent les cartes (`dashboardCollectionCatalog.ts`).
4. Six cartes sont visibles : **Morning shift handover**, **Furnace risk investigation**, **Energy and cost review**, **Quality escape review**, **Compliance evidence pack**, **Platform health and spend** (`dashboardCollectionCatalog.ts`).
5. Le panneau de détail à droite montre le parcours choisi. La capture montre Morning shift handover avec Command Center, Operations, Device Fleet et Lining Forecast, plus **Open** et **Start** (`DashboardCollections.tsx`).
6. La grille et le détail sont des panneaux Dockview (`apps\analytics-mfe\src\components\screens\common.tsx`).

**Toutes les collections du catalogue.**

| Collection | Question traitée | Persona cible | Vues ouvertes |
|---|---|---|---|
| Morning shift handover | What changed overnight and what must this shift act on first? | Plant Manager | Command Center → Operations → Device Fleet → Lining Forecast (`dashboardCollectionCatalog.ts`) |
| Furnace risk investigation | Is the lining risk real, and what is driving it? | Maintenance / Reliability Engineer | Lining Forecast → Thermal Explorer → Sensor Explorer → Maintenance Planner (`dashboardCollectionCatalog.ts`) |
| Energy and cost review | Where is the next megawatt-hour of saving, and what does it cost in CO₂? | Energy Manager | Spot & Schedule → Load-Shift Simulator → Emissions Ledger → ETS Exposure (`dashboardCollectionCatalog.ts`) |
| Quality escape review | Which batches are at risk and what is the common cause? | Quality Engineer | Batch Quality → Defect Analytics (SPC) → Sensor Explorer (`dashboardCollectionCatalog.ts`) |
| Compliance evidence pack | Can we prove how every automated recommendation was decided? | Sustainability Officer / Auditor | Audit & Reports → Emissions Ledger → Procedures (`dashboardCollectionCatalog.ts`) |
| Platform health and spend | Is the platform healthy, and what is it costing us? | Platform Ops | Fabric Capacity → Jobs & Pipelines → Simulator Control → Cost & Telemetry (`dashboardCollectionCatalog.ts`) |

**Pourquoi ce composant a été implémenté.** Le brief demande de réduire l'énergie, prédire les pannes, améliorer la qualité et capturer l'expertise (`docs\usecase\usecase.md`). Ces preuves sont réparties dans plusieurs écrans ; le lanceur crée des parcours guidés pour les rôles, la démo et l'examen (`docs\ux\dashboard-specification.md`; `docs\demo\demo-runbook.md`).

**Objectif & preuves (proof of execution).**

| Élément du cas d'usage | ID exigence | Preuve dans l'application | Origine du nombre (route API + fichier source) |
|---|---|---|---|
| Optimisation énergie et CO₂ | `CHL-01`, `CHL-02`, `OBJ-01`, `AI-02` | “Energy and cost review” | Lanceur statique dans `dashboardCollectionCatalog.ts`; preuves via `POST /v1/energy/schedules:simulate` et routes durabilité (`dataClient.ts`). |
| Prédiction de panne four | `CHL-03`, `OBJ-02`, `OUT-03`, `AI-01` | “Furnace risk investigation” | Catalogue statique ; preuve `GET /v1/furnaces/{assetId}/lining-forecast` (`dataClient.ts`; `proofCatalog.ts`). |
| Qualité | `CHL-04`, `OBJ-03`, `OUT-04` | “Quality escape review” | Routes `GET /v1/quality/batches` et `POST /v1/quality/what-if` (`dataClient.ts`; `proofCatalog.ts`). |
| Supervision humaine et audit | `REG-02`, `REG-03` | “Compliance evidence pack” | Routes audit/durabilité dans `docs\implementation\api-contracts.md`; cartes dans `dashboardCollectionCatalog.ts`. |
| Santé et coût plateforme | Surface support | “Platform health and spend” | `GET /v1/platform/capacity`; `dashboardCollectionCatalog.ts`; `routes.py`. |

**Comment les données arrivent à l'écran.** `DashboardCollections.tsx` → `dashboardCollections` et `dashboardCollectionTags` → aucun BFF. **Start** et **Open** émettent `nav.intent` vers `/{site}/{section}/{subView}` ; la vue cible appelle ensuite son `DataClient` si nécessaire (`DashboardCollections.tsx`; `apps\analytics-mfe\src\api\dataClient.ts`).

**Honnêteté & limites.** Les collections prouvent la navigation et l'onboarding, pas le résultat métier à elles seules. La preuve reste dans les vues de destination et dans `apps\analytics-mfe\src\proof\proofCatalog.ts`. Les routes statiques doivent suivre les changements de navigation (`dashboardCollectionCatalog.ts`).

**Essayez vous-même.** Ouvrez `http://localhost:5266/{site}/dashboards/collections`, sélectionnez une carte puis cliquez **Start** ou **Open**.

---

[◀ Précédent : 10 · Device Operations](10-device-operations.md) · [▲ Index](LISEZMOI.md) · [Suivant ▶ 12 · Proof of Execution](12-proof-of-execution.md)
