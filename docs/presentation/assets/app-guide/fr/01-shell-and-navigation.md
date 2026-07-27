# 01 · Shell et navigation

**Public visé :** nouveaux utilisateurs NovaSteel qui doivent comprendre chaque contrôle persistant.  
**Temps de lecture :** ~17 minutes.  
**Related routes:** `/{site}/{section}/{subView}`, `/lu/command-center/overview`, `/lu/furnace-health/lining-forecast`, `/lu/platform-ops/capacity`.  
**Dernière mise à jour :** 2026-07-27  
**Langue :** 🇬🇧 [English version](../en/01-shell-and-navigation.md)

---

![Référence du chrome Command Center](../screenshots/command-center-overview.png)

La capture sert de carte. Le même shell entoure chaque écran : logo, barre supérieure, bandeau violet de données synthétiques, rail gauche, fil d'Ariane, contenu, boutons de dock, zone de toast et pied de page. Le shell appartient à Blazor; le tableau de bord intérieur appartient à React (`apps\portal-shell\README.md:1-6`; `docs\ux\dashboard-specification.md:64-78`).

## La grammaire des routes

Les routes suivent `/{site}/{section}/{subView}`. L'hôte Blazor déclare `/`, `/{Site}`, `/{Site}/{Section}` et `/{Site}/{Section}/{SubView}` (`apps\portal-shell\Pages\AnalyticsHost.razor:1-4`). Si le site manque, il redirige vers `/lu/command-center` (`apps\portal-shell\Pages\AnalyticsHost.razor:30-39`). Le constructeur de route émet `/{Site}/{section}` ou `/{Site}/{section}/{subView}` (`apps\portal-shell\Services\ShellState.cs:205-209`).

Exemples : `/lu/command-center/overview`, `/de/energy-optimization/spot-price-schedule`, `/be/quality/batches`, `/es/device-operations/fleet`.

## Pourquoi un shell Blazor héberge un microfrontend React

Le projet garde C# là où le brief le demandait : sign-in, routage, chrome, thème, langue et capacité. React/MUI sert aux écrans denses : cartes KPI, graphiques et tables virtualisées (`docs\ux\dashboard-specification.md:64-88`). L'architecture répète cette frontière : shell Blazor dans le navigateur, MFE React/TypeScript pour l'analytique, API Python FastAPI derrière (`docs\architecture\solution-architecture.md:44-50`, `docs\architecture\solution-architecture.md:109-117`).

## Contrat shell ↔ microfrontend

Le shell transmet un contexte typé défini par `contracts\ui\shell-interop.v1.schema.json` : `themeMode`, `locale`, `activePersona`, `site`, `demoMode`, `tokenRef` opaque, `bridgeVersion` et `navigation` (`contracts\ui\shell-interop.v1.schema.json:7-16`, `contracts\ui\shell-interop.v1.schema.json:18-81`). React est monté par `AnalyticsBridge`, qui appelle `mount` puis `update` si le contexte change (`apps\portal-shell\Components\AnalyticsBridge.razor:20-39`).

| Événement | Sens | Preuve |
|---|---|---|
| `nav.intent` | React demande à Blazor de naviguer. | `apps\portal-shell\Pages\AnalyticsHost.razor:47-53` |
| `capacity.request` | React demande au shell de médiatiser une action de capacité via le BFF. | `apps\portal-shell\Pages\AnalyticsHost.razor:54-66` |
| `capacity.panel` | React demande l'ouverture du panneau de capacité du shell. | `apps\portal-shell\Pages\AnalyticsHost.razor:68-73` |
| `toast` | React demande un message de statut. | `apps\portal-shell\Pages\AnalyticsHost.razor:74-79` |
| `telemetry` | React signale un événement de télémétrie accepté. | `apps\portal-shell\Pages\AnalyticsHost.razor:81-83` |

## Les composants du chrome

| Composant | Ce que c'est | Ce que vous voyez | Pourquoi il existe | Preuve |
|---|---|---|---|---|
| Marque / accueil | Lien logo NovaSteel en haut à gauche. | Logo et slogan; clic vers Command Center. | Point d'accueil stable, navigation shell hors MFE. | `apps\portal-shell\Layout\MainLayout.razor:10-15`; `apps\portal-shell\README.md:1-6`. |
| Sélecteur de site | Choix de l'usine. | `LU - Moselle Integrated Works`, plus LU/DE/BE/ES/ALL. | AxelorMetal couvre quatre pays. | `apps\portal-shell\Layout\MainLayout.razor:17-25`; `apps\portal-shell\Services\ShellState.cs:23-38`; `docs\usecase\usecase.md:7-10`. |
| Sélecteur de persona | Rôle principal. | `Marc Weber - Plant Manager` ; la liste affiche les personas de démonstration nommés, et non les seuls intitulés de rôle. | Un utilisateur peut avoir plusieurs personas ; le shell route vers la surface par défaut **et restreint la navigation de gauche aux sections que ce persona utilise réellement**. | `apps\portal-shell\Layout\MainLayout.razor:27-35` ; libellés et filtrage par persona dans `apps\portal-shell\Services\ShellState.cs` ; `docs\personas\personas-and-journeys.md:44-53`. |
| Recherche globale | Champ de recherche du shell. | Placeholder `Search…`. | Point d'entrée global; le toast conseille la recherche locale par vue. | `apps\portal-shell\Layout\MainLayout.razor:37-40`, `apps\portal-shell\Layout\MainLayout.razor:216-222`. |
| Pastille Fabric | État et accès au contrôle de capacité. | `Fabric: Paused` et `Simulated`. | Rend le coût/lifecycle Fabric non-production visible. | `apps\portal-shell\Layout\MainLayout.razor:44-53`; `apps\portal-shell\README.md:8-18`; `docs\ux\dashboard-specification.md:34-35`. |
| Cloche d'alertes | Raccourci vers les alertes. | Icône cloche avec badge rouge `3`. | Le triage critique reste accessible partout. | `apps\portal-shell\Layout\MainLayout.razor:55-57`, `apps\portal-shell\Layout\MainLayout.razor:225-228`; `apps\analytics-mfe\src\personaRoutes.ts:18-24`. |
| Bouton thème | Cycle light/dark/system. | Icône près du drapeau; le mode sombre change le chrome. | Accessibilité, confort et salles de présentation. | `apps\portal-shell\Layout\MainLayout.razor:59-62`, `apps\portal-shell\Layout\MainLayout.razor:230-243`; `apps\portal-shell\Components\SettingsDialog.razor:18-40`. |
| Liste des locales | Sélecteur langue/région. | Drapeau et `en-LU`; cinq locales. | Support LU, FR, DE, NL/BE et ES. | `apps\portal-shell\Layout\MainLayout.razor:64-65`; `apps\portal-shell\Services\ShellState.cs:37-38`; `apps\portal-shell\Components\LocaleListbox.razor:3-35`. |
| Toggle DEMO/CLOUD | Bouton de mode de données. | Badge violet `DEMO`. | Rend honnête le mode synthétique; le cloud peut rester synthétique. | `apps\portal-shell\Layout\MainLayout.razor:67-69`; `apps\portal-shell\Services\ShellState.cs:124-180`. |
| Menu compte | Identité de démonstration. | Avatar `SU`, utilisateur synthétique, rôles, `Sign out (demo)`. | Sépare identité shell et dashboards React. | `apps\portal-shell\Layout\MainLayout.razor:71-89`; `apps\portal-shell\Services\AuthDemoContext.cs:24-34`. |
| Menu hamburger | Menu principal compact. | `Settings`, `Reset workspace layout`, `About NovaSteel`. | Actions moins fréquentes sans surcharger la barre. | `apps\portal-shell\Layout\MainLayout.razor:91-115`, `apps\portal-shell\Layout\MainLayout.razor:245-287`. |
| Settings | Boîte de dialogue de préférences. | Appearance, Locale, Demo mode, BFF URL, aide bilingue. | Regroupe préférences et piège le focus. | `apps\portal-shell\Components\SettingsDialog.razor:5-75`, `apps\portal-shell\Components\SettingsDialog.razor:103-160`. |
| Bandeau synthétique | Avertissement violet. | `Synthetic demo data — not for operational control`. | Évite de confondre démonstration, prédiction et mesure. | `apps\portal-shell\Layout\MainLayout.razor:118-122`; `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:102-119`; `docs\architecture\solution-architecture.md:24-29`. |
| Rail gauche | Navigation permanente, restreinte au persona. | DAILY OPERATIONS, INSIGHT & GOVERNANCE, PLATFORM & REFERENCE. Les captures montrent le Plant Manager qui, en tant que rôle de triage transverse, conserve le menu complet de 14 entrées ; un Energy Manager n'en voit que 4 sous 2 en-têtes. Un en-tête dont tous les éléments sont filtrés disparaît avec eux, et la section ouverte reste toujours listée pour qu'un lien profond ne laisse jamais l'utilisateur sans repère. | Aide les débutants à trouver les surfaces de leur rôle sans parcourir des écrans qui appartiennent à quelqu'un d'autre, tout en préservant la navigation transverse pour le triage. | `apps\portal-shell\Layout\MainLayout.razor:125-145` ; groupes et filtrage par persona `apps\portal-shell\Services\ShellState.cs`. |
| Fil d'Ariane | Repère de localisation. | `LU / Command Center` ou `LU › Executive›overview`. | Donne contexte site/écran après un deep link. | `apps\portal-shell\Layout\MainLayout.razor:147-154`; `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:127-139`. |
| Toast | Message temporaire. | Message au-dessus du contenu. | Confirme les actions sans modal. | `apps\portal-shell\Layout\MainLayout.razor:155-158`; `apps\portal-shell\Services\ShellState.cs:193-197`. |
| Pied de page | Mode et note accessibilité. | `Demo mode · BFF http://localhost:8080` et `WCAG 2.2 AA target · synthetic evidence only`. | Rappelle source backend, cible WCAG et preuve synthétique. | `apps\portal-shell\Layout\MainLayout.razor:163-166`; `docs\ux\dashboard-specification.md:14-16`. |
| Boutons de dock | Contrôles de page MFE. | `Reset layout`, `What's this?`, `Copilot`, `Start guided demo`. | Même espace de travail, aide et démo partout. | `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:147-192`; `apps\analytics-mfe\src\components\dock\WorkspaceDock.tsx:266-277`. |

## Captures des menus et panneaux

![Menu compte](../screenshots/feature-account-menu.png)

La capture montre le menu avatar au-dessus du Command Center. Les rôles affichés sont des rôles de démonstration, pas la preuve d'un employé réel connecté (`apps\portal-shell\Layout\MainLayout.razor:75-87`; `apps\portal-shell\Services\AuthDemoContext.cs:24-34`).

![Settings](../screenshots/feature-settings-dialog.png)

La capture `Settings` montre les radios Appearance, la locale, `Demo mode`, l'URL BFF `http://localhost:8080` et l'option d'aide bilingue. Ces choix correspondent à `ThemeMode`, `Locale`, `DemoMode` et `HelpBilingual` (`apps\portal-shell\Services\ShellState.cs:64-83`, `apps\portal-shell\Components\SettingsDialog.razor:18-72`).

![Panneau Fabric capacity](../screenshots/feature-capacity-panel.png)

Le panneau de droite montre `Paused`, la capacité, le SKU `F2`, l'environnement `demo`, `Sweden Central`, `Live BFF`, le motif, le sélecteur SKU et `Request start` / `Request pause`. Il dit que les transitions simulées ne lancent aucune opération ARM (`apps\portal-shell\Components\CapacityPanel.razor:19-31`, `apps\portal-shell\Components\CapacityPanel.razor:38-73`).

![Mode sombre](../screenshots/feature-dark-theme.png)

La capture de thème sombre garde la même disposition mais change les jetons visuels. Le shell cycle system → light → dark → system, et React reçoit `themeMode` par le bridge (`apps\portal-shell\Layout\MainLayout.razor:230-243`; `contracts\ui\shell-interop.v1.schema.json:18-25`; `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:42-44`).

---

◀ Previous [00 · Bien démarrer](00-getting-started.md) · ▲ Index ([LISEZMOI.md](LISEZMOI.md)) · Next ▶ [02 · Site public AxelorMetal](02-company-website.md)

