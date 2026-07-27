# 18 · Parcours guidé de démonstration

**Public visé :** nouvel arrivant répétant seul la démonstration NovaSteel à `http://localhost:5266`.  
**Temps de lecture :** ~20 minutes.  
**Dernière mise à jour :** 2026-07-27  
**Langue :** 🇬🇧 [English version](../en/18-guided-demo-walkthrough.md)

---

## 0. Prérequis et démarrage

Exécutez les commandes depuis la racine du dépôt. N'ajoutez pas de sources Python ou NuGet non approuvées ; le dépôt utilise les feeds Microsoft protégés (`README.md:41-55`; `docs\tech\security_requirement.md:16-27`).

Construisez une fois si le bundle React ou le portail a changé :

```powershell
npm run build:analytics
dotnet restore .\apps\portal-shell\PortalShell.csproj --configfile .\NuGet.Config --locked-mode
npm run build:portal
```

Ces commandes de build sont celles du handoff racine (`README.md:102-108`).

Démarrez le BFF :

```powershell
npm run run:bff
```

Vérifiez :

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health/ready
```

Le BFF sert la fixture déterministe `demo-full` sur le port 8080 (`README.md:99-120`).

Démarrez le shell :

```powershell
dotnet run --project .\apps\portal-shell\PortalShell.csproj
```

Ouvrez `http://localhost:5266`. Si votre profil local affiche un autre port (par exemple `http://localhost:5000` lorsque le profil `http` n'est pas sélectionné), utilisez les mêmes chemins sur ce port ; la grammaire reste `/{site}/{section}/{subView}` et le CORS du BFF autorise `http://localhost:5266`, `http://localhost:5000`, `http://localhost:5173` et `https://localhost:7075` (`apps\portal-shell\Pages\AnalyticsHost.razor:1-4`; `services\bff-api\src\bff_api\config.py:141-146`).

---

## 1. Visite arrêt par arrêt

### Arrêt 1 — Accueil du site AxelorMetal

**URL :** `http://localhost:5266/lu/company-website/home`  
![Accueil du site AxelorMetal](../screenshots/company-website-home.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Le héros **Engineering the future of steel** et les cartes **Integrated production**, **AI-driven optimization**, **Responsible steelmaking**, **Steel knowledge**. | « AxelorMetal est l'opérateur fictif ; NovaSteel est la plateforme d'aide à la décision que nous défendons. » Cela installe le récit métier avant les écrans plateforme (`apps\analytics-mfe\src\personaRoutes.ts:167-180`; `docs\presentation\assets\app-guide\en\16-traceability-matrix.md:43-50`). | « Pour qui est cette application ? » |

### Arrêt 2 — Command Center

**URL :** `http://localhost:5266/lu/command-center/overview`  
![Vue Command Center](../screenshots/command-center-overview.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Quatre cartes de site, cinq KPI, une alerte critique et **Next-best actions**. | « C'est la page de triage de Marc Weber : énergie, CO₂, RUL du four, rendement haut de gamme et alertes en une vue. » Elle soutient `OUT-01` et renvoie vers les autres preuves (`apps\analytics-mfe\src\personaRoutes.ts:18-24`; `docs\presentation\assets\app-guide\en\16-traceability-matrix.md:88-98`). | « Où voir la priorité du jour ? » |

### Arrêt 3 — Simulateur Device Operations

**URL :** `http://localhost:5266/lu/device-operations/simulator`  
![Simulateur Device Operations](../screenshots/device-operations-simulator.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| **Simulator state: running**, scénario **demo-full**, ticks, appareils, capteurs et incidents actifs. | « La démo est répétable. Un simulateur déterministe intégré au BFF alimente l'histoire, pas des modifications manuelles d'écran. » Cela soutient la provenance de `AI-01` (`docs\README.md:37-41`; `README.md:201-216`). | « D'où viennent les signaux ? » |

### Arrêt 4 — Furnace Health : Lining Forecast

**URL :** `http://localhost:5266/lu/furnace-health/lining-forecast`  
![Prévision du garnissage four](../screenshots/furnace-health-lining-forecast.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Risque de garnissage autour de 90 %, jours jusqu'au seuil autour de 19,7, bande P10–P90, seuil rouge 80 %, panneau des facteurs. | « C'est la preuve IA la plus forte : une régression RUL transparente sur historique thermique synthétique, avec incertitude et facteurs. » Elle prouve `CHL-03`, `OBJ-02`, `OUT-03`, `AI-01` (`services\scoring-worker\src\scoring_worker\rul_model.py:106-197`; `docs\validation-report.md:43-44`). | « Comment NovaSteel prévient avant une défaillance de garnissage à 8 M€ ? » |

### Arrêt 5 — Furnace Health : Maintenance Planner

**URL :** `http://localhost:5266/lu/furnace-health/maintenance-planner`  
![Planification maintenance four](../screenshots/furnace-health-maintenance-planner.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Inspection BF-01 urgente, fenêtre de relining, planning type Gantt et ordre synthétique `WO-DEMO-LUX-1042`. | « La prévision devient une inspection planifiée. Elle n'actionne pas le four ; le processus maintenance humain reste responsable. » Cela soutient `OBJ-02` et `OUT-03` (`services\bff-api\src\bff_api\repository.py:276-285`; `docs\validation-report.md:43-44`). | « Que se passe-t-il après l'alerte ? » |

### Arrêt 6 — Energy Optimization : Spot & Schedule

**URL :** `http://localhost:5266/lu/energy-optimization/spot-price-schedule`  
![Prix spot et planning énergie](../screenshots/energy-optimization-spot-price-schedule.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Pic à 280 EUR/MWh, économies projetées, intensité CO₂, charge déplaçable, courbe prix/charge et lignes de planning. | « L'énergie est aussi un problème de planning. L'écran montre quels lots de réchauffage flexibles peuvent éviter le pic de prix. » Il soutient `CHL-01`, `OBJ-01` et la supervision `REG-02` (`docs\data\synthetic-data-and-simulators.md:128-135`; `docs\validation-report.md:45`). | « Pourquoi le prix spot de l'électricité compte dans l'acier ? » |

### Arrêt 7 — Energy Optimization : Load-Shift Simulator

**URL :** `http://localhost:5266/lu/energy-optimization/load-shift-simulator`  
![Simulateur de déplacement de charge](../screenshots/energy-optimization-load-shift-simulator.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Barres baseline vs optimized, curseurs de fenêtre et concurrence, **Simulate schedule**, **Record simulated approval**. | « L'optimiseur MILP trouve un planning consultatif faisable, sans violation dure. L'approbation est simulée/shadow et n'écrit pas dans le planning production. » Il prouve `AI-02` (`services\optimizer-worker\src\optimizer_worker\milp.py:40-145`; `docs\validation-report.md:45`). | « L'IA contrôle-t-elle la production ? » |

### Arrêt 8 — Quality : Batch Quality

**URL :** `http://localhost:5266/lu/quality/batches`  
![Qualité des batches](../screenshots/quality-batches.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| High-grade yield, first-pass yield, NCR, defect rate, tendance de rendement et table pass/fail. | « La qualité est tracée lot par lot ; le prédit et le mesuré sont séparés. » Cela soutient `CHL-04`, `OBJ-03`, `OUT-04` (`docs\data\synthetic-data-and-simulators.md:137-160`; `docs\validation-report.md:46`). | « Comment afficher la qualité sans cacher les rebuts ? » |

### Arrêt 9 — Quality : SPC

**URL :** `http://localhost:5266/lu/quality/spc`  
![SPC qualité](../screenshots/quality-spc.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Un point hors contrôle, Cpk, part du principal défaut, carte de contrôle et Pareto. | « SPC signifie statistical process control : cela montre quand la variation ne ressemble plus à un comportement normal. » Cela soutient `OBJ-03` (`apps\analytics-mfe\src\components\screens\screenRegistry.ts:41-42`; `docs\presentation\assets\app-guide\en\16-traceability-matrix.md:97-99`). | « Comment voir tôt une dérive qualité ? » |

### Arrêt 10 — Sustainability : émissions et ETS

**URL :** `http://localhost:5266/lu/sustainability-compliance/emissions-ledger`  
![Registre d'émissions](../screenshots/sustainability-emissions-ledger.png)

Puis ouvrez :

**URL :** `http://localhost:5266/lu/sustainability-compliance/ets-exposure`  
![Exposition ETS](../screenshots/sustainability-ets-exposure.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Tendance CO₂ vs cible, scopes, registre immuable, projection ETS, 71 % de quotas utilisés et alerte de dépassement au mois 5. | « Le carbone est opérationnel et financier. L'app relie décisions énergie, émissions et exposition ETS, tout en indiquant que les valeurs sont synthétiques. » Cela soutient `CHL-02`, `OUT-02` et `REG-03` partiel (`docs\architecture\solution-architecture.md:148-155`; `docs\presentation\assets\app-guide\en\16-traceability-matrix.md:106-108`). | « Comment le planning se relie-t-il au carbone ? » |

### Arrêt 11 — Knowledge Hub : Procedures

**URL :** `http://localhost:5266/lu/knowledge-hub/procedures`  
![Procédures Knowledge Hub](../screenshots/knowledge-hub-procedures.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Procédure approuvée, procédure en revue, recherche, barres de couverture, pipeline workflow et **Human-in-the-loop gate**. | « GenAI peut rédiger depuis des entretiens, mais un Knowledge Engineer relit avant que le contenu soit retrouvable. » Cela prouve `CHL-05` et `AI-03` (`services\knowledge-orchestrator\src\knowledge_orchestrator\orchestrator.py:190-242`; `services\knowledge-orchestrator\src\knowledge_orchestrator\retrieval.py:1-10`). | « Comment un récit d'opérateur devient-il une procédure sûre ? » |

### Arrêt 12 — Panneau Copilot

**URL :** `http://localhost:5266/lu/command-center/overview`, puis cliquez **Copilot**.  
![Panneau Copilot](../screenshots/feature-copilot-panel.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Dock à droite, avis vert de protection, questions suggérées, glossaire, zone de saisie et options de raisonnement. | « Copilot explique l'écran actif. Il n'a pas d'outils data-plane ; il répond avec contexte écran, glossaire et sources ancrées. » Cela montre l'assistant transverse (`apps\analytics-mfe\src\api\copilotClient.ts:145-163`; `docs\implementation\api-contracts.md:300-306`). | « Puis-je poser des questions en langage simple ? » |

### Arrêt 13 — Executive Overview

**URL :** `http://localhost:5266/lu/executive-overview/overview`  
![Vue executive](../screenshots/executive-overview.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| Énergie, CO₂, rendement haut de gamme, avertissement 21 jours, failures prevented, comparaison de sites et barres target-vs-actual. | « C'est la consolidation direction. Les chiffres sont des cibles ou preuves synthétiques, pas des résultats industriels réalisés. » Cela soutient `OUT-01`…`OUT-04` (`apps\analytics-mfe\src\components\screens\ExecutiveOverview.tsx:28-31`; `docs\presentation\oral-defense-and-slide-plan.md:21-29`). | « Comment la direction voit-elle la valeur ? » |

### Arrêt 14 — Registre Proof of Execution

**URL :** `http://localhost:5266/lu/proof-of-execution/requirements`  
![Registre Proof of Execution](../screenshots/proof-of-execution-requirements.png)

| À regarder | À dire / ce que cela prouve | Question débutant résolue |
|---|---|---|
| 19 exigences suivies, 15 atteintes, 4 partielles/substituts, filtres, table et panneau evidence. | « C'est le filet de sécurité de soutenance : chaque affirmation a un ID, une preuve, une réserve et un chemin source. » Cela soutient les 19 IDs (`apps\analytics-mfe\src\proof\proofCatalog.ts`; `docs\presentation\assets\app-guide\en\16-traceability-matrix.md:77-83`). | « Où répondre à “prouvez-le” ? » |

---

## 2. Dix questions du jury et où répondre à l'écran

| Question | Meilleur écran | Réponse courte |
|---|---|---|
| Les 14 %, 22 %, 21 jours et 8 % sont-ils prouvés ? | Executive Overview + Proof of Execution | Ce sont des cibles sauf le mécanisme RUL synthétique ; la démo prouve la mécanique, pas les économies usine réalisées (`docs\presentation\faq.md:19-35`). |
| Pourquoi Microsoft Fabric ? | Sustainability / chapitre 17 | Fabric est le cœur gouverné visé : KQL chaud, OneLake medallion, sémantique Direct Lake et Power BI (`docs\presentation\faq.md:38-54`). |
| Pourquoi Blazor plus React ? | N'importe quel écran | Blazor possède shell/identité/navigation ; React possède les dashboards MUI/D3 denses (`docs\presentation\faq.md:65-67`). |
| L'IA peut-elle contrôler le four ? | Maintenance Planner | Non ; l'app est consultative et enregistre des décisions humaines (`docs\presentation\faq.md:71-73`). |
| Qu'est-ce qui évite l'hallucination ? | Copilot + Knowledge Hub | Python calcule les nombres ; RAG/Copilot est ancré, cité, filtré et limité en outils (`docs\presentation\faq.md:116-126`). |
| Les données sont-elles réelles ? | Device Simulator + bandeau démo | Non ; données synthétiques déterministes avec graines, fixtures et checksums (`docs\data\synthetic-data-and-simulators.md:3-25`). |
| Comment le RGPD est-il traité ? | Knowledge Hub + `REG-01` | Consentement, redaction, effacement et tombstones préservant l'audit (`docs\README.md:32-50`). |
| Et si une identité est compromise ? | Tableau sécurité du chapitre 17 | Rôles applicatifs, Azure RBAC, Fabric, Foundry et capacité sont des plans séparés (`docs\presentation\faq.md:133-148`). |
| Comment prouver les économies d'énergie ? | Load-Shift Simulator + Proof | La démo montre une recommandation synthétique faisable ; les gains réels demandent un ledger de pilote (`docs\validation-report.md:43-54`). |
| Où sont les sources ? | Registre Proof + chapitre 16 | Les preuves pointent vers route, API, worker et tests (`docs\presentation\assets\app-guide\en\16-traceability-matrix.md:133-162`). |

---

## 3. Dépannage

| Symptôme | Cause probable | Action |
|---|---|---|
| Zone analytique blanche | Bundle React absent ou obsolète. | Lancez `npm run build:analytics`; le pont JS affiche un fallback si l'import échoue (`apps\portal-shell\wwwroot\js\analyticsBridge.js:12-40`). |
| BFF inaccessible | `npm run run:bff` n'est pas lancé ou le port 8080 est indisponible. | Démarrez le BFF et vérifiez `http://127.0.0.1:8080/health/ready` (`README.md:110-120`). |
| Port déjà utilisé | Un autre processus possède 8080 ou le port shell. | Utilisez `Get-NetTCPConnection -State Listen -LocalPort <port>` et arrêtez uniquement le PID propriétaire ; le README montre ce modèle (`README.md:176-190`). |
| Bundle React périmé | Le code UI a changé mais le bundle n'a pas été reconstruit. | Exécutez `npm run build:analytics`, puis redémarrez le shell (`README.md:102-108`). |
| Origine CORS refusée | L'origine du shell n'est pas autorisée par le BFF. | Utilisez une origine par défaut ou configurez volontairement `BFF_CORS_ORIGINS` (`services\bff-api\src\bff_api\config.py:141-146`). |
| Réponse Copilot en échec | BFF ou route chat en erreur. | Reconnectez le BFF et renvoyez une fois ; Copilot ne fabrique pas silencieusement une réponse ancrée (`apps\analytics-mfe\src\api\copilotClient.ts:145-163`). |
| Contrôles capacité simulés | Mode démo ou capacité locale. | C'est attendu : transitions simulées et médiées par BFF ; le navigateur n'appelle jamais ARM (`apps\portal-shell\Components\CapacityPanel.razor:19-31`; `apps\portal-shell\Services\CapacityService.cs:6-11`). |

---

◀ [17 · Ce qui se passe derrière les écrans](17-how-it-works-behind-the-screens.md) · ▲ [Sommaire](LISEZMOI.md)
