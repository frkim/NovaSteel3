# NovaSteel — Fiche de répétition du présentateur

> **Format :** une page, recto, à imprimer et garder sous la main pendant la soutenance.
> **Date :** 2026-07-26
> **Companion :** [`oral-defense-and-slide-plan.md`](oral-defense-and-slide-plan.md) · [`../demo/demo-runbook.md`](../demo/demo-runbook.md)

---

## Minutage strict (60 minutes)

| Segment | Durée | Horloge | Contenu |
|---|---|---|---|
| **Slides** | 35 min | 00:00 → 35:00 | 20 slides (+ 1 CFO bridge si inséré) |
| **Démo live** | 10 min | 35:00 → 45:00 | 7 onglets, données synthétiques, graine `240725` |
| **Q&A jury** | 15 min | 45:00 → 60:00 | ≥ 8–10 questions ; [faq.md](faq.md) |

## Checkpoints (si en retard de > 30 s, couper en profondeur, pas en honnêteté)

| CP | Horloge cible | Doit être vrai |
|---|---|---|
| CP-1 | **10:00** | Business case + cibles + gardes-fous + personas atterris |
| CP-2 | **18:00** | Architecture + Fabric-centralité + ingestion + « Python décide » atterris |
| CP-3 | **25:30** | 4 deep-dives IA terminés avec étiquettes 🎯 vs 🔬 intactes |
| CP-4 | **34:15** | RAI + sécurité + synthétique + coût/échelle défendus |
| CP-5 | **35:00** | Timer démo lancé, onglet Plant Manager ouvert, checklist verte |
| CP-6 | **45:00** | Phrase récap prononcée ; ne pas déboguer en live |
| CP-7 | **60:00** | ≥ 8 questions répondues ; inconnues logguées en suivi écrit |

## Transitions clés (phrases à mémoriser)

| Moment | Phrase de transition |
|---|---|
| Slide 1 → récit | « Dans les 60 prochaines minutes… un seul contrat : je vous dirai toujours si un chiffre est une *cible* ou une *preuve*. » |
| Avant démo (Slide 20) | « Tout est synthétique et déterministe. Si quelque chose hésite, je bascule sur le résultat en cache — c'est un choix répété, pas une panne. » |
| Retour de démo (45:00) | « Les quatre chiffres restent des cibles ; ce que vous avez vu est la preuve reproductible que les mécanismes fonctionnent. Vos questions les plus difficiles. » |
| CFO bridge | « Construction < 1,1M€, énergie ~24,5M€/an à l'échelle — retour < 12 mois même avec des décotes conservatrices. » |

## Échelle de repli (5 niveaux — ne jamais déboguer > 10 s à l'écran)

1. **Cloud en direct** (nominal)
2. **Rejeu local déterministe** — même séquence d'événements
3. **Cache interactif** — résultats signés de la graine exacte
4. **Enregistrement vidéo** — 90 s, flux complet
5. **Pack de preuve statique** — captures + JSON + transcription

**Signal de main** convenu avec l'opérateur de reset pour passer au niveau suivant.

## Chiffres que le présentateur doit connaître par cœur

| Chiffre | Catégorie | Source |
|---|---|---|
| **−14 %** énergie/tonne | 🎯 TARGET | usecase.md ; solution-requirements.md §4 |
| **−22 %** CO₂/tonne | 🎯 TARGET | usecase.md ; solution-requirements.md §4 |
| **≥ 21 jours** alerte four | 🎯 TARGET (🔬 evidence : ~20 j) | solution-requirements.md §4 |
| **+8 %** rendement haut de gamme | 🎯 TARGET | solution-requirements.md §4 |
| **35 %** = part énergie dans le coût | Fait métier | usecase.md |
| **€8M** coût d'une défaillance four | Fait métier | personas-and-journeys.md |
| **7,25 %** réduction coût énergie (dispatch total) | 🔬 EVIDENCE (scénario synthétique 24 h) | optimizer MILP output |
| **3,29 %** réduction CO₂ (dispatch total) | 🔬 EVIDENCE (scénario synthétique 24 h) | optimizer MILP output |
| **7,89 %** réduction pic (dispatch-attribuable) | 🔬 EVIDENCE (scénario synthétique 24 h) | optimizer MILP output |
| P50 **~20 j** / P10 **18,7** / P90 **20,6** | 🔬 EVIDENCE (scénario synthétique) | demo-runbook.md §5 ; RUL regression |
| **~€24,5M/an** bénéfice énergie à l'échelle | 🎯 TARGET illustratif (dérivé de 14 % × A1 × A3) | operations-and-cost.md §8.5 |
| **< 12 mois** retour sur investissement | 🎯 TARGET illustratif | operations-and-cost.md §8.5 |
| Risque RUL **0,90** / confiance **0,78** | 🔬 EVIDENCE | RUL regression (r² = 0.88) |
| **F2** = SKU Fabric du démo | 🔬 EVIDENCE | deployment-topology.md §5 |
| Graine **240725** | Démo | demo-runbook.md §3 |
| Commande de travail **WO-DEMO-LUX-1042** | Démo | demo-runbook.md §5 |

## Réponses aux pièges fréquents (une ligne)

| Question piège | Réponse d'une ligne |
|---|---|
| « C'est quoi le coût en production ? » | « Un dimensionnement après mesure pilote, pas un fait d'architecture — j'ai les drivers et les contrôles, pas un €/h inventé. » |
| « Le 14 % est prouvé ? » | « 7,25 % sur un scénario de 24 h à un site ; 14 % est la cible annuelle multi-conditions — le pilote la prouve. » |
| « Pourquoi pas Databricks ? » | « Aucun ne donne un seul estate gouverné couvrant RTI sub-seconde + OneLake + Direct Lake + Power BI natif sans copie ni couture. » |
| « L'IA est-elle à haut risque (AI Act) ? » | « Posture conservatrice high-risk-adjacent en attente de classification juridique ; comité RAI obligatoire avant production. » |
| « Et si le réseau tombe ? » | « Cinq niveaux de repli — la démo se termine toujours, même hors ligne. » |

---

*Imprimer recto seul. Garder sur le pupitre, hors champ caméra.*
