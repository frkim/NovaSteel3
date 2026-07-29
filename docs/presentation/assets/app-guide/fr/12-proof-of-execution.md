# 12 · Preuve d'exécution & Exigences techniques

**Audience :** jury, examinateur, auditeur, développeur ou débutant qui veut des preuves  
**Temps de lecture :** 30 minutes  
**Persona :** tous les personas, surtout le jury de soutenance  
**Parcours couverts :** `/{site}/proof-of-execution/requirements`, `/{site}/proof-of-execution/use-case`, `/{site}/technical-requirements/criteria`  
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

**Ce que vous voyez à l'écran.**
1. **Deux onglets.** `Requirement Register` et `Use Case` s'affichent au-dessus de l'espace de travail ; c'est l'onglet Use Case qui est sélectionné ici (`apps\analytics-mfe\src\components\screens\ProofOfExecution.tsx`).
2. **Bande KPI.** Requirements tracked **19**, Met **15**, Partially met **4**, Coverage **78,9 %** — calculés à partir du même catalogue que le registre, garantissant que les deux onglets restent toujours cohérents (`UseCaseBrief.tsx`; `apps\analytics-mfe\src\proof\proofCatalog.ts`).
3. **Panneau « Source of truth ».** Intitulé *NovaSteel — AI-Powered Steel Production Optimization Platform*, il indique « The original brief, reproduced word for word, with the reference ID that proves each statement », renvoie vers `docs/usecase/usecase.md` sur GitHub, et affiche une puce verte **15 of 19 statements evidenced** (`UseCaseBrief.tsx`; `docs\usecase\usecase.md`).
4. **Panneau « Industry profile ».** Industry *Heavy Industry & Metals*, Headquarters *Luxembourg*, Operating region *Luxembourg, Germany, Belgium, Spain*, Regulatory context *GDPR · EU AI Act · Sector-specific EU Directives* — cette dernière ligne portant les badges `REG-01`, `REG-02` et `REG-03` (`UseCaseBrief.tsx`).
5. **Panneau « Business challenge ».** Les cinq défis du brief, chacun avec son badge : énergie à 35 % du coût de production (`CHL-01`), pression EU ETS sur le CO₂ (`CHL-02`), usure de revêtement imprévisible à 8 M€ par événement (`CHL-03`), constance de qualité pour les clients automobiles (`CHL-04`), départ à la retraite des opérateurs experts (`CHL-05`).
6. **Panneau « Transformation objective ».** Réduire la consommation d'énergie (`OBJ-01`), prédire les pannes d'équipement (`OBJ-02`), améliorer la qualité de l'acier (`OBJ-03`), et capturer les savoir-faire experts (`OBJ-04`).
7. **Panneaux « Expected outcome » et « AI infusion point ».** Les chiffres cibles — par exemple, énergie par tonne réduite de 14 % — et les mécanismes IA : un modèle ML informé par la physique qui prédit la dégradation du revêtement à partir des signatures thermiques (`AI-01`), et un agent d'optimisation de la distribution d'énergie qui planifie les procédés énergivores autour des prix spot (`AI-02`).

**Comment lire les couleurs des badges.** Vert signifie que l'exigence est `met` (satisfaite) ; ambre indique `partial` ou `demo`. Un badge n'est pas décoratif : cliquez sur l'onglet Requirement Register et le même ID y porte sa preuve et sa limite (`UseCaseBrief.tsx`; `proofCatalog.ts`).

**Pourquoi ce composant a été implémenté.** Le brief demande une “AI-driven production optimization platform” et liste des résultats mesurables (`docs\usecase\usecase.md`). L'afficher dans l'application évite un écart entre discours et preuve (`UseCaseBrief.tsx`; `docs\presentation\proof_of_execution.md`).

**Objectif & preuves (proof of execution).**

| Élément du cas d'usage | ID exigence | Preuve dans l'application | Origine du nombre (route API + fichier source) |
|---|---|---|---|
| Brief dans l'app | 19 exigences | Lignes du brief avec badges | Aucun BFF ; tableaux `PROFILE`, `CHALLENGES`, `OBJECTIVES`, `OUTCOMES`, `AI_POINTS` dans `UseCaseBrief.tsx`. |
| Traçabilité source | 19 exigences | Lien `docs/usecase/usecase.md` | `USECASE_SOURCE_URL` dans `UseCaseBrief.tsx`. |
| Statut honnête | 19 exigences | Couleur selon les IDs | `statusOf()` lit `PROOF_BY_ID` (`UseCaseBrief.tsx`; `proofCatalog.ts`). |

**Comment les données arrivent à l'écran.** `UseCaseBrief.tsx` → tableaux locaux issus de `docs\usecase\usecase.md` → `PROOF_BY_ID` et `proofCoverage()` → aucun BFF. Les écrans de preuve ont leurs propres routes (`UseCaseBrief.tsx`; `dataClient.ts`).

**Honnêteté & limites.** L'onglet Use Case est une projection du registre, pas une source de vérité indépendante : si une exigence évolue, les deux onglets se mettent à jour ensemble. La couverture affichée de **78,9 %** n'est pas 100 % à dessein : quatre énoncés ne sont que partiellement attestés ou représentés par un substitut de démonstration, et l'onglet le dit sans les dissimuler (`UseCaseBrief.tsx`; `proofCatalog.ts`).

**Essayez vous-même.** Ouvrez `http://localhost:5266/lu/proof-of-execution/use-case`, lisez le panneau *Business challenge*, puis cliquez sur l'onglet **Requirement Register** et recherchez `CHL-03` — la panne de revêtement à 8 M€ — pour voir la preuve derrière le badge que vous venez de lire.

---

## Exigences techniques (Technical Requirements) — `/{site}/technical-requirements/criteria`
![Exigences techniques](../screenshots/technical-requirements-criteria.png)

**En une phrase.** Le barème de notation répondu critère par critère : pour chacun des 12 critères techniques, l'application affiche la note qu'elle s'attribue, la preuve correspondante et — quand la note est inférieure à 5 — l'écart constaté et les travaux qui permettraient de le combler (`apps\analytics-mfe\src\components\screens\TechnicalRequirements.tsx` ; `apps\analytics-mfe\src\proof\technicalCatalog.ts`).

**Contexte pour débutants.** Les deux écrans précédents répondent à la question : *"l'application fait-elle ce que le brief demande ?"*. Celui-ci répond à une question différente : *"est-elle bien construite ?"* Un **barème** est la grille d'évaluation qu'utilise un jury — architecture, design patterns, sécurité, supervision, IA, etc. — chaque critère étant noté sur 5. NovaSteel publie sa propre note contre cette grille directement dans le produit, de sorte que rien ne doit être pris sur parole (`docs\tech\rating_grid.md`).

**Pourquoi cet écran ressemble à l'écran Proof of Execution.** C'est intentionnel. Un jury passant d'un onglet à l'autre n'a qu'une seule mise en page à apprendre : bande KPI → puces de catégories → table de recherche → panneau de détail à droite (`TechnicalRequirements.tsx`).

**Ce que vous voyez à l'écran.**
1. **Bande KPI.** **Total score 56 / 60**, **Grade band A** — *"Exceptional implementation and architectural rigor"* —, **Criteria at 5/5 : 8 / 12** et **Criteria assessed : 12** (`techScorecard()` dans `technicalCatalog.ts`).
2. **Puces de catégories avec sous-totaux courants.** Design (15/15), Development (8/10), Monitoring (5/5), AI integration (9/10), Agentic behaviour (10/10), Additional architecture (4/5), Presentation & documentation (5/5). Un clic filtre la table (`TechnicalRequirements.tsx`).
3. **Barre de progression** pour le total, accompagnée de la phrase *"Self-assessed against docs/tech/rating_grid.md. Every score below 5 states its gap and the work that would close it."* avec deux liens GitHub : **rating_grid.md** et **Full analysis** (`RUBRIC_URL` dans `TechnicalRequirements.tsx`).
4. **Champ de recherche** — il parcourt l'ID, le critère, la citation du barème, le verdict, l'explication, l'écart, le plan de remédiation et chaque libellé de preuve en une seule frappe (`TechnicalRequirements.tsx`).
5. **Table du barème** avec colonnes Ref, Category, Criterion, Verdict et Score, recherche par colonne, sélecteur de colonnes, bascule de densité et export (`TechnicalRequirements.tsx`).
6. **Panneau d'évaluation** à droite. La capture sélectionne `TR-DES-01` : une puce verte **Score 5 of 5**, la puce de catégorie **Design**, le titre du critère, le verdict, un bloc *WHAT THE RUBRIC CALLS EXCELLENT* citant le barème mot pour mot, et un bouton **Open the screen** qui saute vers l'écran démontrant le critère.
7. **Panneau Score by category** en dessous, avec une barre par catégorie — verte quand la catégorie est parfaite, ambre quand des points ont été laissés sur la table.

**Comment lire les couleurs de notation.** Vert = 5 / 5, ambre = 4 / 5, rouge = 3 ou moins. Il n'y a pas de rouge sur cet écran aujourd'hui, mais l'ambre est réel et il est là pour être vu (`scoreColor()` dans `TechnicalRequirements.tsx`).

**Pourquoi ce composant a été implémenté.** Une soutenance est évaluée sur un barème, et le geste honnête est de se noter soi-même en premier, publiquement, dans le produit en fonctionnement. Afficher l'auto-évaluation à l'écran — avec les écarts — transforme une affirmation ("l'architecture est modulaire") en quelque chose qu'un jury peut suivre jusqu'au code qui le prouve (`docs\tech\rating_grid.md` ; `docs\tech\technical-analysis.md`).

**Le barème complet, critère par critère.** Ce tableau reprend le catalogue en langage simple (`apps\analytics-mfe\src\proof\technicalCatalog.ts`).

| Ref | Catégorie | Critère | Note | Verdict, en langage simple |
|---|---|---|---|---|
| `TR-DES-01` | Design | Architecture système, modularité, scalabilité | 5 / 5 | Documentée, modulaire et horizontalement scalable par construction. |
| `TR-DES-02` | Design | Utilisation des design patterns | 5 / 5 | Six patterns nommés, chacun choisi pour une pression spécifique, chacun testé unitairement. |
| `TR-DES-03` | Design | Sécurité | 5 / 5 | Threat modeling en premier, puis implémentation — pas ajoutée après coup. |
| `TR-DEV-01` | Development | Démo de l'application | 4 / 5 | Répétée, lisible par un décideur et résistante hors-ligne — mais certains artefacts Fabric ne s'exécutent pas en direct. |
| `TR-DEV-02` | Development | Complétude de l'implémentation | 4 / 5 | Chaque exigence du brief est implémentée et traçable ; quelques intégrations d'entreprise restent au stade de conception. |
| `TR-MON-01` | Monitoring | Journalisation et métriques | 5 / 5 | OpenTelemetry de bout en bout, avec les KPI métier traités comme des métriques de premier rang. |
| `TR-AI-01` | AI integration | Utilisation des technologies IA | 5 / 5 | Quatre techniques IA distinctes, chacune répondant à une ligne nommée du brief. |
| `TR-AI-02` | AI integration | Sélection et déploiement du modèle IA | 4 / 5 | Choix de modèle par niveau, déployé de façon sécurisée dans l'UE — mais le cycle de vie est documenté, pas automatisé. |
| `TR-AGT-01` | Agentic behaviour | Autonomie et orchestration | 5 / 5 | Un vrai graphe d'états avec travaux de sécurité autonomes et une validation humaine délibérée. |
| `TR-AGT-02` | Agentic behaviour | Coordination multi-agents | 5 / 5 | Les trois patterns nommés — handoff, reflection et graphe d'états — sont implémentés et tracés. |
| `TR-ARC-01` | Additional architecture | Performance et fiabilité | 4 / 5 | La fiabilité est intégrée à la conception ; elle n'est pas encore étayée par des mesures. |
| `TR-PRE-01` | Presentation & documentation | Clarté de l'explication et de la présentation | 5 / 5 | Trois registres d'audience — décideur, technique et débutant — chacun servi délibérément. |

**Les quatre écarts, énoncés sans détour.** Ce sont les seuls critères en dessous de 5, et l'application affiche chaque écart à côté de sa note plutôt que de l'arrondir (`technicalCatalog.ts`).

| Ref | Ce qui manque honnêtement |
|---|---|
| `TR-DEV-01` | Certains artefacts Fabric (notebooks, règles Activator, l'eventstream Real-Time Intelligence) sont provisionnés comme modèles et démontrés à partir de sorties capturées plutôt qu'exécutés en direct dans la fenêtre de démo de 10 minutes. |
| `TR-DEV-02` | Les intégrations Manufacturing Execution System (MES) et batch historian sont spécifiées dans l'architecture mais non implémentées ; la démo lit un flux synthétique à leur place. |
| `TR-AI-02` | Il n'existe pas d'artefact registre de modèles, de notebook d'entraînement ou de gate d'évaluation automatisé dans le dépôt. Le versionnage des modèles est une constante dans le code et le modèle physique est ajusté analytiquement plutôt qu'entraîné ; le cycle de vie est donc décrit dans la documentation plutôt qu'appliqué par outillage. |
| `TR-ARC-01` | Aucun résultat de test de charge, aucune cible SLO/SLA publiée et aucun middleware circuit-breaker dans le code. Les affirmations de fiabilité reposent sur la configuration d'infrastructure et l'intention de conception plutôt que sur un comportement mesuré sous charge. |

**Objectif & preuves (proof of execution).**

| Élément du cas d'usage | ID exigence | Preuve dans l'application | Origine du nombre (route API + fichier source) |
|---|---|---|---|
| La qualité de construction est défendable | — (barème, pas brief) | 12 critères, 56/60, grade A, avec liens de preuve par critère | Aucun BFF ; `techScorecard()` et `TECH_REQUIREMENTS` dans `apps\analytics-mfe\src\proof\technicalCatalog.ts`. |
| Chaque note trace vers le code | — | Les puces de preuve pointent vers des liens GitHub | `githubUrlFor()` dans `apps\analytics-mfe\src\proof\proofCatalog.ts`, réutilisé par `TechnicalRequirements.tsx`. |
| Chaque écart a une correction nommée | `TR-DEV-01`, `TR-DEV-02`, `TR-AI-02`, `TR-ARC-01` | `gap` + `uplift` affichés dans le panneau d'évaluation | Champs `gap` / `uplift` dans `technicalCatalog.ts`. |
| Critère → écran de preuve | 10 sur 12 | Bouton **Open the screen** | `primaryRoute` dans `technicalCatalog.ts` ; navigation via l'événement `nav.intent` (`TechnicalRequirements.tsx`). |

**Comment les données arrivent à l'écran.** `TechnicalRequirements.tsx` → `TECH_REQUIREMENTS`, `TECH_CATEGORY_ORDER`, `techScorecard()` → **aucun BFF** → le catalogue local (`apps\analytics-mfe\src\proof\technicalCatalog.ts`). Comme le registre, c'est une projection purement côté client d'un seul fichier, qui s'affiche identiquement hors-ligne. Le récit long derrière ces mêmes notes se trouve dans `docs\tech\technical-analysis.md`, et le barème dans `docs\tech\rating_grid.md` ; les trois doivent rester synchronisés manuellement.

**Honnêteté & limites.** La note est une **auto-évaluation**, pas un audit externe — l'écran l'indique dans son propre sous-titre. 56/60 n'est pas 60/60 à dessein : quatre critères portent une note ambre et un écart rédigé. Et parce que le catalogue est un fichier TypeScript plutôt qu'un artefact généré, le maintenir aligné avec `docs\tech\technical-analysis.md` est une discipline, pas une garantie automatisée (`technicalCatalog.ts`).

**Essayez vous-même.** Ouvrez `http://localhost:5266/lu/technical-requirements/criteria`, cliquez sur la puce ambre **Development (8/10)** pour filtrer sur les deux critères à 4/5, sélectionnez `TR-DEV-02` et lisez son écart — puis appuyez sur **Open the screen** pour atterrir sur le Registre des exigences que vous avez lu au début de ce chapitre.

---

[◀ Précédent : 11 · Dashboard Collections](11-dashboard-collections.md) · [▲ Index](LISEZMOI.md) · [Suivant ▶ 13 · Platform Ops](13-platform-ops.md)
