# 06 · Qualité — Batch Quality et Defect Analytics (SPC)

**Public visé :** une personne totalement débutante en qualité acier, essais laboratoire et pilotage statistique.  
**Temps de lecture :** ~15 minutes.  
**Persona :** Jens Bakker — Quality Engineer (`apps\analytics-mfe\src\personaRoutes.ts:61-70`; `docs\personas\personas-and-journeys.md:42-50`).  
**Écrans couverts :** `/{site}/quality/batches`, `/{site}/quality/spc`.  
**Dernière mise à jour :** 2026-07-27  
**Langue :** 🇬🇧 [English version](../en/06-quality.md)

---

## Les bases qualité avant d'ouvrir l'écran

Un **lot (batch)** est une unité de production traçable. En acier plat, il peut finir sous forme de bobine. Une **coulée (heat)** est un lot d'acier liquide produit avec une composition chimique donnée avant coulée et laminage. La **généalogie de lot (batch genealogy)** est l'arbre familial du produit : lots de matières premières, coulée, traitement en poche, brame, réchauffage, bobine, échantillon, résultat d'essai et expédition (`apps\analytics-mfe\src\api\domain.ts:155-171`; `services\bff-api\src\bff_api\repository.py:198-226`).

L'**acier haut de gamme pour l'automobile** doit respecter des exigences strictes de résistance, planéité, surface et répétabilité. Les clients automobiles refusent les bobines si les propriétés mécaniques ou l'état de surface sortent de la spécification. Le cas d'usage indique « **Quality consistency issues in high-grade steel for automotive customers** » (`docs\usecase\usecase.md:14-22`). Le résultat attendu est « **High-grade steel yield improved by 8%** » (`docs\usecase\usecase.md:37-42`).

Le **rendement (yield)** est la part de matière produite qui est vendable au grade prévu. Le **rendement du premier coup (first-pass yield)** signifie que le lot passe l'inspection sans retouche. Le **scrap** est de la matière non vendable comme prévu. La **retouche (rework)** est un traitement supplémentaire pour corriger ou déclasser la matière. Les deux coûtent du temps et de l'argent (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:31-36`).

NovaSteel distingue clairement qualité **prédite** et qualité **mesurée**. Un score prédit est une estimation modèle, par exemple un risque de premier passage calculé depuis le biais de température de bobinage (`services\scoring-worker\src\scoring_worker\service.py:73-97`). Un résultat laboratoire mesuré est une valeur d'essai, par exemple une résistance en MPa avec statut PASS/FAIL (`apps\analytics-mfe\src\api\domain.ts:134-153`). Le tiroir permet de basculer entre **Predicted** et **Measured** et rappelle qu'aucune recette ni consigne n'est écrite (`apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:117-180`).

La **maîtrise statistique des procédés (Statistical Process Control, SPC)** sert à voir si un procédé est stable ou dérive. Une **carte de contrôle (control chart)** trace les échantillons avec une **ligne centrale (centre line)**, une **limite supérieure de contrôle (UCL)** et une **limite inférieure de contrôle (LCL)**. Un point hors UCL/LCL est **hors contrôle** et demande investigation (`apps\analytics-mfe\src\components\charts\ControlChart.tsx:120-184`; `apps\analytics-mfe\src\components\screens\QualitySpc.tsx:52-77`). **Cp/Cpk** sont des indices de capabilité : plus ils sont élevés, mieux le procédé tient dans les limites de spécification ; la cible affichée est Cpk ≥ 1,33 (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:38-43`). Un **diagramme de Pareto (Pareto chart)** classe les causes de défaut de la plus fréquente à la moins fréquente et ajoute une courbe de pourcentage cumulé pour cibler les causes qui créent la majorité des défauts (`apps\analytics-mfe\src\components\charts\ParetoChart.tsx:23-168`).

---

## Batch Quality — `/{site}/quality/batches`

![Écran Batch quality](../screenshots/quality-batches.png)

**En une phrase.** Cet écran présente les KPI qualité, une tendance de rendement prédit et un tableau de lots cliquable ouvrant la généalogie et un what-if borné (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:19-92`; `apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:42-185`).

**Contexte sidérurgique (pour les débutants).** Une bobine peut passer ou échouer parce que sa résistance, sa chimie, sa surface ou son historique thermique ne respecte pas la promesse du grade. La démo NovaSteel se concentre sur une bobine automobile DP780 en dérive (`docs\demo\demo-runbook.md:84-88`; `apps\analytics-mfe\src\api\fixtures.ts:359-407`).

**Ce que vous voyez à l'écran.**

1. **Shell global et bannière.** La capture montre le site LU, la navigation gauche et la bannière violette de données synthétiques. Elle rappelle que les données qualité ne sont pas de production (`docs\demo\demo-runbook.md:39-45`; `apps\analytics-mfe\src\api\fixtures.ts:21-29`).
2. **Persona et onglets.** L'en-tête montre « Jens Bakker — Quality Engineer ». « Batch Quality » est sélectionné ; « Defect Analytics (SPC) » est l'autre onglet (`apps\analytics-mfe\src\personaRoutes.ts:61-70`).
3. **Carte KPI — rendement haut de gamme (« High-grade yield »).** La capture affiche **94.8%**, **+1.2 pts** et cible **95%**. Plus haut est meilleur ; une baisse signifie davantage d'acier hors grade premium (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:31-36`).
4. **Carte KPI — premier passage (« First-pass yield »).** La carte affiche **97.1%** et cible **97%**. Plus haut est meilleur car il y a moins de retouches (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:31-36`).
5. **Carte KPI — NCR ouverts (« Open NCRs »).** La carte montre **3**. NCR signifie **Non-Conformance Record**, un dossier formel de non-conformité à traiter avant libération (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:30-35`).
6. **Carte KPI — taux de défauts (« Defect rate »).** La carte affiche **182 ppm** avec cible **170**. **ppm** signifie parties par million ; plus bas est meilleur (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:35`).
7. **Graphique — tendance de rendement (« Yield trend »).** La ligne reste proche des hauts 90, chute nettement vers le lot #7, puis dérive vers le bas. Bon signe : une ligne stable près de la cible. Mauvais signe : l'excursion descendante visible (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:25-29`; `apps\analytics-mfe\src\components\charts\LineChart.tsx:45-180`).
8. **Lire la courbe.** Un graphique en ligne montre l'évolution d'échantillons ordonnés. Ici, gauche-droite = ordre des lots ; plus bas = rendement premier passage prédit qui se dégrade (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:52-68`).
9. **Tableau « Batches ».** Il comporte recherche globale, recherches par colonne, badges de preuve et colonnes **Batch**, **Grade**, **Heat**, **Value**, **Coiling bias °C**, **Risk**, **Result**, **Updated**. Les lignes visibles montrent des bobines DP780 autour de 810–818 MPa, risque 57–61%, et pastilles PASS/FAIL (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:38-88`).
10. **Étiquettes PASS et FAIL.** La pastille de résultat est un statut laboratoire, pas une prédiction. Le pourcentage de risque est dérivé du modèle ; la valeur en MPa est une mesure qualité (`apps\analytics-mfe\src\api\domain.ts:134-153`; `services\scoring-worker\src\scoring_worker\service.py:73-97`).
11. **Tiroir de lot au clic.** Le tiroir affiche l'identifiant du lot, le grade, le statut et le biais de température de bobinage. Il liste ensuite la généalogie : matières premières, coulée, traitement poche, brame, réchauffage, bobine, échantillon, expédition (`apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:31-40`; `apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:79-113`).
12. **What-if borné.** Le tiroir propose les curseurs **Coiling temperature Δ** et **Force balance Δ**, puis le basculeur Predicted/Measured. Le mode Predicted affiche rendement actuel → proposé et bande P10–P90 ; le mode Measured affiche le résultat labo et répète qu'aucune consigne ni recette n'est écrite (`apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:117-180`; `services\scoring-worker\src\scoring_worker\service.py:99-145`).

**Pourquoi ce composant a été implémenté.** Il répond directement au défi « Quality consistency issues in high-grade steel for automotive customers » (`docs\usecase\usecase.md:14-22`) et à l'objectif « Improves steel quality » (`docs\usecase\usecase.md:26-33`). La spécification UX définit Batch Quality comme la surface des KPI de rendement, du tableau de lots et du tiroir de détail (`docs\ux\dashboard-specification.md:717-734`).

**Objectif et preuve (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Qualité automobile haut de gamme | `CHL-04` | KPI lots, tendance rendement, tableau PASS/FAIL, tiroir what-if | `GET /v1/quality/batches`; `GET /v1/quality/batches/{batchId}/genealogy`; `POST /v1/quality/what-if`; `services\bff-api\src\bff_api\routes.py:412-492`; `apps\analytics-mfe\src\proof\proofCatalog.ts:292-310` |
| Améliorer la qualité acier | `OBJ-03` | Tendance issue du risque et what-if borné | `services\scoring-worker\src\scoring_worker\service.py:73-145`; `apps\analytics-mfe\src\proof\proofCatalog.ts:373-393` |
| Cible rendement haut de gamme | `OUT-04` | KPI High-grade yield et mapping preuve | `apps\analytics-mfe\src\components\screens\QualityBatches.tsx:31-36`; `apps\analytics-mfe\src\proof\proofCatalog.ts:495-518`; `docs\presentation\proof_of_execution.md:352-357` |

**Comment les données arrivent jusqu'à cet écran.** `QualityBatches.tsx` appelle `client.getQualityBatches()` (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:19-23`). `DataClient.getQualityBatches()` appelle `GET /v1/quality/batches`; `getGenealogy()` appelle `GET /v1/quality/batches/{batchId}/genealogy`; `qualityWhatIf()` appelle `POST /v1/quality/what-if` (`apps\analytics-mfe\src\api\dataClient.ts:205-235`). La BFF lit les lignes qualité et la généalogie dans le repository puis envoie le what-if au scoring worker (`services\bff-api\src\bff_api\routes.py:412-492`; `services\bff-api\src\bff_api\repository.py:161-226`; `services\scoring-worker\src\scoring_worker\service.py:99-145`).

**Honnêteté et réserves.** Les données sont synthétiques et déterministes (`apps\analytics-mfe\src\api\fixtures.ts:21-29`). Le modèle de rendement est un substitut calibré sur le biais de température de bobinage, pas un modèle métallurgique entraîné en production (`apps\analytics-mfe\src\proof\proofCatalog.ts:292-310`). Le +8% est une cible/surrogate de démo, pas un résultat client mesuré (`docs\presentation\proof_of_execution.md:352-357`). Le what-if est consultatif et n'écrit aucune recette ni consigne (`services\scoring-worker\src\scoring_worker\service.py:140-144`; `contracts\openapi\bff-api-v1.yaml:243-255`).

**À vous d'essayer.** Ouvrez `http://localhost:5266/lu/quality/batches`, cliquez une ligne DP780 comme `COIL-LUX-260725-017`, inspectez la généalogie, déplacez le curseur de température, puis basculez de Predicted à Measured (`apps\analytics-mfe\src\components\screens\QualityBatches.tsx:76-89`; `apps\analytics-mfe\src\components\screens\QualityBatchDrawer.tsx:117-180`).

---

## Defect Analytics (SPC) — `/{site}/quality/spc`

![Écran Defect analytics SPC](../screenshots/quality-spc.png)

**En une phrase.** Cet écran montre si le procédé est statistiquement stable et quelles causes de défaut traiter en priorité (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:20-101`).

**Contexte sidérurgique (pour les débutants).** Même si des bobines passent individuellement, le procédé peut dériver. La SPC détecte cette dérive en vérifiant si les échantillons restent dans la variation normale ou franchissent une limite de contrôle (`apps\analytics-mfe\src\components\charts\ControlChart.tsx:120-184`).

**Ce que vous voyez à l'écran.**

1. **Carte KPI — points hors contrôle (« Out-of-control points »).** La capture affiche **1** avec cible « I-MR, 3σ limits ». Bon = zéro ; un point signifie qu'un échantillon a franchi une limite statistique (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:26-43`).
2. **Carte KPI — capabilité (« Process Cpk »).** La capture affiche **1.18** avec cible **≥ 1.33**. Plus haut est meilleur ; sous la cible, le procédé n'est pas assez capable pour la constance attendue (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:38-43`).
3. **Carte KPI — part du défaut principal (« Top defect share »).** La capture affiche **39.5%** et « Pareto 80/20 ». Le premier type de défaut représente donc une grosse part du total (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:28-42`; `apps\analytics-mfe\src\api\fixtures.ts:423-431`).
4. **Carte KPI — défauts 30 jours (« Defects (30d) »).** La capture affiche **86** défauts synthétiques sur 30 jours (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:42`; `apps\analytics-mfe\src\api\fixtures.ts:423-431`).
5. **Carte de contrôle.** Le panneau principal s'appelle **SPC control chart (coiling temperature bias)**. La ligne bleue trace 20 échantillons. La ligne centrale pointillée est **x̄ 1.9**. L'UCL rouge vaut environ **8.5** et la LCL environ **−4.7**. Le dernier point à **11.4** est rouge et hors contrôle (`apps\analytics-mfe\src\api\fixtures.ts:410-420`; `apps\analytics-mfe\src\components\charts\ControlChart.tsx:120-184`).
6. **Lire UCL, LCL et centre line.** La ligne centrale est la moyenne normale. UCL/LCL ne sont pas des limites client ; ce sont des rails statistiques, souvent à trois écarts types. Un point au-delà signifie « enquêter sur le procédé », pas « rebuter automatiquement toutes les bobines » (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:57-77`; `apps\analytics-mfe\src\components\charts\ControlChart.tsx:139-184`).
7. **Pareto des défauts (« Defect Pareto »).** Les barres orange montrent les comptes par type de défaut, triés décroissants, et la ligne rouge montre le cumul. Dans la capture, « Coiling temperature drift » domine avec 34 occurrences, puis « Edge crack » avec 21 (`apps\analytics-mfe\src\api\fixtures.ts:423-431`; `apps\analytics-mfe\src\components\charts\ParetoChart.tsx:23-168`).
8. **Lire le Pareto 80/20.** Commencez par la plus grande barre. Si les premières barres expliquent l'essentiel de la ligne cumulée, corrigez-les d'abord. Bon signe : la barre principale diminue avec le temps ; mauvais signe : une cause reste dominante (`apps\analytics-mfe\src\components\charts\ParetoChart.tsx:81-160`; `docs\ux\dashboard-specification.md:986-993`).
9. **Tableau « Defects ».** Le tableau sous le Pareto a des recherches et colonnes **Defect**, **Cause**, **Count**. Les lignes visibles incluent **Coiling temperature drift / Process / 34**, **Edge crack / Material / 21**, **Surface scale / Reheat / 14** et **Thickness variance / Mill / 9** (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:45-98`; `apps\analytics-mfe\src\api\fixtures.ts:423-431`).

**Pourquoi ce composant a été implémenté.** L'écran existe parce que le brief mentionne les problèmes de constance qualité en acier automobile haut de gamme (`docs\usecase\usecase.md:14-22`). La spécification UX demande des cartes SPC, limites UCL/LCL, marqueurs de violation, classement Pareto et tableau de défauts (`docs\ux\dashboard-specification.md:717-734`; `docs\ux\dashboard-specification.md:986-993`).

**Objectif et preuve (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Défi de constance qualité | `CHL-04` | KPI hors contrôle, carte SPC, vue Pareto causes racines | Écran SPC actuel sur fixtures frontend : `apps\analytics-mfe\src\components\screens\QualitySpc.tsx:1-101`; `apps\analytics-mfe\src\api\fixtures.ts:410-431`; preuve `apps\analytics-mfe\src\proof\proofCatalog.ts:292-310` |
| Améliorer la qualité acier | `OBJ-03` | Cpk, limites de contrôle, analyse défauts | `apps\analytics-mfe\src\proof\proofCatalog.ts:373-393`; exploration corrective : `POST /v1/quality/what-if`, `services\scoring-worker\src\scoring_worker\service.py:99-145` |
| Cible rendement haut de gamme | `OUT-04` | La SPC soutient la cible affichée dans Batch Quality | `docs\presentation\proof_of_execution.md:352-357`; `apps\analytics-mfe\src\proof\proofCatalog.ts:495-518` |

**Comment les données arrivent jusqu'à cet écran.** Dans l'implémentation actuelle, `QualitySpc.tsx` importe directement `spcSeries()` et `defectPareto()` depuis les fixtures frontend (`apps\analytics-mfe\src\components\screens\QualitySpc.tsx:1-24`; `apps\analytics-mfe\src\api\fixtures.ts:410-431`). Le workflow qualité plus large passe par `GET /v1/quality/batches`, `GET /v1/quality/batches/{batchId}/genealogy` et `POST /v1/quality/what-if` (`docs\implementation\api-contracts.md:209-216`; `contracts\openapi\bff-api-v1.yaml:209-255`).

**Honnêteté et réserves.** Les valeurs SPC sont des fixtures synthétiques, pas un flux laboratoire réel (`apps\analytics-mfe\src\api\fixtures.ts:410-431`). Le Cpk et les défauts servent à expliquer le workflow ; ils ne prouvent pas une capabilité industrielle réelle. Un franchissement de limite déclenche une recherche de cause, pas un rejet automatique. Aucun setpoint correctif n'est écrit depuis l'écran SPC (`docs\ux\dashboard-specification.md:1190-1195`).

**À vous d'essayer.** Ouvrez `http://localhost:5266/lu/quality/spc`, repérez le dernier point rouge au-dessus de l'UCL, puis utilisez le Pareto pour identifier la cause principale avant de revenir à Batch Quality pour un what-if borné (`apps\analytics-mfe\src\components\screens\screenRegistry.ts:41-42`; `apps\analytics-mfe\src\components\screens\QualitySpc.tsx:52-98`).

---

◀ [05 · Optimisation de l'énergie](05-energy-optimization.md) · ▲ [Index](LISEZMOI.md) · [07 · Durabilité et conformité](07-sustainability-and-compliance.md) ▶

