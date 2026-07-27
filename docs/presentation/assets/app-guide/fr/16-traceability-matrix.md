# 16 · Matrice de traçabilité — écran ↔ cas d'usage ↔ preuve

**Public visé :** toute personne devant démontrer que NovaSteel répond réellement au cas d'usage AxelorMetal — examinateur, membre du jury, nouvel arrivant dans l'équipe.
**Temps de lecture :** ~12 minutes (ou 30 secondes s'il ne vous faut qu'une seule ligne).
**Écrans couverts :** les 31 écrans.
**Dernière mise à jour :** 2026-07-27
**Langue :** 🇬🇧 [English version](../en/16-traceability-matrix.md)

---

## 1. Pourquoi cette page existe

Une démonstration *impressionnante* ne prouve rien en soi. Ce qui prouve quelque chose,
c'est une **boucle fermée** :

```
problème métier  →  un écran qui le traite  →  un chiffre affiché sur cet écran
      →  la route d'API qui a produit ce chiffre  →  le fichier source qui l'a calculé
      →  un test automatisé qui verrouille le comportement
```

Cette page est cette boucle, écrite une fois pour chaque écran et chaque exigence. Si
vous ne devez lire qu'un seul fichier de ce guide avant de défendre l'application,
lisez celui-ci et [12 · Preuve d'exécution](12-proof-of-execution.md).

Deux conventions utilisées partout :

| Convention | Signification |
|---|---|
| **Identifiant d'exigence** | Un identifiant stable (`REG-01`, `CHL-03`, `OUT-02`, `AI-01`…) pour une ligne du cahier des charges. Défini dans `apps/analytics-mfe/src/proof/proofCatalog.ts`. |
| **Statut** | `Met` (atteint) = cela fonctionne. `Partial` (partiel) = cela fonctionne mais de façon plus étroite que le cahier des charges. `Demo surrogate` (substitut de démonstration) = le *mécanisme* est réel, le *chiffre annoncé* est une cible calculée à partir de données synthétiques, et il est étiqueté comme cible partout dans l'interface. |

> **L'honnêteté d'abord.** Tous les chiffres visibles dans l'application proviennent d'un
> jeu de données **synthétique** et déterministe. NovaSteel est **purement consultatif
> (advisory-only)** : il n'écrit jamais de consigne (setpoint), ne dialogue jamais avec
> un automate (PLC) et ne touche jamais à un verrouillage de sécurité.

---

## 2. Le cas d'usage en un tableau

Source : [`docs/usecase/usecase.md`](../../../../usecase/usecase.md).

| Défi métier | Ce qu'il coûte à AxelorMetal | Identifiant | Écran principal |
|---|---|---|---|
| L'énergie représente 35 % du coût de production, sans optimisation temps réel | Le premier poste de coût pilotable | `CHL-01` | Energy Optimization › Spot & Schedule |
| CO₂ sous pression des pénalités du SEQE-UE (EU ETS) | Une facture carbone qui croît avec le prix du quota | `CHL-02` | Sustainability › Emissions Ledger |
| L'usure du garnissage réfractaire est imprévisible | **8 M€ par défaillance catastrophique** | `CHL-03` | Furnace Health › Lining Forecast |
| Irrégularité qualité sur les aciers haut de gamme pour l'automobile | Bobines rebutées, contrats perdus | `CHL-04` | Quality › Batch Quality |
| Départs en retraite plus rapides que la captation du savoir | Une expertise tacite irremplaçable quitte l'usine | `CHL-05` | Knowledge Hub › Procedures |

| Objectif de transformation | Identifiant | Écran principal |
|---|---|---|
| Réduire la consommation d'énergie | `OBJ-01` | Energy Optimization › Spot & Schedule |
| Prédire les défaillances d'équipement | `OBJ-02` | Furnace Health › Lining Forecast |
| Améliorer la qualité de l'acier | `OBJ-03` | Quality › Batch Quality |
| Capter et structurer l'expertise opérationnelle | `OBJ-04` | Knowledge Hub › Capture Status |

| Résultat attendu | Cible | Identifiant | Statut | Écran principal |
|---|---|---|---|---|
| Consommation d'énergie par tonne | −14 % kWh/t | `OUT-01` | Substitut de démo | Command Center › Overview |
| Émissions de CO₂ | −22 % | `OUT-02` | Substitut de démo | Sustainability › Emissions Ledger |
| Alerte avant défaillance du garnissage | 21 jours | `OUT-03` | **Atteint** | Furnace Health › Lining Forecast |
| Rendement acier haut de gamme | +8 pts au premier passage | `OUT-04` | Substitut de démo | Quality › Batch Quality |

| Point d'infusion IA | Identifiant | Statut | Écran principal |
|---|---|---|---|
| Un modèle ML informé par la physique prédit la dégradation du garnissage à partir des signatures thermiques | `AI-01` | Atteint | Furnace Health › Thermal Explorer |
| Un agent d'optimisation de la consommation planifie autour des prix spot | `AI-02` | Atteint | Energy Optimization › Load-Shift Simulator |
| Un système GenAI interroge les opérateurs et structure une bibliothèque de procédures | `AI-03` | Atteint | Knowledge Hub › Procedures |

| Contexte réglementaire | Identifiant | Statut | Écran principal |
|---|---|---|---|
| RGPD (GDPR) — données personnelles licites, minimisées, effaçables | `REG-01` | Atteint | Sustainability › Audit & Reports |
| Règlement européen sur l'IA (EU AI Act) — supervision humaine et transparence | `REG-02` | Atteint | Sustainability › Audit & Reports |
| Directives sectorielles — comptabilité et déclaration SEQE-UE | `REG-03` | Partiel | Sustainability › ETS Exposure |

**Totaux :** 19 exigences — 15 pleinement atteintes, 1 partielle, 3 substituts de démonstration.

---

## 3. Matrice écran → exigence (les 31 écrans)

La grammaire d'URL est `/{site}/{section}/{subView}`, par exemple
`http://localhost:5266/lu/furnace-health/lining-forecast`. `{site}` vaut `lu`, `de`, `be` ou `es`.

### Exploitation quotidienne (Daily operations)

| N° | Écran | Route | Persona | Prouve | Chapitre du guide |
|---|---|---|---|---|---|
| 1 | Command Center | `command-center/overview` | Marc Weber — directeur d'usine | `OUT-01`, et point d'entrée de triage vers tous les autres | [03](03-command-center-and-operations.md) |
| 2 | Operations | `operations/overview` | Marc Weber — directeur d'usine | `CHL-01`…`CHL-04` (surface opérationnelle) | [03](03-command-center-and-operations.md) |
| 3 | Lining Forecast | `furnace-health/lining-forecast` | Elena Duarte / Tomás Rossi | `CHL-03`, `OBJ-02`, `OUT-03` | [04](04-furnace-health.md) |
| 4 | Thermal Explorer | `furnace-health/thermal-explorer` | Elena Duarte — opératrice de haut fourneau | `AI-01` | [04](04-furnace-health.md) |
| 5 | Maintenance Planner | `furnace-health/maintenance-planner` | Tomás Rossi — ingénieur maintenance | `OBJ-02`, `OUT-03` | [04](04-furnace-health.md) |
| 6 | Spot & Schedule | `energy-optimization/spot-price-schedule` | Sofia Lindqvist — responsable énergie | `CHL-01`, `OBJ-01`, `REG-02` (validation humaine) | [05](05-energy-optimization.md) |
| 7 | Load-Shift Simulator | `energy-optimization/load-shift-simulator` | Sofia Lindqvist — responsable énergie | `AI-02` | [05](05-energy-optimization.md) |
| 8 | Batch Quality | `quality/batches` | Jens Bakker — ingénieur qualité | `CHL-04`, `OBJ-03`, `OUT-04` | [06](06-quality.md) |
| 9 | Defect Analytics (SPC) | `quality/spc` | Jens Bakker — ingénieur qualité | `OBJ-03` | [06](06-quality.md) |

### Pilotage et gouvernance (Insight & governance)

| N° | Écran | Route | Persona | Prouve | Chapitre du guide |
|---|---|---|---|---|---|
| 10 | Executive Overview | `executive-overview/overview` | Isabelle Moreau — direction générale | `OUT-01`…`OUT-04` (consolidation) | [09](09-executive-overview.md) |
| 11 | Board Report | `executive-overview/board-report` | Isabelle Moreau — direction générale | `OUT-01`…`OUT-04` (reporting) | [09](09-executive-overview.md) |
| 12 | Emissions Ledger | `sustainability-compliance/emissions-ledger` | Amina Haddad — responsable RSE | `CHL-02`, `OUT-02` | [07](07-sustainability-and-compliance.md) |
| 13 | ETS Exposure | `sustainability-compliance/ets-exposure` | Amina Haddad — responsable RSE | `REG-03` | [07](07-sustainability-and-compliance.md) |
| 14 | Audit & Reports | `sustainability-compliance/audit` | Amina Haddad — responsable RSE | `REG-01`, `REG-02` | [07](07-sustainability-and-compliance.md) |
| 15 | Procedures | `knowledge-hub/procedures` | Pieter Claes — ingénieur connaissance | `CHL-05`, `AI-03` | [08](08-knowledge-hub.md) |
| 16 | Capture Status | `knowledge-hub/capture-status` | Pieter Claes — ingénieur connaissance | `OBJ-04`, `REG-01` | [08](08-knowledge-hub.md) |
| 17 | Dashboard Collections | `dashboards/collections` | Tous les personas | Navigation / prise en main | [11](11-dashboard-collections.md) |
| 18 | Requirement Register | `proof-of-execution/requirements` | Tous les personas | **Les 19 identifiants** | [12](12-proof-of-execution.md) |
| 19 | Use Case | `proof-of-execution/use-case` | Tous les personas | Le cahier des charges lui-même, rendu dans l'application | [12](12-proof-of-execution.md) |
| 20 | Technical Requirements | `technical-requirements/criteria` | Tous les personas | La grille technique, auto-évaluée 56/60 | [12](12-proof-of-execution.md) |

### Plateforme et référence (Platform & reference)

| N° | Écran | Route | Persona | Prouve | Chapitre du guide |
|---|---|---|---|---|---|
| 21 | Device Fleet | `device-operations/fleet` | Rui Almeida — ingénieur systèmes OT | Provenance des données pour `AI-01` | [10](10-device-operations.md) |
| 22 | Sensor Explorer | `device-operations/sensors` | Rui Almeida — ingénieur systèmes OT | Provenance des données pour `AI-01` | [10](10-device-operations.md) |
| 23 | Simulator Control | `device-operations/simulator` | Rui Almeida — ingénieur systèmes OT | Déterminisme / reproductibilité | [10](10-device-operations.md) |
| 24 | Fabric Capacity | `platform-ops/capacity` | Nils Andersen — exploitation plateforme | Maîtrise des coûts, contrôle des rôles | [13](13-platform-ops.md) |
| 25 | Jobs & Pipelines | `platform-ops/jobs` | Nils Andersen — exploitation plateforme | Observabilité des pipelines de données | [13](13-platform-ops.md) |
| 26 | Cost & Telemetry | `platform-ops/cost-telemetry` | Nils Andersen — exploitation plateforme | Transparence du coût d'exploitation | [13](13-platform-ops.md) |
| 27 | AxelorMetal — Home | `company-website/home` | Site public | Récit métier | [02](02-company-website.md) |
| 28 | AxelorMetal — Company | `company-website/company` | Site public | Récit métier | [02](02-company-website.md) |
| 29 | AxelorMetal — Products & Markets | `company-website/products` | Site public | Récit métier | [02](02-company-website.md) |
| 30 | AxelorMetal — Steel Knowledge | `company-website/steel-knowledge` | Site public | Point d'entrée pour les débutants | [02](02-company-website.md) |
| 31 | AxelorMetal — Contact | `company-website/contact` | Site public | Récit métier | [02](02-company-website.md) |

---

## 4. Matrice exigence → preuve

La version faisant autorité, lisible par machine, est
[`apps/analytics-mfe/src/proof/proofCatalog.ts`](../../../../../apps/analytics-mfe/src/proof/proofCatalog.ts).
L'écran **Proof of Execution** dans l'application et
[`docs/presentation/proof_of_execution.md`](../../../proof_of_execution.md) sont deux
projections de ce fichier unique : ils ne peuvent donc pas diverger silencieusement.

| ID | Exigence (résumé) | Statut | D'où vient le chiffre | Réserve annoncée |
|---|---|---|---|---|
| `REG-01` | RGPD : données opérateur licites, minimisées, effaçables | Atteint | `services/knowledge-orchestrator/src/knowledge_orchestrator/erasure.py`, `pii.py`, `consent.py` ; `POST /v1/privacy/erasure-requests` | L'expiration planifiée de rétention est une procédure d'exploitation, pas un travail automatisé |
| `REG-02` | AI Act : supervision humaine, pas d'auto-validation | Atteint | `state_graph.py` (nœud `IN_REVIEW` verrouillé), `tools.py` (liste d'outils interdits), `prompt_defense.py`, `content_safety.py`, `infra/bicep/modules/alerts.bicep` | La classification Annexe III et la fiche de modèle sont documentaires, pas des objets de code |
| `REG-03` | Comptabilité et déclaration SEQE-UE | **Partiel** | `fabric/notebooks/ns-silver-to-gold.Notebook` ; `GET /v1/sustainability/summary`, `/v1/sustainability/emissions` | Le référentiel d'allocation (1,50 t/t d'acier) et le prix du quota sont des constantes de démonstration ; le MACF (CBAM) n'est pas implémenté |
| `CHL-01` | Énergie = 35 % du coût, sans optimisation temps réel | Atteint | MILP `services/optimizer-worker` (PuLP/CBC) ; `POST /v1/energy/schedules:simulate` | Prix spot issus de fixtures, pas d'un flux ENTSO-E réel |
| `CHL-02` | CO₂ sous pression des pénalités SEQE | Atteint | Registre d'émissions + calcul Scope 1/2 en couche gold | Facteurs d'émission synthétiques |
| `CHL-03` | Usure du garnissage imprévisible, 8 M€ par défaillance | Atteint | Régression `services/scoring-worker` sur l'épaisseur réfractaire et le flux thermique, P10/P50/P90 + confiance | Historique thermique synthétique |
| `CHL-04` | Irrégularité qualité sur acier automobile | Atteint | Écrans qualité lot + généalogie + SPC | Prédit et mesuré en laboratoire clairement distingués |
| `CHL-05` | Départs en retraite, savoir qui disparaît | Atteint | Chaîne captation → revue → publication de l'orchestrateur de connaissance | La reconnaissance vocale s'exécute localement sur des fixtures |
| `OBJ-01` | Réduire la consommation d'énergie | Atteint | Proposition de l'optimiseur + validation humaine | Consultatif uniquement |
| `OBJ-02` | Prédire les défaillances d'équipement | Atteint | Prévision de RUL + création d'ordre de travail (`POST /v1/workorders`) | Ordres de travail synthétiques ; pas d'intégration GMAO |
| `OBJ-03` | Améliorer la qualité de l'acier | Atteint | Qualité de lot, what-if borné, SPC | Consultatif uniquement |
| `OBJ-04` | Capter et structurer l'expertise | Atteint | Consentement → entretien → brouillon → revue → publication | Soumis au consentement et à validation humaine |
| `OUT-01` | −14 % d'énergie par tonne | **Substitut de démo** | Carte KPI du Command Center, étiquetée comme *cible* | Chiffre dérivé du jeu de données synthétique |
| `OUT-02` | −22 % de CO₂ | **Substitut de démo** | Emissions Ledger, étiqueté comme *cible* | Chiffre dérivé du jeu de données synthétique |
| `OUT-03` | Alerte garnissage à 21 jours | **Atteint** | RUL P50 ≥ 21 jours, verrouillé par `tests/e2e/test_local_demo_persona_journeys.py` | Le mécanisme et l'horizon de 21 jours sont réels, sur entrée synthétique |
| `OUT-04` | +8 pts de rendement haut de gamme | **Substitut de démo** | Batch Quality, étiqueté comme *cible* | Chiffre dérivé du jeu de données synthétique |
| `AI-01` | ML informé par la physique sur signatures thermiques | Atteint | Régression MCO (OLS) `services/scoring-worker` sur variables thermiques | Ce n'est pas un modèle profond entraîné, mais une régression transparente et explicable |
| `AI-02` | Agent d'optimisation de la consommation | Atteint | Identité d'agent nommée + liste blanche d'outils + MILP + passage de main vers le RUL | Il propose, il n'engage jamais |
| `AI-03` | Captation de connaissance par GenAI | Atteint | Extraction ancrée + boucle critique (`critic.py`) + recherche hybride avec obligation de citation | Adaptateur local sur fixtures lorsqu'aucun point de terminaison Foundry n'est configuré |

---

## 5. Les preuves que vous pouvez exécuter vous-même

| Affirmation | Commande (depuis la racine du dépôt) |
|---|---|
| Le front-end se comporte comme documenté | `npm run test:frontend` |
| L'API BFF se comporte comme documenté | `npm run test:bff` |
| Les parcours par persona bouclent de bout en bout | `pytest tests/e2e` |
| La liste blanche des SKU de capacité Fabric est appliquée aux quatre endroits | `pytest tests/infra/test_capacity_sku_allow_list.py` |
| L'ensemble de la solution compile | `npm run build` |

Les résultats agrégés sont consignés dans [`docs/validation-report.md`](../../../../validation-report.md)
et `artifacts/demo-validation/rehearsal-report.md`.

---

## 6. Comment utiliser cette matrice lors d'une soutenance

1. **Ouvrez le registre dans l'application** (`/lu/proof-of-execution/requirements`) à côté
   de cette page. Tout ce que vous affirmez ici peut y être montré en direct, en un clic.
2. **N'annoncez jamais un résultat comme atteint.** Dites : « le mécanisme fonctionne ;
   les −14 % sont une cible calculée à partir du jeu de données synthétique, et l'interface
   l'étiquette comme une cible ». Le catalogue dit exactement la même chose : un jury qui
   fouille le dépôt y trouve une concordance, pas une contradiction.
3. **Commencez par `OUT-03`.** C'est le seul résultat marqué **Atteint** : l'alerte
   garnissage à 21 jours est produite par une vraie régression et verrouillée par un test
   automatisé.
4. **Répondez à « d'où vient ce chiffre ? » par un chemin de fichier**, pas par un adjectif.
   La 4ᵉ colonne du §4 vous donne ce chemin pour chaque exigence.

---

◀ [15 · Glossaire](15-glossary.md) · ▲ [Sommaire](LISEZMOI.md) · [17 · Ce qui se passe derrière les écrans](17-how-it-works-behind-the-screens.md) ▶

