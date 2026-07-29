# 00 · Bien démarrer

**Public visé :** personnes totalement débutantes dans l'acier et dans l'application NovaSteel.  
**Temps de lecture :** ~15 minutes.  
**Related routes:** `/lu/command-center/overview`, `/lu/dashboards/collections`, `/lu/company-website/home`, `/lu/proof-of-execution/use-case`.  
**Dernière mise à jour :** 2026-07-27  
**Langue :** 🇬🇧 [English version](../en/00-getting-started.md)

---

![Vue d'ensemble du centre de commande](../screenshots/command-center-overview.png)

## Ce qu'est NovaSteel, en 5 lignes

NovaSteel est une interface de démonstration pour une plateforme d'optimisation de production d'acier par IA. Son opérateur fictif est AxelorMetal, producteur d'acier luxembourgeois présent au Luxembourg, en Allemagne, en Belgique et en Espagne (`docs\usecase\usecase.md:7-10`).

L'application aide à comprendre l'énergie, les émissions de CO₂, la santé du four, la qualité de l'acier et la capture du savoir des experts dans un même portail (`docs\ux\dashboard-specification.md:24-35`).

Elle est **uniquement consultative** : aucun écran n'écrit de consigne de four, de commande PLC ni d'action de sécurité (`docs\architecture\solution-architecture.md:22-29`).

Toutes les données du guide sont des **données synthétiques de démonstration**. Elles servent à apprendre et à prouver le fonctionnement, pas à piloter une usine (`docs\architecture\solution-architecture.md:24-27`; `apps\portal-shell\Layout\MainLayout.razor:118-122`).

Quand un chiffre est une prédiction ou une cible, le guide le dit explicitement. Une prédiction n'est pas une mesure réelle de l'usine (`docs\presentation\proof_of_execution.md:317-352`, `docs\presentation\proof_of_execution.md:476-480`).

## La fabrication de l'acier en 3 minutes

| Étape | Explication simple | Pourquoi NovaSteel s'y intéresse |
|---|---|---|
| Minerai de fer (iron ore) | Roche qui contient du fer. C'est la matière première. | C'est le début de la chaîne matière qui deviendra acier (`docs\architecture\solution-architecture.md:17-18`). |
| Haut fourneau (blast furnace) | Grand four qui transforme minerai, coke et calcaire en fonte liquide. | La chaleur du four et l'usure du revêtement sont au cœur de l'alerte à 21 jours (`docs\usecase\usecase.md:16-20`). |
| Fonte liquide (hot metal) | Fer liquide issu du haut fourneau, encore trop chargé en carbone. | Elle alimente ensuite la conversion en acier. |
| Convertisseur BOF (Basic Oxygen Furnace) | Four où l'on souffle de l'oxygène pour réduire le carbone et produire l'acier. | La stabilité du procédé influence qualité et carbone (`docs\usecase\usecase.md:21`, `docs\architecture\solution-architecture.md:18`). |
| Coulée (casting) | L'acier liquide est solidifié en brames, blooms ou billettes. | La généalogie relie les défauts aux heats et aux brames (`docs\personas\personas-and-journeys.md:275-287`). |
| Laminoir (rolling mill) | Des cylindres écrasent et allongent l'acier pour former bobines, tôles ou produits longs. | Les écrans suivent débit et qualité sur ces actifs (`apps\analytics-mfe\src\personaRoutes.ts:27-33`, `apps\analytics-mfe\src\personaRoutes.ts:61-70`). |
| Bobine / tôle (coil / plate) | Produit fini ou semi-fini. Une bobine est une bande enroulée; une tôle est une plaque épaisse. | Les clients automobiles demandent une qualité stable (`docs\usecase\usecase.md:21`). |

Un **revêtement réfractaire (refractory lining)** est la paroi interne résistante à la chaleur d'un four. Il protège la coque métallique. S'il s'use trop, la défaillance peut être grave; le cas d'usage chiffre l'événement à **8 M€** (`docs\usecase\usecase.md:20`).

Un **heat** est une coulée, c'est-à-dire un lot de métal liquide traité ensemble. Un **batch** est un groupe d'enregistrements de production géré comme une unité. NovaSteel suit souvent un heat jusqu'à la brame, la bobine, le résultat qualité et la recommandation (`apps\analytics-mfe\src\personaRoutes.ts:61-70`; `docs\personas\personas-and-journeys.md:275-287`).

L'énergie et le CO₂ dominent le dossier parce que l'acier exige des températures très élevées et parce que la réglementation carbone européenne donne un prix aux émissions. Le brief indique que l'énergie représente **35 % du coût de production** et que le CO₂ est soumis à la pression de l'EU ETS (`docs\usecase\usecase.md:18-19`).

## Le problème métier que NovaSteel adresse

Le brief décrit « un producteur intégré d'acier basé au Luxembourg, exploitant des hauts fourneaux et laminoirs dans quatre pays » confronté à cinq problèmes liés (`docs\usecase\usecase.md:14-22`).

| Problème du brief | Traduction débutant | Preuve / ID |
|---|---|---|
| L'énergie représente 35 % du coût | L'électricité et les combustibles sont si chers que le planning compte. | `CHL-01` (`docs\presentation\proof_of_execution.md:182-208`) |
| CO₂ sous pression EU ETS | L'entreprise doit gérer le coût des quotas carbone. | `CHL-02`, `REG-03` (`docs\presentation\proof_of_execution.md:208-221`, `docs\presentation\proof_of_execution.md:152-154`) |
| Défaillance de revêtement à 8 M€ | L'entreprise veut être prévenue avant qu'une paroi de four ne devienne dangereuse. | `CHL-03` (`docs\presentation\proof_of_execution.md:221-241`) |
| Qualité automobile constante | Les constructeurs automobiles exigent des nuances répétables et traçables. | `CHL-04` (`docs\presentation\proof_of_execution.md:241-259`) |
| Départs à la retraite | Le savoir d'experts part plus vite qu'il n'est documenté. | `CHL-05` (`docs\presentation\proof_of_execution.md:259-276`) |

### Objectifs chiffrés du brief

| Résultat attendu | Cible | Lecture honnête | ID |
|---|---:|---|---|
| Énergie par tonne | −14 % | Cible/surrogate de démonstration, pas économie mesurée en usine. | `OUT-01` (`docs\usecase\usecase.md:39`, `docs\presentation\proof_of_execution.md:317-328`) |
| Émissions de CO₂ | −22 % | Cible sur données synthétiques, pas déclaration EU ETS réelle. | `OUT-02` (`docs\usecase\usecase.md:40`, `docs\presentation\proof_of_execution.md:328-340`) |
| Alerte revêtement four | 21 jours | Le mécanisme de prévision est démontré et marqué satisfait. | `OUT-03` (`docs\usecase\usecase.md:41`, `docs\presentation\proof_of_execution.md:340-352`) |
| Rendement acier haut de gamme | +8 % | Cible modélisée sur lots synthétiques. | `OUT-04` (`docs\usecase\usecase.md:42`, `docs\presentation\proof_of_execution.md:352-362`) |

## Qui l'utilise

L'application est organisée par **persona**, c'est-à-dire un rôle nommé qui détermine l'écran utile en premier. Les noms canoniques viennent du document personas et sont repris dans `personaRoutes.ts` (`docs\personas\personas-and-journeys.md:44-53`, `docs\personas\personas-and-journeys.md:524-525`).

| Persona | Rôle simple | Section principale |
|---|---|---|
| Marc Weber — Plant Manager | Pilote la journée de l'usine et arbitre les priorités. | Command Center / Operations (`apps\analytics-mfe\src\personaRoutes.ts:18-33`) |
| Elena Duarte — Furnace Operator | Surveille les signaux du four pendant le poste. | Furnace Health (`apps\analytics-mfe\src\personaRoutes.ts:36-46`) |
| Tomás Rossi — Maintenance & Reliability Engineer | Planifie inspections et relinings selon le risque RUL. | Furnace Health (`apps\analytics-mfe\src\personaRoutes.ts:36-46`) |
| Sofia Lindqvist — Energy Manager | Examine prix spot et recommandations de déplacement de charge. | Energy Optimization (`apps\analytics-mfe\src\personaRoutes.ts:49-58`) |
| Jens Bakker — Quality Engineer | Protège qualité, généalogie et SPC. | Quality (`apps\analytics-mfe\src\personaRoutes.ts:61-70`) |
| Amina Haddad — Sustainability Officer | Suit émissions, EU ETS et preuves d'audit. | Sustainability & Compliance (`apps\analytics-mfe\src\personaRoutes.ts:73-83`) |
| Pieter Claes — Knowledge Engineer | Relit le savoir capturé et publie les procédures. | Knowledge Hub (`apps\analytics-mfe\src\personaRoutes.ts:86-95`) |
| Isabelle Moreau — Executive | Consulte les résultats portefeuille et le board report. | Executive Overview (`apps\analytics-mfe\src\personaRoutes.ts:98-107`) |
| Rui Almeida — OT Systems Engineer | Vérifie appareils simulés et flux capteurs. | Device Operations (`apps\analytics-mfe\src\personaRoutes.ts:110-121`) |
| Nils Andersen — Platform Ops | Gère capacité non-production, jobs et coûts. | Platform Ops (`apps\analytics-mfe\src\personaRoutes.ts:154-164`) |

Choisir un persona dans la liste déroulante de la barre supérieure fait deux choses : ouvrir l'écran d'accueil de ce persona et réduire le menu de gauche aux sections où ce persona travaille, en masquant tout intitulé de groupe devenu vide (`apps\portal-shell\Services\ShellState.cs`, `SectionsByPersona` / `VisibleNavigationItems`). Marc Weber — Plant Manager est le rôle de triage transverse et conserve donc le menu complet ; la section actuellement ouverte reste toujours listée, afin qu'un lien profond ne puisse jamais vous laisser sur une page sans entrée de menu.

## L'architecture en une image avec des mots

`Shell Blazor WebAssembly → microfrontend analytique React → BFF Python FastAPI → workers et fixtures déterministes → cible cloud Microsoft Fabric.`

Le shell Blazor possède le chrome global, le routage, l'identité, la langue, le thème et le panneau de capacité Fabric (`apps\portal-shell\README.md:1-6`). Le microfrontend React possède les tableaux de bord denses, cartes KPI, graphiques et tables virtualisées (`docs\ux\dashboard-specification.md:64-78`). Les API métier sont en Python/FastAPI (`docs\architecture\solution-architecture.md:92-101`). La démonstration utilise simulateur et replays déterministes, pas des systèmes de production (`docs\architecture\solution-architecture.md:32-38`). La cible cloud est Fabric : Eventstream, Eventhouse/KQL, OneLake/Lakehouse, modèle sémantique et Power BI (`docs\architecture\solution-architecture.md:72-86`).

Frontière d'honnêteté : la plateforme ne pilote jamais un four. Elle aide des décisions humaines et une répétition synthétique (`docs\architecture\solution-architecture.md:24-29`; `README.md:35-39`).

## Exécuter localement

Depuis la racine du dépôt. N'ajoutez pas de sources publiques Python ou NuGet. Le dépôt impose les feeds Microsoft protégés (`README.md:41-55`; `docs\tech\security_requirement.md:5-27`).

```powershell
npm run build:analytics
dotnet restore .\apps\portal-shell\PortalShell.csproj --configfile .\NuGet.Config --locked-mode
npm run build:portal
```

Ces commandes construisent le bundle React et le shell (`README.md:102-108`). Le README du shell précise que la bibliothèque React doit exister sous `wwwroot\analytics-mfe` avant de servir Blazor (`apps\portal-shell\README.md:45-47`).

Démarrer le BFF :

```powershell
npm run run:bff
```

Puis vérifier :

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health/ready
```

Ces commandes sont les commandes BFF locales de référence (`README.md:110-120`).

Démarrer le shell :

```powershell
dotnet run --project .\apps\portal-shell\PortalShell.csproj `
    --launch-profile http `
    --no-restore
```

Le README racine ouvre `http://localhost:5266/lu/command-center` ; toutes les routes de ce guide suivent la même grammaire `http://localhost:5266/{site}/{section}/{subView}`. Si vous démarrez la coque sans le profil de lancement `http`, .NET peut retomber sur `http://localhost:5000` — les chemins sont identiques, seul le port change, et la liste CORS par défaut du BFF autorise les deux (`README.md:122-134`; `apps\portal-shell\Properties\launchSettings.json:4-10`; `services\bff-api\src\bff_api\config.py:141-146`).

L'exemple uvicorn du simulateur d'appareils autonome est optionnel; par défaut, la démo web l'exécute dans le BFF (`README.md:201-216`).

## Comment lire ce guide

| Fichier | Ce qu'il explique |
|---|---|
| README / LISEZMOI | Index et parcours de lecture. |
| 00 Getting started | Bases acier, cas d'usage, personas, commandes locales. |
| 01 Shell & navigation | Chrome persistant, menus, routes et bridge. |
| 02 AxelorMetal public website | Site public fictif dans le portail. |
| 03 Command Center & Operations | Triage quotidien, statuts, alertes, actions. |
| 04 Furnace Health | RUL, signatures thermiques, maintenance. |
| 05 Energy Optimization | Prix spot, déplacement de charge, dispatch consultatif. |
| 06 Quality | Qualité batch, généalogie, défauts, SPC. |
| 07 Sustainability & Compliance | CO₂, EU ETS, preuve d'audit. |
| 08 Knowledge Hub | Recherche de procédures et gouvernance GenAI. |
| 09 Executive Overview | Cibles portefeuille et board report. |
| 10 Device Operations | Flotte simulée, capteurs, incident. |
| 11 Dashboard Collections | Parcours guidés entre écrans. |
| 12 Proof of Execution | IDs d'exigence, preuves et grille technique. |
| 13 Platform Ops | Capacité, jobs, coût plateforme. |
| 14 Cross-cutting features | Dock, Copilot, aide, paramètres, localisation, composants. |
| 15 Glossary | Définitions acier, industrie, plateforme et IA. |
| 16 Traceability matrix | Carte écran → cas d'usage → preuve. |
| 17 How it works behind the screens | Flux de données et mécanique d'implémentation. |
| 18 Guided demo walkthrough | Scénario de répétition pas à pas. |

---

▲ Index ([LISEZMOI.md](LISEZMOI.md)) · Next ▶ [01 · Shell & navigation](01-shell-and-navigation.md)

