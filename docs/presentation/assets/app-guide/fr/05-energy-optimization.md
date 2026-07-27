# 05 · Optimisation de l'énergie — Spot & Schedule et Load-Shift Simulator

**Public visé :** une personne totalement débutante en sidérurgie, marchés de l'électricité et NovaSteel.  
**Temps de lecture :** ~14 minutes.  
**Persona :** Sofia Lindqvist — Energy Manager (`apps\analytics-mfe\src\personaRoutes.ts:49-58`; `docs\personas\personas-and-journeys.md:158-199`).  
**Écrans couverts :** `/{site}/energy-optimization/spot-price-schedule`, `/{site}/energy-optimization/load-shift-simulator`.  
**Dernière mise à jour :** 2026-07-27  
**Langue :** 🇬🇧 [English version](../en/05-energy-optimization.md)

---

## Les bases acier et électricité avant d'ouvrir l'écran

Fabriquer de l'acier demande énormément de chaleur. Dans le cas d'usage NovaSteel, le problème est formulé ainsi : « **Energy costs represent 35% of total production cost with no real-time optimization** » (`docs\usecase\usecase.md:14-22`). Les résultats attendus sont « **Energy consumption per ton reduced by 14%** » et « **CO₂ emissions reduced by 22%** » (`docs\usecase\usecase.md:37-42`).

Un prix **day-ahead** ou **spot** est le prix de l'électricité pour un court créneau, souvent exprimé en **€/MWh** : euros par mégawattheure. Un **mégawattheure (MWh)** est une quantité d'énergie ; utiliser 10 mégawatts pendant une heure consomme 10 MWh. L'écran affiche aussi l'**intensité carbone** du réseau, c'est-à-dire les émissions de CO₂-équivalent associées à chaque MWh (`apps\analytics-mfe\src\api\domain.ts:71-86`).

Les prix ont des **pics** et des **creux**. Un pic est une heure chère, comme la pointe de rareté du soir à 280 €/MWh dans les données de démonstration (`apps\analytics-mfe\src\api\fixtures.ts:37-43`; `docs\demo\demo-runbook.md:123-133`). Un creux est une heure moins chère. L'**effacement de charge (load shifting / demand response)** consiste à déplacer une demande électrique flexible hors des pics vers des heures moins coûteuses. Un **planning de dispatch (dispatch schedule)** indique quel lot ou procédé tourne dans quel créneau (`apps\analytics-mfe\src\api\domain.ts:88-132`).

Tous les procédés sidérurgiques ne peuvent pas bouger. Un **haut fourneau (blast furnace)** produit en continu : l'arrêter ou le retarder sans préparation est dangereux et irréaliste. Un **four de réchauffage (reheat furnace)** chauffe des brames ou bobines avant laminage ; certains lots peuvent être déplacés si les règles de livraison, maintien, trempe thermique et capacité restent respectées (`services\optimizer-worker\src\optimizer_worker\milp.py:1-8`; `services\optimizer-worker\src\optimizer_worker\service.py:163-190`). Un **four électrique à arc (electric-arc furnace)**, lorsqu'il existe, est aussi plus déplaçable qu'un haut fourneau car il fonctionne par campagnes, mais cet écran NovaSteel modélise aujourd'hui les lots de réchauffage (`services\bff-api\fixtures\demo-full\heat_batch.ndjson:2-8`; `services\optimizer-worker\src\optimizer_worker\service.py:372-400`).

### Ce que l'optimiseur résout vraiment

NovaSteel utilise un **programme linéaire en nombres mixtes (mixed-integer linear program, MILP)**. Dit simplement : le solveur choisit un créneau pour chaque lot éligible, respecte des règles non négociables, puis cherche la combinaison la moins chère et la moins carbonée (`services\optimizer-worker\src\optimizer_worker\milp.py:1-8`).

| Idée du solveur | Explication simple | Preuve |
|---|---|---|
| Fonction objectif | Le score à minimiser : coût de l'énergie plus impact carbone. | `services\optimizer-worker\src\optimizer_worker\milp.py:110-125`; `docs\presentation\proof_of_execution.md:182-204` |
| Variables de décision | Des choix oui/non : « le lot B démarre au créneau S ». | `services\optimizer-worker\src\optimizer_worker\milp.py:65-89` |
| Contrainte d'affectation | Chaque lot démarre exactement une fois. | `services\optimizer-worker\src\optimizer_worker\milp.py:90-95` |
| Contrainte de capacité | Pas plus que le nombre autorisé de lots en parallèle. | `services\optimizer-worker\src\optimizer_worker\milp.py:97-108` |
| Lot urgent figé | Un lot automobile urgent reste à son créneau prévu ; on ne le sacrifie pas pour une électricité moins chère. | `services\optimizer-worker\src\optimizer_worker\milp.py:71-75`; `services\bff-api\fixtures\demo-full\heat_batch.ndjson:4` |
| Limites de décalage et maintien | Les lots non urgents ne bougent que dans la fenêtre autorisée. | `services\optimizer-worker\src\optimizer_worker\service.py:68-74`; `services\optimizer-worker\src\optimizer_worker\milp.py:76-84` |
| Faisabilité | Une proposition n'est acceptable que si toutes les règles dures sont satisfaites. | `services\optimizer-worker\src\optimizer_worker\service.py:159-190` |

« Zero hard-constraint violations » est important parce qu'un planning moins cher mais impossible à produire n'a aucune valeur. Le simulateur affiche ce nombre et l'objectif est « must be 0 » (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:30-35`; `services\optimizer-worker\src\optimizer_worker\service.py:159-216`).

L'économie modélisée est la différence en euros entre le planning de base et le planning optimisé. Exemple simple : si une charge flexible sort de la fenêtre 17:00–20:00 à environ 280 €/MWh pour aller vers des heures moins chères, l'économie vaut approximativement MWh déplacés × écart de prix ; l'écran affiche le résultat confirmé via `rec.savings.costEur` (quelques milliers d'euros, par exemple ~3,3 k€ dans la capture BFF visible ou ~4,2 k€ dans un scénario équivalent) (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:30-35`; `services\optimizer-worker\src\optimizer_worker\service.py:87-104`; `services\optimizer-worker\src\optimizer_worker\service.py:217-235`).

Les recommandations sont **shadow/advisory**, c'est-à-dire consultatives. L'interface enregistre une approbation simulée ; elle n'écrit jamais un planning opérationnel ni une consigne d'usine (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:109-129`; `services\bff-api\src\bff_api\routes.py:305-354`; `contracts\openapi\bff-api-v1.yaml:146-185`).

---

## Spot & Schedule — `/{site}/energy-optimization/spot-price-schedule`

![Écran Spot price and scheduled load](../screenshots/energy-optimization-spot-price-schedule.png)

**En une phrase.** Cet écran compare la courbe de prix de l'électricité, la charge prévue et la charge optimisée, puis liste les lots de réchauffage déplaçables et le lot urgent figé (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:16-114`).

**Contexte sidérurgique (pour les débutants).** Un lot de réchauffage est une opération de chauffe avant laminage. Le problème métier est le coût énergétique, et le point d'infusion IA indique qu'« **an energy dispatch optimization agent schedules energy-intensive processes around electricity spot prices** » (`docs\usecase\usecase.md:46-50`).

**Ce que vous voyez à l'écran.**

1. **Shell global et bannière de sécurité.** La capture montre la barre supérieure NovaSteel, le site LU, la navigation gauche et la bannière violette « Synthetic demo data — not for operational control ». Cette transparence est obligatoire pour la démo (`docs\demo\demo-runbook.md:39-45`; `docs\ux\dashboard-specification.md:130-183`).
2. **Persona et actions de page.** L'en-tête montre « Sofia Lindqvist — Energy Manager », puis « Reset layout », « What's this? », « Copilot » et « Start guided demo ». Les noms viennent du registre des routes (`apps\analytics-mfe\src\personaRoutes.ts:49-58`).
3. **Onglets.** « Spot & Schedule » est sélectionné ; « Load-Shift Simulator » est le second onglet (`apps\analytics-mfe\src\personaRoutes.ts:54-58`).
4. **Carte KPI — prix de pointe (« Peak price today »).** La carte affiche **280 €/MWh**, « evening scarcity » et « peak ~18:30 ». Bon signe : la charge flexible évite cette heure chère. Mauvais signe : un gros bloc de charge reste sur le pic (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:34-49`; `apps\analytics-mfe\src\api\fixtures.ts:37-43`).
5. **Carte KPI — économies projetées (« Projected savings »).** La carte indique une économie modélisée et « simulated / shadow ». C'est une proposition, pas une facture mesurée (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:42-50`; `services\optimizer-worker\src\optimizer_worker\service.py:191-235`).
6. **Carte KPI — intensité CO₂ (« CO₂ intensity »).** La carte affiche par exemple **165 gCO₂/kWh** avec une cible. Plus bas est meilleur car chaque MWh déplacé porte moins de carbone (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:35-48`; `apps\analytics-mfe\src\api\domain.ts:71-86`).
7. **Carte KPI — charge déplaçable (« Shiftable load »).** La carte montre **18 MW** dans les contraintes. C'est la charge électrique flexible que l'optimiseur peut déplacer ; la charge de base reste fixe (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:48`).
8. **Graphique — prix spot et charge planifiée (« Spot price & scheduled load »).** La ligne orange est le prix sur l'axe droit ; la zone turquoise est la demande optimisée sur l'axe gauche ; la ligne bleue pointillée est la ligne de base. Dans la capture, le prix orange monte le soir et la charge optimisée baisse sur cette fenêtre (`apps\analytics-mfe\src\components\charts\PriceLoadChart.tsx:28-224`; `apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:65-91`).
9. **Lire le graphique à deux axes.** L'axe gauche est en **MW** ; l'axe droit est en **€** par MWh. Sur le même axe temps, prix haut + charge optimisée basse = bonne éviction du pic (`apps\analytics-mfe\src\components\charts\PriceLoadChart.tsx:98-177`).
10. **Tableau de planning (« Schedule »).** Le tableau affiche recherche globale, recherches par colonne, badges de preuve, puis **Process**, **Grade**, **Window**, **Tonnage**, **€/MWh**, **Shift (min)** et **Status**. Les lignes visibles combinent des lots « Shiftable » et un lot « Fixed (urgent) », signe que l'optimiseur respecte l'urgence de production (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:52-111`; `services\optimizer-worker\src\optimizer_worker\milp.py:71-75`).

**Pourquoi ce composant a été implémenté.** Le composant existe parce que le brief dit : « Energy costs represent 35% of total production cost with no real-time optimization » (`docs\usecase\usecase.md:14-22`). La spécification UX fait d'Energy Optimization l'espace de Sofia pour prix spot, plannings simulés et intensité CO₂ (`docs\ux\dashboard-specification.md:47-50`; `docs\ux\dashboard-specification.md:697-715`).

**Objectif et preuve (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Coût énergétique majeur | `CHL-01` | KPI prix de pointe, courbe prix/charge, tableau de planning | `GET /v1/energy/intervals`; `POST /v1/energy/schedules:simulate`; `apps\analytics-mfe\src\api\dataClient.ts:183-202`; `services\bff-api\src\bff_api\routes.py:226-279`; `apps\analytics-mfe\src\proof\proofCatalog.ts:223-244` |
| Réduire la consommation d'énergie | `OBJ-01` | Planning optimisé et preuve énergie par tonne | `services\optimizer-worker\src\optimizer_worker\metrics.py:32-39`; `apps\analytics-mfe\src\proof\proofCatalog.ts:337-357` |
| Agent IA de dispatch énergie | `AI-02` | Écran rattaché à `AI-02`; badges sur le planning | `services\optimizer-worker\src\optimizer_worker\milp.py:1-145`; `apps\analytics-mfe\src\proof\proofCatalog.ts:546-578` |

**Comment les données arrivent jusqu'à cet écran.** `EnergySpotSchedule.tsx` appelle `client.getEnergyIntervals()` et `client.simulateEnergy(...)` (`apps\analytics-mfe\src\components\screens\EnergySpotSchedule.tsx:16-20`). `DataClient` mappe ces appels vers `GET /v1/energy/intervals` et `POST /v1/energy/schedules:simulate`, avec repli sur fixtures déterministes (`apps\analytics-mfe\src\api\dataClient.ts:183-202`). La BFF transmet la simulation à `EnergyDispatchOptimizer.simulate()` (`services\bff-api\src\bff_api\routes.py:255-279`; `services\bff-api\src\bff_api\services.py:128-166`). L'optimiseur utilise PuLP/CBC si disponible, sinon un heuristique déterministe (`services\optimizer-worker\src\optimizer_worker\service.py:247-330`).

**Honnêteté et réserves.** Les données sont synthétiques, les prix de marché sont des fixtures et non un flux licencié, et l'écran montre des propositions, pas des économies facturées (`apps\analytics-mfe\src\api\fixtures.ts:21-29`; `apps\analytics-mfe\src\proof\proofCatalog.ts:223-244`). L'interface n'écrit jamais un planning ni une consigne (`contracts\openapi\bff-api-v1.yaml:146-185`; `docs\ux\dashboard-specification.md:711-715`). Les économies « whole-dispatch » incluent volontairement la charge fixe pour ne pas exagérer (`services\optimizer-worker\src\optimizer_worker\service.py:87-94`).

**À vous d'essayer.** Ouvrez `http://localhost:5266/lu/energy-optimization/spot-price-schedule`, repérez le pic à 280 €/MWh, puis vérifiez que le statut « Fixed (urgent) » reste figé dans le tableau (`apps\analytics-mfe\src\personaRoutes.ts:49-58`; `apps\analytics-mfe\src\components\screens\screenRegistry.ts:39-40`).

---

## Load-Shift Simulator — `/{site}/energy-optimization/load-shift-simulator`

![Écran Load-shift simulator](../screenshots/energy-optimization-load-shift-simulator.png)

**En une phrase.** Cet écran permet à Sofia de modifier des garde-fous de planification, de lancer un dispatch simulé et de comparer coût et pic de charge avant/après (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:14-136`).

**Contexte sidérurgique (pour les débutants).** Un simulateur est une zone « et si ? » sûre. L'usine peut tester « et si je permets 180 minutes de décalage et deux lots maximum en parallèle ? » sans modifier un planning réel (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:17-21`; `apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:109-129`).

**Ce que vous voyez à l'écran.**

1. **Carte KPI — estimation en direct (« Estimated saving (live) »).** La capture affiche **11.5%** et « client estimate ». La valeur change immédiatement avec les curseurs ; ce n'est pas le résultat final de l'optimiseur (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:23-32`).
2. **Carte KPI — économie confirmée (« Confirmed saving »).** La capture montre une économie confirmée par la BFF, par exemple **9%**, avec une valeur en euros. Elle remplace l'estimation après « Simulate schedule » (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:30-35`; `apps\analytics-mfe\src\api\dataClient.ts:190-203`).
3. **Carte KPI — réduction de pic (« Peak reduction »).** La capture montre environ **−7.9%**. Bon signe : le pic MW du soir baisse ; mauvais signe : l'optimisation créerait un nouveau pic ailleurs (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:33`; `services\optimizer-worker\src\optimizer_worker\service.py:106-135`).
4. **Carte KPI — violations dures (« Hard violations »).** La capture affiche **0** et « must be 0 ». Toute valeur non nulle rend la proposition infaisable (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:34`; `services\optimizer-worker\src\optimizer_worker\service.py:159-216`).
5. **Graphique — comparaison (« Baseline vs optimized »).** Le graphique en barres groupées contient **Cost (k€)** et **Peak (MW)**. Chaque groupe compare la ligne de base à l'optimisé. Des barres optimisées plus basses sont bonnes si le tonnage et les contraintes restent inchangés (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:43-72`; `apps\analytics-mfe\src\components\charts\BarChart.tsx:28-145`).
6. **Lire un graphique en barres groupées.** Une barre compare des catégories, pas une évolution temporelle. Ici, baseline = « si l'on ne change rien » ; optimized = « sous le scénario soumis » (`apps\analytics-mfe\src\components\charts\BarChart.tsx:88-137`).
7. **Contrôles de scénario (« Scenario controls »).** Le panneau latéral affiche **Max shift window: 180 min** et **Max concurrent batches: 2**. Ce sont des garde-fous, pas des commandes machine (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:77-108`).
8. **Bouton « Simulate schedule ».** Il envoie les valeurs des curseurs à la BFF ; il ne valide pas un planning usine (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:109-114`; `apps\analytics-mfe\src\api\dataClient.ts:190-203`).
9. **Bouton « Record simulated approval ».** Le code affiche un message : « Simulated/shadow approval recorded — no operational schedule was written » (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:115-129`). La route d'approbation enregistre un audit `SIMULATED_APPROVED` (`services\bff-api\src\bff_api\routes.py:305-354`).
10. **Note sous les boutons.** L'écran précise qu'aucune action UI n'écrit un planning opérationnel et que l'approbation est simulée/shadow en Phase 0/1 (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:127-129`).

**Pourquoi ce composant a été implémenté.** Le simulateur réalise le point d'infusion « an energy dispatch optimization agent schedules energy-intensive processes around electricity spot prices » (`docs\usecase\usecase.md:46-50`). Il implémente aussi l'UX demandant curseurs de scénario, barres avant/après, « Simulate schedule » et approbation simulée (`docs\ux\dashboard-specification.md:711-715`).

**Objectif et preuve (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Optimisation énergétique contrainte | `CHL-01` | Scénario à curseurs, économie confirmée, zéro violation dure | `POST /v1/energy/schedules:simulate`; `services\optimizer-worker\src\optimizer_worker\service.py:52-235`; `apps\analytics-mfe\src\proof\proofCatalog.ts:223-244` |
| Réduire la consommation d'énergie | `OBJ-01` | Comparaison baseline/optimized et conservation du tonnage | `services\optimizer-worker\src\optimizer_worker\service.py:96-104`; `services\optimizer-worker\src\optimizer_worker\metrics.py:32-39`; `apps\analytics-mfe\src\proof\proofCatalog.ts:337-357` |
| Agent IA de dispatch | `AI-02` | MILP/CBC ou repli déterministe, proposition consultative | `services\optimizer-worker\src\optimizer_worker\milp.py:65-145`; `services\optimizer-worker\src\optimizer_worker\service.py:247-330`; `apps\analytics-mfe\src\proof\proofCatalog.ts:546-578` |
| Cibles énergie et CO₂ | `OUT-01`, `OUT-02` | Économies modélisées contribuant aux cibles, non mesurées | `docs\presentation\proof_of_execution.md:307-338`; `apps\analytics-mfe\src\proof\proofCatalog.ts:415-462` |

**Comment les données arrivent jusqu'à cet écran.** `EnergySimulator.tsx` conserve l'état des curseurs, calcule une estimation locale instantanée et appelle `client.simulateEnergy(committed)` pour le résultat confirmé (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:14-35`). `DataClient.simulateEnergy()` poste `site`, `horizonHours`, `scenario` et contraintes vers `POST /v1/energy/schedules:simulate` (`apps\analytics-mfe\src\api\dataClient.ts:94-100`; `apps\analytics-mfe\src\api\dataClient.ts:190-203`). La BFF ajoute une ligne d'audit pour la simulation (`services\bff-api\src\bff_api\services.py:128-166`).

**Honnêteté et réserves.** Le scénario est synthétique et déterministe ; le décalage 17:00–20:00 hors d'un pic à 280 €/MWh est modélisé, pas validé par une facture (`apps\analytics-mfe\src\api\fixtures.ts:37-43`; `docs\demo\demo-runbook.md:123-133`). Les économies affichées varient selon que la BFF locale ou le repli fixture sert l'écran, mais les deux sont étiquetés synthetic/shadow (`apps\analytics-mfe\src\api\dataClient.ts:127-149`). Aucun setpoint, ordre PLC, recette four ou planning opérationnel n'est écrit (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:127-129`; `contracts\openapi\bff-api-v1.yaml:146-185`).

**À vous d'essayer.** Ouvrez `http://localhost:5266/lu/energy-optimization/load-shift-simulator`, déplacez « Max shift window », observez l'estimation en direct, cliquez « Simulate schedule » et vérifiez que « Hard violations » reste à 0 (`apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:17-35`; `apps\analytics-mfe\src\components\screens\EnergySimulator.tsx:77-129`).

---

◀ [04 · Santé des fours](04-furnace-health.md) · ▲ [Index](LISEZMOI.md) · [06 · Qualité](06-quality.md) ▶


