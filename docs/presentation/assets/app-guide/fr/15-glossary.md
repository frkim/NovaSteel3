# 15 · Glossaire

**Public visé :** débutants qui veulent des définitions simples des termes acier, industrie, plateforme et IA.  
**Temps de lecture :** ~19 minutes.  
**Related routes:** toutes les routes; surtout `/lu/furnace-health/lining-forecast`, `/lu/energy-optimization/spot-price-schedule`, `/lu/quality/batches`, `/lu/sustainability-compliance/emissions-ledger`.  
**Dernière mise à jour :** 2026-07-27  
**Langue :** 🇬🇧 [English version](../en/15-glossary.md)

---

Les noms d’écrans ci-dessous viennent des routes personas et de la matrice de preuve (`apps\analytics-mfe\src\personaRoutes.ts:16-182`; `docs\presentation\proof_of_execution.md:439-447`). Toutes les données restent synthétiques et consultatives (`apps\portal-shell\Layout\MainLayout.razor:118-122`; `docs\architecture\solution-architecture.md:22-29`).

## A. Termes acier et industrie

| Terme anglais | Terme français | Définition simple | Où vous le rencontrez dans NovaSteel |
|---|---|---|---|
| BOF / converter | Convertisseur BOF | Four à oxygène basique : cuve où l’on souffle de l’oxygène dans la fonte liquide pour réduire le carbone et produire de l’acier. | Quality; AxelorMetal Steel Knowledge |
| Blast furnace | Haut fourneau | Grand four où le coke et l’air chaud transforment le minerai de fer en fonte liquide. C’est là que commencent une grande partie de la chaleur, de l’énergie et du risque d’usure du revêtement. | Furnace Health; AxelorMetal public website |
| CMMS | GMAO / CMMS | Logiciel de gestion de maintenance : actifs, tâches et ordres de travail. NovaSteel ne simule que le lien vers un ordre de travail. | Furnace Health › Maintenance Planner |
| Campaign | Campagne | Période d’exploitation entre deux grands rebuilds ou remplacements de revêtement. Une campagne plus longue signifie plus de production avant un arrêt coûteux. | Furnace Health › Maintenance Planner |
| Carbon intensity | Intensité carbone | CO₂ émis par unité produite, souvent par tonne d’acier ou par MWh. Plus elle est basse, mieux c’est pour l’EU ETS et le suivi durable. | Sustainability › Emissions Ledger |
| Coil | Bobine | Longue bande d’acier laminée puis enroulée. Les bobines sont courantes pour l’automobile et l’industrie. | Quality › Batch Quality |
| Control chart | Carte de contrôle | Graphique de maîtrise statistique qui montre si un procédé reste stable ou dérive. | Quality › Defect Analytics (SPC) |
| Cp / Cpk | Cp / Cpk | Indices de capabilité : statistiques simples qui indiquent si un procédé tient dans les limites de spécification et s’il est bien centré. | Quality › Defect Analytics (SPC) |
| Day-ahead market | Marché day-ahead | Marché de l’électricité où les prix du lendemain sont fixés la veille, souvent heure par heure. | Energy Optimization › Spot & Schedule |
| Demand response | Effacement / réponse à la demande | Adaptation de la consommation électrique à un signal de prix ou de réseau. Dans NovaSteel, c’est consultatif, jamais un contrôle automatique. | Energy Optimization › Load-Shift Simulator |
| EU ETS | SEQE-UE / EU ETS | Système européen d’échange de quotas d’émission : les entreprises doivent disposer de quotas pour leurs émissions de CO₂. | Sustainability › ETS Exposure |
| Genealogy | Généalogie matière | Traçage du heat jusqu’à la brame, la bobine et le résultat qualité. Cela aide à retrouver l’origine d’un défaut. | Quality › Batch Quality |
| Hearth | Creuset | Partie basse du haut fourneau où s’accumule la fonte liquide. Son état thermique compte pour la santé du revêtement. | Furnace Health › Thermal Explorer |
| Heat / batch | Coulée / lot | Un heat est une coulée de métal liquide traitée ensemble; un batch regroupe des enregistrements de production comme une unité. | Quality › Batch Quality |
| Hot metal | Fonte liquide | Fonte liquide issue du haut fourneau avant conversion finale en acier. | Operations; AxelorMetal Steel Knowledge |
| Industrial DMZ | DMZ industrielle | Zone réseau protégée entre OT et IT/cloud. Elle réduit le risque d’accès direct du cloud vers l’usine. | Device Operations; Architecture guide |
| Load shifting | Déplacement de charge | Déplacer un travail énergivore flexible hors des heures chères ou très carbonées. NovaSteel le propose à approbation humaine. | Energy Optimization › Spot & Schedule |
| MTBF | MTBF | Temps moyen entre pannes : durée moyenne de fonctionnement d’un actif avant une panne. | Device Operations › Device Fleet |
| MWh | MWh | Mégawattheure : unité d’énergie. Un MWh correspond à un mégawatt consommé pendant une heure. | Command Center; Energy Optimization |
| OT / IT | OT / IT | L’OT exploite les équipements industriels; l’IT exploite les systèmes métier et cloud. NovaSteel sépare l’analytique consultative du contrôle. | Device Operations; Platform Ops |
| PLC | Automate programmable / PLC | Ordinateur industriel qui commande des équipements. NovaSteel n’écrit pas dans les PLC. | Device Operations |
| Pareto | Pareto | Classement montrant les quelques causes responsables de la majorité des défauts ou pertes. | Quality › Defect Analytics (SPC) |
| RUL | Durée de vie résiduelle (RUL) | Durée estimée avant qu’un actif atteigne un seuil de panne ou d’intervention. | Furnace Health › Lining Forecast |
| Refractory lining | Revêtement réfractaire | Paroi interne résistante à la chaleur d’un four. Son usure augmente le risque de défaillance et motive l’alerte à 21 jours. | Furnace Health › Lining Forecast |
| SCADA | SCADA | Systèmes de supervision utilisés pour surveiller et contrôler les équipements. NovaSteel reste hors de cette boucle de contrôle. | Device Operations |
| SPC | MSP / SPC | Maîtrise statistique des procédés : utilisation de statistiques pour détecter une dérive avant l’augmentation des défauts. | Quality › Defect Analytics (SPC) |
| Scope 1 / 2 / 3 | Scopes 1 / 2 / 3 | Catégories d’émissions : directes, liées à l’énergie achetée et liées à la chaîne de valeur. | Sustainability › Emissions Ledger |
| Scrap / rework | Rebut / reprise | Matière rejetée ou nécessitant un retraitement. Moins de rebut/reprise signifie meilleur rendement et coût plus bas. | Quality › Batch Quality |
| Spot price | Prix spot | Prix de marché courant de l’électricité, souvent variable heure par heure. | Energy Optimization › Spot & Schedule |
| Taphole | Trou de coulée | Ouverture permettant de vidanger la fonte liquide d’un haut fourneau. | Furnace Health › Thermal Explorer |
| Thermal signature | Signature thermique | Profil de températures, flux thermique et refroidissement qui peut indiquer l’état du revêtement. | Furnace Health › Thermal Explorer |
| Tuyère | Tuyère | Buse qui souffle de l’air chaud dans le haut fourneau. Les problèmes autour des tuyères influencent les profils thermiques. | Furnace Health › Thermal Explorer |
| Work order | Ordre de travail | Enregistrement d’une tâche de maintenance : quoi inspecter, quand et par qui. NovaSteel crée seulement des exemples synthétiques. | Furnace Health › Maintenance Planner |
| Yield | Rendement | Part de la production qui devient produit conforme plutôt que rebut ou reprise. | Quality; Executive Overview |
| t CO₂e | t CO₂e | Tonnes équivalent CO₂ : unité standard pour comparer les gaz à effet de serre. | Sustainability › Emissions Ledger |

## B. Termes plateforme et tech

| Terme anglais | Terme français | Définition simple | Où vous le rencontrez dans NovaSteel |
|---|---|---|---|
| Audit hash-chain | Chaîne de hachage d’audit | Modèle d’audit append-only où chaque enregistrement référence le hash précédent, rendant une altération visible. | Proof of Execution; Sustainability › Audit & Reports |
| Azure AI Foundry | Azure AI Foundry | Plateforme Microsoft pour construire et gouverner des applications et agents IA. En démo, des adaptateurs locaux déterministes peuvent remplacer les appels live. | Knowledge Hub; Proof of Execution |
| BFF | BFF | Backend for Frontend : couche API adaptée au navigateur, pour éviter que l’UI appelle directement tous les backends. | Portal shell; Platform Ops |
| Blazor WebAssembly | Blazor WebAssembly | Runtime front-end C# utilisé pour le shell NovaSteel : routage, chrome, thème, langue et panneau de capacité. | Every route / shell |
| Deterministic seed | Graine déterministe | Valeur de départ fixe qui rend les données synthétiques répétables. Les mêmes entrées produisent la même histoire de démo. | Device Operations; guided demo |
| Direct Lake | Direct Lake | Mode Power BI lisant efficacement les données Fabric Lakehouse sans importer toutes les lignes ailleurs. | Architecture; Executive Overview |
| Dockview | Dockview | Bibliothèque React de panneaux dockables utilisée pour les panneaux déplaçables et redimensionnables. | Every dashboard screen |
| EU AI Act | Règlement européen sur l’IA | Règlement européen centré sur le risque IA, la transparence, la supervision humaine et la gouvernance. | Proof of Execution; Sustainability › Audit & Reports |
| Eventhouse / KQL | Eventhouse / KQL | Magasin analytique temps réel de Fabric, interrogé avec le langage Kusto Query Language. | Architecture; Device Operations |
| Eventstream | Eventstream | Composant Fabric d’ingestion d’événements en streaming. | Architecture; Device Operations |
| GDPR | RGPD | Règlement européen sur les données personnelles. La démo NovaSteel utilise des données synthétiques/non personnelles. | Proof of Execution; Sustainability › Audit & Reports |
| Grounding | Ancrage | Lien entre une réponse IA et des faits approuvés, le contexte écran ou des documents, pour éviter une réponse flottante. | Copilot; Knowledge Hub |
| Idempotency key | Clé d’idempotence | Clé unique permettant au serveur de traiter des requêtes répétées comme la même action. | Platform Ops › Capacity |
| LLM | Grand modèle de langage (LLM) | Grand modèle de langage : IA qui génère ou résume du texte à partir d’un prompt et d’un contexte. | Copilot; Knowledge Hub |
| Lakehouse | Lakehouse | Stockage combinant lac de données fichiers et tables proches d’un entrepôt. | Architecture; Sustainability |
| MILP / PuLP / CBC | MILP / PuLP / CBC | Optimisation linéaire en nombres entiers mixtes et outils Python/solveurs utilisés pour les recommandations de planning. | Energy Optimization |
| Managed identity | Identité managée | Identité cloud affectée à une charge de travail pour s’authentifier sans secret stocké. | Architecture; Platform Ops |
| Medallion bronze / silver / gold | Médaillon bronze / silver / gold | Couches de qualité des données : brut/atterrissage, nettoyé/conformé, puis faits prêts métier. | Architecture; Proof of Execution |
| Microfrontend | Microfrontend | Application front-end embarquée dans un autre shell front-end. NovaSteel utilise React dans un shell Blazor. | Every dashboard screen |
| Microsoft Fabric | Microsoft Fabric | Plateforme analytique Microsoft pour streaming, lakehouse, KQL, modèles sémantiques et Power BI. | Platform Ops; Architecture |
| OLS regression | Régression OLS | Régression des moindres carrés ordinaires : méthode simple pour ajuster une ligne et estimer une relation. | Furnace Health › Lining Forecast |
| OneLake | OneLake | Couche de stockage lac unifiée de Fabric. | Architecture |
| Power BI | Power BI | Outil Microsoft de rapports et dashboards; l’architecture cible peut exposer des rapports gouvernés. | Executive Overview; Architecture |
| RAG | RAG | Retrieval-Augmented Generation : rechercher des faits pertinents avant de demander à un LLM de répondre. | Copilot; Knowledge Hub |
| Semantic model | Modèle sémantique | Modèle métier de tables, mesures, relations et sécurité utilisé par les rapports. | Executive Overview; Sustainability |
| Synthetic data | Données synthétiques | Données artificielles créées pour la démo et les tests, pas des données d’usine ou personnelles réelles. | Every screen |
| WCAG 2.2 AA | WCAG 2.2 AA | Objectif d’accessibilité pour clavier, lecteur d’écran, contraste, focus et signaux non uniquement colorés. | Shell footer; all screens |

---

◀ Previous [14 · Fonctionnalités transverses](14-cross-cutting-features.md) · ▲ Index ([LISEZMOI.md](LISEZMOI.md)) · Next ▶ [16 · Matrice de traçabilité](16-traceability-matrix.md)

