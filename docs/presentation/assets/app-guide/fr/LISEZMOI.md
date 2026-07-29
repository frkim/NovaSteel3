# NovaSteel — Guide de l'application pour débutants

**De quoi s'agit-il ?** Une visite complète, capture d'écran par capture d'écran, de
**l'application front-end NovaSteel**, écrite pour une personne qui n'a jamais travaillé
dans la sidérurgie. Chaque écran est expliqué deux fois : une fois en langage simple
(« qu'est-ce que je regarde ? ») et une fois comme élément de preuve (« quelle ligne du
cas d'usage cet écran démontre-t-il, et d'où vient ce chiffre ? »).

**Langues.** 🇫🇷 Français (ce dossier) · 🇬🇧 [English version](../en/README.md)

**Dernière mise à jour :** 2026-07-28 · **Captures d'écran :** 37, prises sur
l'application en fonctionnement à l'adresse `http://localhost:5266` (coque Blazor +
BFF FastAPI, données de démonstration synthétiques).

---

## La version en 60 secondes

| | |
|---|---|
| **L'entreprise** | *AxelorMetal* — un sidérurgiste intégré luxembourgeois fictif, exploitant hauts fourneaux et laminoirs au Luxembourg, en Allemagne, en Belgique et en Espagne. |
| **La plateforme** | *NovaSteel* — la plateforme d'optimisation de production pilotée par l'IA qu'AxelorMetal utilise pour décider de la prochaine action. |
| **Le problème** | L'énergie pèse 35 % du coût de production ; le CO₂ est taxé via le système européen d'échange de quotas (EU ETS) ; une défaillance imprévue du garnissage réfractaire coûte **8 M€** ; la qualité des aciers automobiles haut de gamme dérive ; et les opérateurs qui savent traiter tout cela partent en retraite. |
| **La promesse** | −14 % d'énergie par tonne, −22 % de CO₂, une alerte **21 jours** avant une défaillance de garnissage, +8 points de rendement haut de gamme. |
| **La réserve honnête** | Toutes les données sont **synthétiques**. NovaSteel est **purement consultatif** : il n'écrit jamais de consigne, ne dialogue jamais avec un automate, ne touche jamais à un verrouillage de sécurité. |

---

## À lire dans cet ordre

### Commencez ici

| N° | Chapitre | Ce que vous y trouvez |
|---|---|---|
| 00 | [Prise en main](00-getting-started.md) | La sidérurgie en 3 minutes, le problème métier, les 10 personas et comment lancer l'application vous-même. |
| 01 | [Coque applicative et navigation](01-shell-and-navigation.md) | Chaque bouton du cadre permanent : sélecteur de site, sélecteur de persona, pastille de capacité, thème, langue, bandeau de démonstration, rail de navigation. |
| 02 | [Site public AxelorMetal](02-company-website.md) | Le site institutionnel de 5 pages qui plante le décor — dont *Steel Knowledge*, la meilleure porte d'entrée pour un débutant. |

### Les écrans de travail

| N° | Chapitre | Persona | Démontre |
|---|---|---|---|
| 03 | [Command Center et Operations](03-command-center-and-operations.md) | Directeur d'usine | Triage multi-sites, les 5 KPI principaux |
| 04 | [Furnace Health](04-furnace-health.md) | Opérateur four, ingénieur maintenance | `CHL-03`, `OBJ-02`, `OUT-03`, `AI-01` |
| 05 | [Energy Optimization](05-energy-optimization.md) | Responsable énergie | `CHL-01`, `OBJ-01`, `AI-02` |
| 06 | [Quality](06-quality.md) | Ingénieur qualité | `CHL-04`, `OBJ-03`, `OUT-04` |
| 07 | [Sustainability & Compliance](07-sustainability-and-compliance.md) | Responsable RSE | `CHL-02`, `OUT-02`, `REG-01`…`REG-03` |
| 08 | [Knowledge Hub](08-knowledge-hub.md) | Ingénieur connaissance | `CHL-05`, `OBJ-04`, `AI-03` |
| 09 | [Executive Overview](09-executive-overview.md) | Direction générale | Consolidation `OUT-01`…`OUT-04` |
| 10 | [Device Operations](10-device-operations.md) | Ingénieur systèmes OT | D'où viennent les données capteurs |
| 11 | [Dashboard Collections](11-dashboard-collections.md) | Tous | Bouquets de tableaux de bord organisés par question |
| 12 | [Proof of Execution](12-proof-of-execution.md) | Tous | Le registre complet des exigences, le brief dans l'application et la grille technique |
| 13 | [Platform Ops](13-platform-ops.md) | Exploitation plateforme | Capacité Fabric, traitements, coûts |

### Transverse et référence

| N° | Chapitre | Ce que vous y trouvez |
|---|---|---|
| 14 | [Fonctionnalités transverses](14-cross-cutting-features.md) | L'espace de travail Dockview, le chat Copilot, l'aide « What's this? », la visite guidée, les réglages, les thèmes, la localisation et les composants d'interface partagés. |
| 15 | [Glossaire](15-glossary.md) | Tous les termes sidérurgiques et techniques, EN ↔ FR, avec « où vous le rencontrez dans NovaSteel ». |
| 16 | [Matrice de traçabilité](16-traceability-matrix.md) | Écran ↔ cas d'usage ↔ identifiant d'exigence ↔ preuve ↔ test, pour les 31 écrans. |
| 17 | [Ce qui se passe derrière les écrans](17-how-it-works-behind-the-screens.md) | Ce qui se produit entre un clic et un graphique : coque, microfrontend, BFF, workers et l'architecture Fabric cible. |
| 18 | [Visite guidée de la démonstration](18-guided-demo-walkthrough.md) | Un parcours autonome, plus un tableau de questions/réponses pour le jury et un guide de dépannage. |

---

## Parcours de lecture conseillés

| Si vous êtes… | Lisez |
|---|---|
| **Débutant en sidérurgie et sur l'application** | 00 → 02 → 15 → 03 → 04 → 05 → 06 |
| **En préparation d'une présentation ou d'une soutenance** | 00 → 16 → 12 → 18 → 17 |
| **Développeur rejoignant le projet** | 17 → 01 → 14 → puis le chapitre de l'écran que vous modifiez |
| **Auditeur ou responsable conformité** | 07 → 08 → 12 → 16 |
| **Pressé (15 minutes)** | 00 §« La version en 60 secondes » → 16 §2 → 18 |

---

## Structure de chaque chapitre d'écran

Chaque écran est documenté selon les mêmes sept blocs, afin que vous sachiez toujours où
regarder :

1. **En une phrase** — à quoi sert l'écran.
2. **Contexte sidérurgique** — les notions métier présupposées, expliquées depuis zéro.
3. **Ce que vous voyez à l'écran** — une visite numérotée de chaque panneau et composant visible, avec la façon de le lire et ce qui distingue une bonne d'une mauvaise valeur.
4. **Pourquoi ce composant a été implémenté** — le moteur métier, rattaché à une citation du cahier des charges.
5. **Objectif et preuve** — un tableau reliant l'élément du cas d'usage → l'identifiant d'exigence → la preuve dans l'application → la route d'API et le fichier source d'où vient le chiffre.
6. **Honnêteté et réserves** — données synthétiques, prédiction vs mesure, rôle purement consultatif.
7. **À vous d'essayer** — un chemin de clics à suivre sur `http://localhost:5266`.

---

## Où se trouvent les éléments

| Élément | Chemin |
|---|---|
| Ce guide (français) | `docs/presentation/assets/app-guide/fr/` |
| Ce guide (anglais) | `docs/presentation/assets/app-guide/en/` |
| Captures d'écran (37 PNG) | `docs/presentation/assets/app-guide/screenshots/` |
| Catalogue des exigences (source de vérité) | `apps/analytics-mfe/src/proof/proofCatalog.ts` |
| Cahier des charges du cas d'usage | `docs/usecase/usecase.md` |
| Document de preuve d'exécution | `docs/presentation/proof_of_execution.md` |
| Runbook de démonstration (script de 10 min) | `docs/demo/demo-runbook.md` |
| Code front-end | `apps/portal-shell/` (coque Blazor), `apps/analytics-mfe/` (React) |
| Code back-end | `services/bff-api/`, `services/optimizer-worker/`, `services/scoring-worker/`, `services/knowledge-orchestrator/` |

Les captures d'écran sont des **prises de vue de l'application de ce dépôt, réalisées par
nos soins** — aucune image tierce n'est versionnée. Voir
[`../../PROVENANCE.md`](../../PROVENANCE.md).

---

## Régénérer les captures d'écran

Les captures proviennent de l'application réellement exécutée, elles ne sont pas simulées.
Pour les rafraîchir :

1. Démarrez le BFF : `npm run run:bff` (sert `http://localhost:8080`).
2. Reconstruisez le bundle React si vous l'avez modifié : `npm run build:analytics`.
3. Démarrez la coque : `dotnet run --project apps\portal-shell\PortalShell.csproj` (sert `http://localhost:5266`).
4. Parcourez chaque route `/{site}/{section}/{subView}` et capturez la page entière dans une fenêtre de 1680 px de large, en enregistrant sous `docs/presentation/assets/app-guide/screenshots/<slug-de-l-ecran>.png`.

Les restaurations de paquets doivent utiliser exclusivement les flux protégés Microsoft —
voir [`docs/tech/security_requirement.md`](../../../../tech/security_requirement.md).

---

▶ Commencez par [00 · Prise en main](00-getting-started.md).

