# 12 · Preuve d'exécution

**Audience :** jury, examinateur, auditeur, développeur ou débutant qui veut des preuves  
**Temps de lecture :** 22 minutes  
**Persona :** tous les personas, surtout le jury de soutenance  
**Parcours couverts :** `/{site}/proof-of-execution/requirements`, `/{site}/proof-of-execution/use-case`  
**Dernière mise à jour :** 2026-07-27  
**Langue :** 🇬🇧 [English version](../en/12-proof-of-execution.md)

---

## Registre des exigences (Requirement Register) — `/{site}/proof-of-execution/requirements`
![Registre des exigences](../screenshots/proof-of-execution-requirements.png)

**En une phrase.** Le grand livre des preuves : chaque phrase du brief a un ID stable, un statut, un écran de preuve, des preuves et une limite si besoin (`apps\analytics-mfe\src\components\screens\ProofOfExecution.tsx`; `apps\analytics-mfe\src\proof\proofCatalog.ts`).

**Contexte pour débutants.** Un registre de preuve est une checklist pour examinateur. Au lieu d'affirmer que NovaSteel répond au brief, l'application liste ce qui est prouvé, où le voir et ce qui reste simulé. Les mêmes IDs sont apposés sur les écrans de preuve ; `OUT-03` signifie toujours l'alerte de revêtement de four à 21 jours (`docs\presentation\proof_of_execution.md`; `ProofOfExecution.tsx`).

**Vocabulaire des statuts.**

| Statut | Signification | Pourquoi c'est utile |
|---|---|---|
| Met | La capacité existe et fonctionne dans la démo. | Le jury peut ouvrir l'écran de preuve (`proofCatalog.ts`). |
| Partial | La capacité existe mais couvre moins que le brief. | La limite est annoncée avant d'être découverte par recherche (`docs\presentation\proof_of_execution.md`). |
| Demo surrogate | Le mécanisme est réel ; le chiffre phare est une cible synthétique. | Cela sépare contrôle construit et résultat industriel atteint (`proofCatalog.ts`). |

**Ce que vous voyez à l'écran.**
1. Les cartes KPI affichent **19** exigences, **15** satisfaites, **4** partielles/substituts et **78,9 %** de couverture, calculés par `proofCoverage()` (`proofCatalog.ts`; `ProofOfExecution.tsx`).
2. Les puces de catégories séparent Regulatory context, Business challenge, Transformation objective, Expected outcome et AI infusion point (`proofCatalog.ts`).
3. La recherche couvre IDs, énoncés, cibles, limites et preuves (`ProofOfExecution.tsx`).
4. La barre de progression n'est pas à 100 %, volontairement, car les caveats restent visibles (`ProofOfExecution.tsx`; `docs\presentation\proof_of_execution.md`).
5. La table affiche Ref, Category, Requirement, Target et Status avec tri, recherche et export (`ProofOfExecution.tsx`; `docs\ux\dashboard-specification.md`).
6. Le panneau de détail montre explication, preuves et bouton **Open the screen** si une route existe (`ProofOfExecution.tsx`).
7. La capture sélectionne `REG-01`, avec la preuve GDPR : consentement, minimisation, effacement et tombstone d'audit (`proofCatalog.ts`).

**Pourquoi ce composant a été implémenté.** Le brief liste contexte réglementaire, cinq défis, quatre objectifs, quatre résultats et trois points d'IA (`docs\usecase\usecase.md`). Le registre transforme ces phrases en preuves traçables (`docs\presentation\proof_of_execution.md`; `proofCatalog.ts`).

**Registre complet.** Ce tableau reprend le catalogue en français simple (`apps\analytics-mfe\src\proof\proofCatalog.ts`).

| ID | Exigence en langage simple | Statut | Écran(s) de preuve | Preuve |
|---|---|---|---|---|
| `REG-01` | Les données personnelles opérateur doivent être licites, minimisées et effaçables. | Met | Audit & Reports | Consentement, redaction PII, effacement, tombstone d'audit (`proofCatalog.ts`). |
| `REG-02` | L'IA influençant l'industrie exige supervision humaine et transparence. | Met | Energy Optimization; Audit | Graphe validé par humain, outils interdits, défense de prompt, sécurité de contenu (`proofCatalog.ts`). |
| `REG-03` | La comptabilité EU ETS doit être reportable. | Partial | ETS Exposure; Emissions Ledger | Émissions gold et routes summary ; constantes de démo (`proofCatalog.ts`). |
| `CHL-01` | L'énergie vaut 35 % du coût et doit être optimisée. | Met | Spot & Schedule; Load-Shift Simulator | Programme linéaire mixte (MILP) ; `POST /v1/energy/schedules:simulate` (`proofCatalog.ts`). |
| `CHL-02` | Le CO₂ est sous pression EU ETS. | Met | Emissions Ledger | Terme carbone dans l'optimiseur, métrique et registre (`proofCatalog.ts`). |
| `CHL-03` | L'usure de revêtement doit être prédite avant une panne à 8 M€. | Met | Lining Forecast | Features physiques, modèle RUL, route forecast (`proofCatalog.ts`). |
| `CHL-04` | La qualité des aciers automobiles haut de gamme varie trop. | Met | Batch Quality; Defect Analytics (SPC) | Risque batch, contrôle statistique des procédés, what-if qualité (`proofCatalog.ts`). |
| `CHL-05` | Le savoir des opérateurs part à la retraite. | Met | Procedures; Capture Status | Entretiens avec consentement, procédures revues, recherche sur approuvé seulement (`proofCatalog.ts`). |
| `OBJ-01` | Réduire la consommation d'énergie. | Met | Energy Optimization; Command Center | Énergie par tonne issue du planning résolu (`proofCatalog.ts`). |
| `OBJ-02` | Prédire les pannes d'équipement. | Met | Lining Forecast; Maintenance Planner | Scoring RUL et règle Real-Time Intelligence (`proofCatalog.ts`). |
| `OBJ-03` | Améliorer la qualité de l'acier. | Met | Quality | Rendement prédit, Pareto défauts, SPC, what-if borné (`proofCatalog.ts`). |
| `OBJ-04` | Capturer et structurer l'expertise. | Met | Capture Status | Entretien parlé vers procédure citée, revue, versionnée (`proofCatalog.ts`). |
| `OUT-01` | Réduire l'énergie par tonne de 14 %. | Demo surrogate | Command Center; Executive Overview | Mécanisme réel ; −14 % est une cible synthétique (`proofCatalog.ts`). |
| `OUT-02` | Réduire les émissions CO₂ de 22 %. | Demo surrogate | Emissions Ledger; Executive Overview | Recalcul Scope 2 ; −22 % reste une ambition (`proofCatalog.ts`). |
| `OUT-03` | Prévoir une panne de revêtement 21 jours à l'avance. | Met | Lining Forecast | Seuil P50 ≤ 21 jours et risque ≥ 0,80 (`proofCatalog.ts`). |
| `OUT-04` | Améliorer le rendement haut de gamme de 8 points. | Demo surrogate | Batch Quality; Executive Overview | Rendement synthétique scoré ; +8 est la cible (`proofCatalog.ts`). |
| `AI-01` | Un ML informé par la physique prédit la dégradation du revêtement. | Met | Thermal Explorer | Features thermiques et régression avec incertitude (`proofCatalog.ts`). |
| `AI-02` | L'agent d'énergie planifie selon les prix spot. | Met | Load-Shift Simulator | Solveur MILP, handoff agent, approbation humaine (`proofCatalog.ts`). |
| `AI-03` | La GenAI transforme les entretiens en procédures cherchables. | Met | Procedures | Speech-to-text, extraction ancrée, boucle critique, recherche hybride (`proofCatalog.ts`). |

**Conception anti-dérive.** `docs\presentation\proof_of_execution.md`, l'écran, les badges et ce guide projettent tous `apps\analytics-mfe\src\proof\proofCatalog.ts`. `ProofOfExecution.tsx` importe `PROOF_REQUIREMENTS`, et les badges résolvent `PROOF_BY_ID`; un ID ne peut pas changer de sens silencieusement (`ProofOfExecution.tsx`; `proofCatalog.ts`).

**Objectif & preuves (proof of execution).**

| Élément du cas d'usage | ID exigence | Preuve dans l'application | Origine du nombre (route API + fichier source) |
|---|---|---|---|
| Brief complet | `REG-01`…`AI-03` | Registre filtrable avec caveats et liens | Aucun BFF ; `ProofOfExecution.tsx` importe `PROOF_REQUIREMENTS` de `proofCatalog.ts`. |
| Couverture | 19 exigences | 19 total, 15 Met, 4 partial/demo, 78,9 % | `proofCoverage()` dans `proofCatalog.ts`. |
| IDs stables | 19 exigences | Badges et panneau détail | `ProofBadge` résout `PROOF_BY_ID` (`ProofOfExecution.tsx`; `proofCatalog.ts`). |

**Comment les données arrivent à l'écran.** `ProofOfExecution.tsx` → `PROOF_REQUIREMENTS`, `PROOF_CATEGORY_ORDER`, `proofCoverage()` → aucun BFF → catalogue local (`proofCatalog.ts`). Les liens ouvrent les écrans qui utilisent ensuite leur propre `DataClient` si besoin (`dataClient.ts`).

**Honnêteté & limites.** Le registre est crédible parce qu'il n'est pas tout vert : `REG-03` est Partial ; `OUT-01`, `OUT-02`, `OUT-04` sont Demo surrogate (`proofCatalog.ts`). Le document de preuve recommande d'annoncer les caveats avant que le jury les trouve par grep (`docs\presentation\proof_of_execution.md`).

**Essayez vous-même.** Ouvrez `http://localhost:5266/{site}/proof-of-execution/requirements`, cherchez `OUT-02` ou `GDPR`, puis utilisez **Open the screen**.

---

## Cas d'usage (Use Case) — `/{site}/proof-of-execution/use-case`
![Cas d'usage](../screenshots/proof-of-execution-use-case.png)

**En une phrase.** L'onglet Use Case amène le brief original dans l'application et relie chaque ligne aux IDs de preuve (`apps\analytics-mfe\src\components\screens\UseCaseBrief.tsx`).

**Contexte pour débutants.** Un brief de cas d'usage résume industrie, défi, objectif, résultats attendus et mécanismes d'IA. Le brief NovaSteel est `docs\usecase\usecase.md`; le composant le reproduit avec des badges de preuve (`UseCaseBrief.tsx`; `docs\usecase\usecase.md`).

**Ce que vous voyez à l'écran.** La capture fournie montre actuellement la même disposition visible que Requirements : cartes KPI, filtres, barre de progression, registre et détail `REG-01` (`../screenshots/proof-of-execution-use-case.png`; `ProofOfExecution.tsx`). Le composant source Use Case définit :
1. une bande KPI avec `proofCoverage()` (`UseCaseBrief.tsx`; `proofCatalog.ts`) ;
2. un panneau source vers `docs/usecase/usecase.md` (`UseCaseBrief.tsx`) ;
3. le profil industrie : Heavy Industry & Metals, Luxembourg, LU/DE/BE/ES, GDPR/EU AI Act/directives UE (`UseCaseBrief.tsx`; `docs\usecase\usecase.md`) ;
4. défis, objectifs, résultats attendus et points IA, chacun avec badges (`UseCaseBrief.tsx`).

**Pourquoi ce composant a été implémenté.** Le brief demande une “AI-driven production optimization platform” et liste des résultats mesurables (`docs\usecase\usecase.md`). L'afficher dans l'application évite un écart entre discours et preuve (`UseCaseBrief.tsx`; `docs\presentation\proof_of_execution.md`).

**Objectif & preuves (proof of execution).**

| Élément du cas d'usage | ID exigence | Preuve dans l'application | Origine du nombre (route API + fichier source) |
|---|---|---|---|
| Brief dans l'app | 19 exigences | Lignes du brief avec badges | Aucun BFF ; tableaux `PROFILE`, `CHALLENGES`, `OBJECTIVES`, `OUTCOMES`, `AI_POINTS` dans `UseCaseBrief.tsx`. |
| Traçabilité source | 19 exigences | Lien `docs/usecase/usecase.md` | `USECASE_SOURCE_URL` dans `UseCaseBrief.tsx`. |
| Statut honnête | 19 exigences | Couleur selon les IDs | `statusOf()` lit `PROOF_BY_ID` (`UseCaseBrief.tsx`; `proofCatalog.ts`). |

**Comment les données arrivent à l'écran.** `UseCaseBrief.tsx` → tableaux locaux issus de `docs\usecase\usecase.md` → `PROOF_BY_ID` et `proofCoverage()` → aucun BFF. Les écrans de preuve ont leurs propres routes (`UseCaseBrief.tsx`; `dataClient.ts`).

**Honnêteté & limites.** Si l'image capturée montre encore le registre, décrivez les widgets visibles et citez le composant source pour le contenu Use Case attendu. L'onglet est une projection, pas une source séparée (`ProofOfExecution.tsx`; `UseCaseBrief.tsx`; `proofCatalog.ts`).

**Essayez vous-même.** Ouvrez `http://localhost:5266/{site}/proof-of-execution/use-case` et basculez entre Requirements et Use Case si nécessaire.

---

[◀ Précédent : 11 · Dashboard Collections](11-dashboard-collections.md) · [▲ Index](LISEZMOI.md) · [Suivant ▶ 13 · Platform Ops](13-platform-ops.md)
