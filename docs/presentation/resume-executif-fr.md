# NovaSteel — Résumé exécutif

> **Statut :** Document de soutenance orale — résumé d'une page
> **Date :** 2026-07-26
> **Langue :** Français (européen professionnel)
> **Convention :** 🎯 TARGET = objectif projeté (non démontré) · 🔬 EVIDENCE = résultat reproductible sur données synthétiques
> **Companion :** [`oral-defense-and-slide-plan.md`](oral-defense-and-slide-plan.md) · [`faq.md`](faq.md) · [`../demo/demo-runbook.md`](../demo/demo-runbook.md)

---

## Le défi industriel

AxelorMetal est un sidérurgiste intégré européen (siège au Luxembourg) exploitant des **hauts fourneaux** et des **laminoirs** sur quatre sites de l'UE. Quatre problèmes structurels menacent la compétitivité :

1. **Énergie = 35 % du coût de production** sans levier d'optimisation en temps réel.
2. **Émissions de CO₂** sous pression réglementaire croissante (EU ETS — marché des quotas).
3. **Défaillances du revêtement réfractaire** : ~€8M par événement, actuellement imprévisibles.
4. **Perte du savoir-faire** : les opérateurs experts partent à la retraite plus vite qu'on ne peut capitaliser leur expertise.

---

## La solution : une plateforme d'aide à la décision gouvernée

AxelorMetal déploie **NovaSteel**, une plateforme unique d'optimisation de la production sidérurgique centrée sur **Microsoft Fabric** (jumeau numérique des données) et **Microsoft Foundry** (IA générative) :

| Capacité IA | Fonction | Modèle |
|---|---|---|
| Pilotage énergétique | Décaler les charges flexibles hors des pics de prix/carbone | Optimiseur MILP (PuLP) — Python |
| Durée de vie résiduelle (RUL) du garnissage | Prédire la défaillance réfractaire ≥ 21 jours à l'avance | Régression physique (flux thermique) — Python |
| Risque qualité | Détecter les dérives avant résultat laboratoire | Modèle prédictif — Python |
| Capture du savoir | Interviewer, transcrire (Azure Speech), structurer (Foundry) | Agent GenAI avec approbation humaine |

**Principe fondamental :** la plateforme *conseille* ; l'humain *décide*. Aucun composant n'écrit dans un automate, une interlock ou un point de consigne. C'est de l'**aide à la décision**, jamais du contrôle.

---

## Les quatre objectifs chiffrés (🎯 TARGET)

| ID | Objectif | Cible | Mesure |
|---|---|---|---|
| O1 | Réduction de l'énergie par tonne | 🎯 **−14 %** | kWh/t, €/t vs. référence |
| O2 | Réduction du CO₂ par tonne | 🎯 **−22 %** | tCO₂/t vs. référence |
| O3 | Alerte anticipée de défaillance four | 🎯 **≥ 21 jours** | Horizon P50 du modèle RUL |
| O4 | Amélioration du rendement haut de gamme | 🎯 **+8 %** | % de coulées conformes automobile |

> Ces chiffres sont des **cibles de transformation**, pas des résultats démontrés. La démonstration
> prouve que les *mécanismes* fonctionnent de bout en bout sur données synthétiques (🔬 EVIDENCE).
>
> **Résultats validés sur un scénario synthétique de 24 h (un site, graine `240725`) :**
> 🔬 Coût énergie **−7,25 %** · CO₂ **−3,29 %** · Pic **−7,89 %** (dispatch total) ·
> RUL P50 **~20 j** (P10 18,7 / P90 20,6 / risque 0,90 / confiance 0,78).
> L'écart entre les cibles et les preuves s'explique par la portée : un scénario vs. un
> pilote annuel multi-conditions — voir [`operations-and-cost.md`](../operations/operations-and-cost.md) §8.5.6.

---

## Architecture et gouvernance

- **Cœur de données :** Microsoft Fabric — Real-Time Intelligence (Eventstream + Eventhouse/KQL) pour le flux chaud ; OneLake / Lakehouse (bronze→argent→or) pour l'historique gouverné ; Direct Lake pour un modèle sémantique unique.
- **IA déterministe :** Python (FastAPI) pour les calculs ; Foundry pour l'explication et la recherche documentaire (ADR-006 : « Python décide, Foundry explique »).
- **Identités managées :** zéro secret stocké ; Entra ID partout ; quatre plans d'autorisation séparés.
- **Résidence UE :** traitement en **Sweden Central** ; Foundry Data Zone (EU) ; aucune donnée hors UE.
- **Posture EU AI Act :** classification prudente « high-risk-adjacent » en attente de confirmation juridique ; comité RAI interdisciplinaire avant mise en production.
- **Sécurité de la chaîne logicielle :** feeds protégés Microsoft uniquement (`packagefeedproxy.microsoft.io`) ; SBOM ; déploiement par GitHub OIDC.

---

## Rentabilité illustrative (🎯 TARGET)

| | Fourchette illustrative |
|---|---|
| **Construction** | €0,6–1,1M (unique) |
| **Exploitation** | €0,3–0,7M/an |
| **Bénéfice énergie (O1)** | ~€24,5M/an à l'échelle *(14 % × 35 % × 1 Mt)* |
| **Défaillances évitées (O3)** | ~€3,2M/an *(€8M × 1 / 2,5 ans)* |
| **Retour sur investissement** | **< 12 mois** (conservateur) ; < 9 mois (base) |

> Hypothèses et table de sensibilité détaillées dans [`../operations/operations-and-cost.md`](../operations/operations-and-cost.md) §8.5.
> Tous les chiffres sont 🎯 TARGET / illustratifs — à confirmer avec les données réelles AxelorMetal.

---

## La démonstration — ce que le jury verra

Une démonstration **déterministe de 10 minutes** sur données entièrement synthétiques (graine `240725`) :

- Tableau de bord usine → cœur Fabric → pilotage énergétique → alerte RUL → qualité → capture du savoir → audit et gouvernance.
- Chaque écran porte le bandeau **« Données synthétiques — pas pour le contrôle opérationnel »**.
- Échelle de repli à 5 niveaux (cloud en direct → rejeu local → cache interactif → enregistrement → pack de preuve statique) — la présentation se termine toujours, même hors réseau.

---

## Posture d'honnêteté

Ce projet distingue systématiquement :

- 🎯 **TARGET** — objectif de transformation, à prouver par un pilote sur données réelles.
- 🔬 **EVIDENCE** — résultat reproductible sur scénario synthétique, montré en direct.

Un seul chiffre présenté comme acquis alors qu'il est projeté coûte plus de crédibilité qu'une fonctionnalité manquante.

---

*Document à l'usage du jury de soutenance — Luxembourg, juillet 2026.*
