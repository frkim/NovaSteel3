# 09 · Vue exécutive

**Audience :** débutant complet dans l'acier et NovaSteel  
**Temps de lecture :** 15 minutes  
**Persona :** Isabelle Moreau — direction générale (COO)  
**Parcours couverts :** `/{site}/executive-overview/overview`, `/{site}/executive-overview/board-report`  
**Dernière mise à jour :** 2026-07-27  
**Langue :** 🇬🇧 [English version](../en/09-executive-overview.md)

---

## Vue exécutive (Executive Overview) — `/{site}/executive-overview/overview`
![Vue exécutive](../screenshots/executive-overview.png)

**En une phrase.** Un cockpit de comité de direction qui transforme la performance de plusieurs sites sidérurgiques en cibles, risques et éléments de retour sur investissement (`apps\analytics-mfe\src\components\screens\ExecutiveOverview.tsx`; `docs\personas\personas-and-journeys.md`).

**Contexte pour débutants.** Une dirigeante ne pilote pas un capteur de four ; elle vérifie si l'entreprise produit moins cher, plus proprement, avec moins de pannes et une meilleure qualité. **Coût par tonne** : euros pour produire une tonne métrique d'acier. **Intensité énergétique** : énergie par tonne ; le brief dit que l'énergie vaut 35 % du coût. **Intensité CO₂** : dioxyde de carbone équivalent par tonne, important à cause du système européen d'échange de quotas d'émission (EU ETS). **Rendement** : part conforme du premier coup. **Arrêt non planifié** : arrêt surprise ; le brief cite 8 M€ par défaillance de revêtement de four (`docs\usecase\usecase.md`; `apps\analytics-mfe\src\proof\proofCatalog.ts`).

**Ce que vous voyez à l'écran.**
1. Le shell affiche site, persona, recherche, capacité Fabric, mode démo et langue ; la bannière violette rappelle que les données sont synthétiques et non opérationnelles (`apps\portal-shell\README.md`; `docs\README.md`).
2. L'en-tête nomme Isabelle Moreau — Executive, responsable de la lecture portefeuille (`docs\personas\personas-and-journeys.md`).
3. Les cartes KPI montrent **Energy / t −14%**, **CO₂ −22%**, **High-grade yield +8%**, **Advance warning 21 d** et **Failures prevented 1**. Les infobulles indiquent ce qui est cible ou modélisé (`ExecutiveOverview.tsx`; `proofCatalog.ts`).
4. Le graphique **Site comparison** compare énergie, CO₂ et rendement pour Moselle, Bremen, Ghent et Bilbao, issus de `executiveSites()` (`ExecutiveOverview.tsx`; `apps\analytics-mfe\src\api\fixtures.ts`).
5. **Target vs actual** affiche 92 %, 88 %, 96 % et 100 %. Ce sont des progrès synthétiques vers cible, pas un audit industriel (`ExecutiveOverview.tsx`).
6. La table **Site scorecard** liste site, delta énergie, delta CO₂, delta rendement et alertes ouvertes (`ExecutiveOverview.tsx`; `docs\ux\dashboard-specification.md`).
7. Les contrôles de panneaux viennent de l'espace Dockview commun (`apps\analytics-mfe\src\components\screens\common.tsx`).

**Pourquoi ce composant a été implémenté.** Le brief cite le coût énergie, la pression CO₂, les pannes de revêtement et les problèmes de qualité haut de gamme (`docs\usecase\usecase.md`). Cette vue regroupe ces douleurs en une histoire d'investissement pour Isabelle (`docs\personas\personas-and-journeys.md`).

**Objectif & preuves (proof of execution).**

| Élément du cas d'usage | ID exigence | Preuve dans l'application | Origine du nombre (route API + fichier source) |
|---|---|---|---|
| Énergie par tonne −14 % | `OUT-01` | KPI “Energy / t −14%” | Pas de BFF ; `ExecutiveOverview.tsx` importe `executiveSites()` depuis `fixtures.ts`. Statut Demo surrogate dans `proofCatalog.ts`. |
| CO₂ −22 % | `OUT-02` | KPI “CO₂ −22%” | Fixture locale ; `proofCatalog.ts` précise que −22 % est une cible. |
| Alerte revêtement à 21 jours | `OUT-03` | KPI “Advance warning 21 d” | Preuve via `DataClient.getLiningForecast()` → `GET /v1/furnaces/{assetId}/lining-forecast` (`dataClient.ts`; `proofCatalog.ts`). |
| Rendement haut de gamme +8 points | `OUT-04` | KPI “High-grade yield +8%” | Preuve via `DataClient.getQualityBatches()` → `GET /v1/quality/batches` (`dataClient.ts`; `proofCatalog.ts`). |
| Cadrage ROI panne évitée | `CHL-03`, `OUT-03` | “Failures prevented 1”, “€8M avoided (modeled)” | Texte dans `ExecutiveOverview.tsx`; 8 M€ dans `docs\usecase\usecase.md`. |

**Comment les données arrivent à l'écran.** `ExecutiveOverview.tsx` → `executiveSites()` → `apps\analytics-mfe\src\api\fixtures.ts`. Les vues de preuve utilisent composant → `DataClient` → route `/v1/...` du BFF → worker ou fixture (`dataClient.ts`; `docs\implementation\api-contracts.md`).

**Honnêteté & limites.** La défense locale est synthétique et consultative ; elle ne se connecte pas à l'OT, aux automates PLC, aux interverrouillages, aux fours ni aux systèmes de production (`docs\README.md`). `OUT-01`, `OUT-02`, `OUT-04` sont Demo surrogate ; `OUT-03` est Met avec caveats (`proofCatalog.ts`).

**Essayez vous-même.** Ouvrez `http://localhost:5266/{site}/executive-overview/overview`.

---

## Rapport conseil (Board Report) — `/{site}/executive-overview/board-report`
![Rapport conseil](../screenshots/executive-board-report.png)

**En une phrase.** Un emplacement réservé pour un rapport Power BI de niveau direction, actif seulement quand Fabric et le flux de jeton seront prêts (`apps\analytics-mfe\src\components\screens\ExecutivePowerBi.tsx`).

**Contexte pour débutants.** Power BI est l'outil Microsoft de reporting. Microsoft Fabric porte les lakehouses, pipelines, modèles sémantiques et rapports Power BI de l'architecture cible (`docs\README.md`; `docs\architecture\solution-architecture.md`). Un rapport conseil emballe la preuve pour revue senior (`docs\ux\dashboard-specification.md`).

**Ce que vous voyez à l'écran.**
1. L'onglet **Board Report** est sélectionné (`ExecutivePowerBi.tsx`).
2. Le panneau rayé **Paginated board report** est volontaire, pas une erreur (`ExecutivePowerBi.tsx`).
3. Le badge affiche **Capacity Paused — start required** ; bon état = Running (`ExecutivePowerBi.tsx`).
4. Le texte indique que le BFF médie les jetons et qu'aucun secret de service n'arrive au navigateur (`ExecutivePowerBi.tsx`; `docs\ux\dashboard-specification.md`).
5. **Open capacity control** envoie vers le contrôle de capacité du shell (`ExecutivePowerBi.tsx`; `apps\portal-shell\README.md`).

**Pourquoi ce composant a été implémenté.** Le persona Isabelle ouvre un cockpit valeur & ROI avant le comité, et le brief exige des résultats attendus visibles (`docs\personas\personas-and-journeys.md`; `docs\usecase\usecase.md`). Cet onglet montre le point d'intégration sans prétendre qu'un tenant Power BI live existe déjà (`docs\README.md`).

**Objectif & preuves (proof of execution).**

| Élément du cas d'usage | ID exigence | Preuve dans l'application | Origine du nombre (route API + fichier source) |
|---|---|---|---|
| Reporting portefeuille | `OUT-01`…`OUT-04` | Onglet Board Report | Placeholder dans `ExecutivePowerBi.tsx`; IDs dans `proofCatalog.ts`. |
| Aucun secret navigateur | `REG-02` | Texte sur le BFF | `ExecutivePowerBi.tsx`; `docs\ux\dashboard-specification.md`. |
| Reporting dépendant de capacité | Surface support | Badge pause + bouton | `client.getCapacity()` → `GET /v1/platform/capacity`; `CapacityPanel.razor`; `CapacityService.cs`. |

**Comment les données arrivent à l'écran.** `ExecutivePowerBi.tsx` → `client.getCapacity()` → `GET /v1/platform/capacity` → adaptateur capacité BFF ou fixture (`dataClient.ts`; `routes.py`; `capacity.py`). Le rapport n'est pas chargé localement.

**Honnêteté & limites.** Le dépôt précise qu'aucun workspace/capacité Fabric ni tenant Power BI n'est prouvé localement (`docs\README.md`).

**Essayez vous-même.** Ouvrez `http://localhost:5266/{site}/executive-overview/board-report`.

---

[◀ Précédent : 08 · Knowledge Hub](08-knowledge-hub.md) · [▲ Index](LISEZMOI.md) · [Suivant ▶ 10 · Device Operations](10-device-operations.md)
