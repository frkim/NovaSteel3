# 03 — Command Center et Operations

**Public visé :** personnes totalement débutantes dans l’acier et NovaSteel  
**Temps de lecture :** 18 minutes  
**Persona :** Marc Weber — Plant Manager  
**Routes couvertes :** `/{site}/command-center/overview`, `/{site}/operations/overview`  
**Dernière mise à jour :** 2026-07-27  
[🇬🇧 English version](../en/03-command-center-and-operations.md)

## Comment lire un tableau de bord NovaSteel

| Brique | Signification | Source |
|---|---|---|
| Bannière données synthétiques | Données de démonstration uniquement, pas de pilotage opérationnel. | `docs\demo\demo-runbook.md:37-44` |
| Pastille persona | Affiche le rôle actif, par exemple « Marc Weber - Plant Manager ». | `apps\analytics-mfe\src\personaRoutes.ts:18-33` |
| Panneaux dockés | Redimensionnement, réorganisation, maximisation et reset ; les panneaux structurels ne sont pas fermables. | `apps\analytics-mfe\src\components\screens\common.tsx:158-187`; `docs\ux\dashboard-specification.md:407-442` |
| Carte KPI | Libellé, valeur, unité, flèche de tendance, écart, cible, fraîcheur, aide et parfois popover “Why?”. | `apps\analytics-mfe\src\components\primitives\KpiCard.tsx:29-49`, `apps\analytics-mfe\src\components\primitives\KpiCard.tsx:97-144` |
| Point de fraîcheur | Frais, obsolète ou fixture synthétique de secours. | `apps\analytics-mfe\src\components\primitives\FreshnessBadge.tsx:14-38` |
| Couleurs de sévérité | Toujours avec texte et glyphe, jamais seulement la couleur. | `apps\analytics-mfe\src\components\primitives\SeverityPill.tsx:10-33`; `docs\ux\dashboard-specification.md:334-343` |
| Badge de preuve | Relie l’élément visible au registre Proof of Execution. | `apps\analytics-mfe\src\components\primitives\ProofBadge.tsx:13-70` |
| Table de données | Recherche globale, recherche par colonne, tri, choix de colonnes, densité, export, refresh, pagination. | `apps\analytics-mfe\src\components\primitives\DataTable.tsx:248-428` |

**P50** signifie la prédiction médiane : la moitié des résultats plausibles est au-dessus et l’autre moitié en dessous. Un RUL P50 de 21 jours indique que l’estimation centrale du modèle est 21 jours restants (`apps\analytics-mfe\src\components\primitives\ConfidenceMeter.tsx:13-64`). **Confidence %** est la confiance du modèle ou de l’alerte, rendue en pourcentage dans la colonne « Conf. » (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:176-182`).

---

## Command Center — `/{site}/command-center/overview`
![Vue Command Center](../screenshots/command-center-overview.png)

**En une phrase.** Command Center est l’écran de triage inter-personas de Marc Weber : quelle usine exige l’attention, quel KPI est à risque et quelle action ouvrir ensuite.

**Contexte sidérurgique pour débutants.** Un directeur d’usine porte sécurité, production, coût et qualité. MWh signifie mégawattheure, unité d’électricité. CO₂ Scope 2 désigne les émissions liées à l’électricité achetée. RUL (remaining useful life) signifie durée de vie utile restante. Le rendement haut de gamme (high-grade yield) est la part d’acier premium conforme du premier coup. Ces sujets correspondent au persona Marc Weber et aux quatre résultats cibles (`docs\personas\personas-and-journeys.md:67-107`; `docs\specs\solution-requirements.md:55-67`).

**Ce que vous voyez à l’écran.**

1. **Tuiles de statut site.** LU Moselle Integrated Works est orange « Attention » avec une alerte active ; DE Saarbrücken, BE Liège et ES Asturias sont bleus « Healthy ». Bon : Healthy sans alerte ; mauvais : Attention/Critical avec alertes ouvertes (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:186-221`).
2. **KPI consommation d’énergie.** Carte verte, environ 1 016,4 MWh, « −10.4% target », cible « target −14% energy/t ». Bon : énergie par tonne plus basse ; mauvais : hausse ou cible ratée (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:38-52`; `docs\presentation\proof_of_execution.md:317-327`).
3. **KPI CO₂ Scope 2.** Carte verte, environ 165,9 t/day, « −22% target ». Bon : émissions électriques plus basses ; −22 % est une cible, pas une mesure (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:53-67`; `docs\presentation\proof_of_execution.md:328-338`).
4. **KPI revêtement de four RUL.** Carte orange, 21 jours (P50), HEARTH-07, cible « ≥21-day advance warning ». Le revêtement de four (furnace lining) est la couche réfractaire protectrice. Mauvais : durée prévue proche du seuil ; bon : délai suffisant pour une maintenance planifiée (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:68-92`; `docs\presentation\proof_of_execution.md:340-350`).
5. **KPI rendement haut de gamme.** Carte verte, 88 % prédit, « +8% target ». « Predicted » signifie sortie modèle, pas résultat laboratoire final (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:93-107`; `docs\presentation\proof_of_execution.md:352-357`).
6. **KPI alertes ouvertes.** Carte rouge, 1 alerte ouverte dont 1 critique. Bon : zéro critique ; mauvais : carte rouge nécessitant triage (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:108-123`).
7. **Table “Active alerts”.** Colonnes : Severity, Time, Site/Unit, Component, Message, Conf., Status. La ligne visible est CRITICAL pour `LUX-BF-01`, `HEARTH-SECTOR-07`, RUL autour de 21 jours, confiance environ 87 %, statut OPEN (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:163-184`, `apps\analytics-mfe\src\components\screens\CommandCenter.tsx:229-256`).
8. **Contrôles de table.** La barre montre choix de colonnes, densité, export et refresh ; chaque colonne visible a un champ de recherche (`apps\analytics-mfe\src\components\primitives\DataTable.tsx:248-428`).
9. **Next-best actions.** Les cartes recommandent un load shift simulé, une inspection hearth et une revue qualité. « Open » ouvre l’écran propriétaire ; il ne pilote pas l’usine (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:139-161`, `apps\analytics-mfe\src\components\screens\CommandCenter.tsx:260-282`).
10. **Donut “Alert severity mix”.** Le donut résume Critical, Warning et Info. Bon : vide ou faible sévérité ; mauvais : grande part rouge critique (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:127-137`, `apps\analytics-mfe\src\components\screens\CommandCenter.tsx:283-294`).

**Pourquoi ce composant a été implémenté.** Le cas d’usage cite coût énergie, pression CO₂, usure de revêtement imprévisible, qualité et perte de connaissance (`docs\usecase\usecase.md:14-22`). Command Center transforme les quatre premiers en page de triage unique (`docs\ux\dashboard-specification.md:314-333`).

**Objectif & preuves d’exécution.**

| Élément du cas d’usage | ID d’exigence | Preuve dans l’application | Origine du chiffre (route API + fichier source) |
|---|---|---|---|
| Réduire l’énergie | OBJ-01, OUT-01 | KPI énergie avec MWh et `target −14% energy/t`. | `DataClient.getCommandSummary('all')` appelle `GET /v1/command-center/summary?site=all` (`apps\analytics-mfe\src\api\dataClient.ts:155-160`). Le BFF calcule `energyConsumptionMwh` (`services\bff-api\src\bff_api\routes.py:49-59`; `services\bff-api\src\bff_api\repository.py:300-323`). Fallback : `apps\analytics-mfe\src\api\fixtures.ts:459-480`. |
| Réduire le CO₂ | OUT-02 | KPI Scope 2 en tonnes/jour et `−22% target`. | Même route ; `scope2KgCo2e` vient de consommation × intensité carbone (`services\bff-api\src\bff_api\repository.py:300-324`). Limite : `docs\presentation\proof_of_execution.md:328-338`. |
| Prédire les pannes | OBJ-02, OUT-03, AI-01 | KPI RUL 21 jours (P50), cible d’alerte et drivers “Why?”. | Même route ; OUT-03 et AI-01 sont catalogués (`apps\analytics-mfe\src\proof\proofCatalog.ts:465-543`). |
| Améliorer le rendement | OBJ-03, OUT-04 | KPI yield 88 % prédit avec cible +8 %. | Même route ; `qualityPredictedFirstPassYieldPct` (`services\bff-api\src\bff_api\repository.py:324-328`). Limite : `apps\analytics-mfe\src\proof\proofCatalog.ts:495-518`. |
| Triage transverse | CHL-01..CHL-04 | Table et donut montrent les alertes critiques ouvertes. | `DataClient.getAlerts()` appelle `GET /v1/realtime/alerts:poll` via `pollAlerts()` (`apps\analytics-mfe\src\api\dataClient.ts:286-317`). BFF : `AlertEventBuffer` (`services\bff-api\src\bff_api\routes.py:97-116`; `services\bff-api\src\bff_api\services.py:75-84`). |

**Comment les données arrivent à cet écran.** `CommandCenter` → `client.getCommandSummary('all')` et `client.getAlerts()` → `DataClient` → `GET /v1/command-center/summary?site=all` et `GET /v1/realtime/alerts:poll` → `command_summary()` et `AlertEventBuffer`; en cas d’échec, les fixtures déterministes prennent le relais (`apps\analytics-mfe\src\components\screens\CommandCenter.tsx:19-25`; `apps\analytics-mfe\src\api\dataClient.ts:127-160`, `apps\analytics-mfe\src\api\dataClient.ts:286-317`; `services\bff-api\src\bff_api\repository.py:300-341`; `apps\analytics-mfe\src\api\fixtures.ts:221-355`, `apps\analytics-mfe\src\api\fixtures.ts:459-480`).

**Honnêteté & limites.** Les grands chiffres sont des cibles sur données synthétiques, pas des mesures de production. Les actions naviguent ou enregistrent des décisions de démo ; elles ne contrôlent pas les équipements (`docs\presentation\proof_of_execution.md:307-315`; `docs\specs\solution-requirements.md:96-105`).

**Essayez vous-même.** Ouvrez `http://localhost:5266/lu/command-center/overview`, cherchez `HEARTH` dans Active alerts, puis ouvrez l’action d’inspection.

---

## Operations — `/{site}/operations/overview`
![Vue Operations](../screenshots/operations-overview.png)

**En une phrase.** Operations montre la santé de production courante : débit, efficacité équipement, alertes, intensité énergétique, ponctualité, équipes et triage d’incident.

**Contexte sidérurgique pour débutants.** Le débit (throughput) est la vitesse de production en tonnes par heure. OEE (Overall Equipment Effectiveness) combine disponibilité, performance et qualité. L’intensité énergétique (energy intensity) est le coût par tonne d’acier. Un shift board montre l’équipe en poste et la relève. Le triage d’incident classe les anomalies par sévérité (`apps\analytics-mfe\src\components\screens\Operations.tsx:35-49`; `docs\ux\dashboard-specification.md:654-673`).

**Ce que vous voyez à l’écran.**

1. **Bande KPI.** Throughput 128.4 t/h, OEE 84.1 %, Active alerts 1 avec 1 critical, Energy intensity 312 €/t et On-time 96.4 %. Bon : proche des cibles 130 t/h, 85 %, zéro critique, 300 €/t ou moins, 97 % à l’heure (`apps\analytics-mfe\src\components\screens\Operations.tsx:35-41`).
2. **Mini-courbe throughput.** La carte Throughput inclut une petite tendance pour voir la direction immédiatement (`apps\analytics-mfe\src\components\screens\Operations.tsx:25-40`; `apps\analytics-mfe\src\components\primitives\KpiCard.tsx:124-131`).
3. **Graphique “Throughput vs target”.** La ligne bleue représente le débit horaire ; la ligne orange pointillée est la cible 130 t/h. Bon : proche ou au-dessus de la cible sans conduite dangereuse ; mauvais : écart durable (`apps\analytics-mfe\src\components\screens\Operations.tsx:25-33`, `apps\analytics-mfe\src\components\screens\Operations.tsx:55-74`).
4. **Shift board.** Crew A est en poste, Crew B est la suivante avec heure de passation, Crew C est au repos. Bon : responsabilité claire ; mauvais : pas de propriétaire pendant incident (`apps\analytics-mfe\src\components\screens\Operations.tsx:77-97`).
5. **Table “Alerts & incidents”.** Colonnes : Severity, Time, Unit, Type/message, Owner/status. La même alerte CRITICAL hearth apparaît ici, ce qui montre le flux partagé avec Command Center (`apps\analytics-mfe\src\components\screens\Operations.tsx:43-49`, `apps\analytics-mfe\src\components\screens\Operations.tsx:99-113`; `apps\analytics-mfe\src\components\primitives\DataTable.tsx:248-428`).
6. **Pattern IncidentPanel.** Le composant réutilisable `IncidentPanel`, dans le simulateur device, montre incidents actifs, pastilles de sévérité, barres de progression, boutons trigger, dialogues de cible et actions clear. Il n’est pas le graphique principal Operations, mais documente le même modèle de triage simulé (`apps\analytics-mfe\src\components\devices\IncidentPanel.tsx:168-387`).

**Pourquoi ce composant a été implémenté.** Les exigences disent que décisions énergie, qualité et santé d’actifs sont fragmentées entre systèmes (`docs\specs\solution-requirements.md:32-43`). Operations donne à Marc une vue de production vivante avec les alertes critiques visibles.

**Objectif & preuves d’exécution.**

| Élément du cas d’usage | ID d’exigence | Preuve dans l’application | Origine du chiffre (route API + fichier source) |
|---|---|---|---|
| Vue production Plant Manager | CHL-01..CHL-04 contexte | KPI production, OEE, alertes, énergie et livraison. | Throughput/OEE/energy/on-time sont générés dans `Operations.tsx` (`apps\analytics-mfe\src\components\screens\Operations.tsx:25-41`). Le nombre d’alertes utilise `GET /v1/realtime/alerts:poll` (`apps\analytics-mfe\src\api\dataClient.ts:286-317`). |
| Triage alertes/incidents | OBJ-02, OUT-03, AI-01 | L’alerte hearth critique est visible dans Operations. | `Operations` sonde `client.getAlerts()` toutes les 10 s (`apps\analytics-mfe\src\components\screens\Operations.tsx:19-24`). Route BFF : `GET /v1/realtime/alerts:poll` (`services\bff-api\src\bff_api\routes.py:97-116`). Fixture : `apps\analytics-mfe\src\api\fixtures.ts:221-236`. |
| Sensibilité coût énergie | OBJ-01, OUT-01 | KPI Energy intensity à 312 €/t contre cible 300. | Valeur locale dans `Operations.tsx` (`apps\analytics-mfe\src\components\screens\Operations.tsx:35-40`). Preuve OUT-01 : `apps\analytics-mfe\src\proof\proofCatalog.ts:415-438`. |
| Livraison et qualité | OBJ-03, OUT-04 | OEE et On-time indiquent la stabilité pendant le triage. | Valeurs locales dans `Operations.tsx` (`apps\analytics-mfe\src\components\screens\Operations.tsx:35-41`). Preuve OUT-04 : `apps\analytics-mfe\src\proof\proofCatalog.ts:495-518`. |

**Comment les données arrivent à cet écran.** `Operations` → `client.getAlerts()` → `DataClient.getAlerts()` → `pollAlerts()` → `GET /v1/realtime/alerts:poll` → BFF `AlertEventBuffer` initialisé depuis `repository.alerts_rows()` ; fallback : `fixtures.alerts()` (`apps\analytics-mfe\src\components\screens\Operations.tsx:19-24`; `apps\analytics-mfe\src\api\dataClient.ts:286-317`; `services\bff-api\src\bff_api\routes.py:97-116`; `services\bff-api\src\bff_api\services.py:75-84`; `apps\analytics-mfe\src\api\fixtures.ts:221-355`). Les KPI hors alertes et la courbe throughput sont générés dans `Operations.tsx` (`apps\analytics-mfe\src\components\screens\Operations.tsx:25-41`).

**Honnêteté & limites.** Vue opérationnelle synthétique : la courbe throughput est générée côté front-end pour la démo, et le flux d’alertes est synthétique. L’écran aide au triage et à la navigation ; il ne modifie ni fours, ni planning, ni interverrouillages de sécurité (`apps\analytics-mfe\src\components\screens\Operations.tsx:25-41`; `docs\specs\solution-requirements.md:96-105`).

**Essayez vous-même.** Ouvrez `http://localhost:5266/lu/operations/overview`, comparez la ligne bleue à la cible orange, puis cherchez `CRITICAL` dans la table.

---

[◀ Précédent : site corporate AxelorMetal](02-company-website.md) · [▲ Index](LISEZMOI.md) · [Suivant ▶ Furnace Health](04-furnace-health.md)

