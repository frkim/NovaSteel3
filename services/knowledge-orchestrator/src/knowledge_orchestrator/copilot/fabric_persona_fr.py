"""French answers served for the Copilot's per-persona predefined questions.

Every figure below is synthetic demo data: it is the value already shown on the
matching screen, emitted by the device simulator, or recorded in the verified
July-2026 gold scorecard. Keep prose and numbers in sync with the fixture pack --
the whole point of these answers is that an operator can check them against the
screens.

Formatting note: the Copilot panel renders paragraphs, ``**bold**`` and
``_italic_`` only. Do not use tables, headings or code spans.
"""

from __future__ import annotations

from typing import Final

ANSWERS: Final[dict[str, str]] = {
    # -- plant-manager -------------------------------------------------------
    "persona-plant-manager-q1": """**Il n'y a pas de KPI journalier unique au niveau ligne dans ce pack de démo.** Le proxy en direct le plus proche est **LUX-RHF-01**, la ligne de réchauffage qui s'écarte le plus du plan pendant la fenêtre de tension.

- Le débit du site est de **128.4 t/h** contre un objectif de **130 t/h**, avec un OEE de **84.1%** contre 85%
- Entre **17:00 et 20:00** le profil de réchauffage tombe à environ **114-122 t/h**
- Cette fenêtre coïncide avec le pic du soir à **€280/MWh**, donc le creux correspond à un décalage de charge délibéré plutôt qu'à un arrêt non planifié
- La qualité en aval reste à surveiller parce que **COIL-LUX-260725-017** porte un biais de bobinage de **+11.4 °C**

Si vous voulez la ligne la plus en retard d'un point de vue opérationnel, traitez d'abord la fenêtre du four de réchauffage. La conséquence est commerciale plutôt que catastrophique : vous échangez une courte baisse de débit contre une énergie moins chère et une exposition Scope 2 plus faible.""",
    "persona-plant-manager-q2": """**Le pack ne contient pas de registre de rendement étiqueté par équipe pour le poste de nuit.** L'élément le plus probant pointe vers une dérive qualité locale, pas vers une variation métallurgique à l'échelle de l'usine.

- Le lot actuellement en FAIL est **COIL-LUX-260725-017** sur **LUX-HSM-01**, avec un biais de bobinage de **+11.4 °C**
- La limite d'élasticité est de **452.4 MPa** contre une spécification de **380-520 MPa**, donc l'acier reste dans la plage, mais le résultat de laboratoire est **REVIEW**
- Le SPC place le sous-groupe **20** à **11.4**, au-dessus de la limite de contrôle supérieure de **8.5**
- Sur juillet 2026, on compte **86 défauts**, et les dérives de température de bobinage représentent **34 (39.5%)**, devant les fissures de bord 21 et les incrustations de surface 14

Commencez la matinée par la maîtrise du bobinage au laminoir à chaud, la discipline de libération sur la bobine DP780 et la confirmation que la dérive était assignable plutôt que systémique. C'est la cause la plus probable sur laquelle vous pouvez agir en premier.""",
    "persona-plant-manager-q3": """**Commencez par le creuset, puis le plan de charge, puis la dérive qualité DP780.** C'est l'ordre de triage le plus net ce matin.

- **1. Fourneau** - **ALERT-HEARTH-SECTOR-07-260725** est la seule alerte critique : risque **0.8995**, **P50 19.65 jours**, revêtement réfractaire **363 mm** contre un minimum de **300 mm**
- **2. Énergie** - **REC-DEMO-LUX-240725** attend toujours une approbation et vaut **€2,688.70** soit **7.25%**, avec une demande de pointe ramenée de **56.0 MW** à **51.58 MW**
- **3. Qualité** - **COIL-LUX-260725-017** porte un biais de bobinage de **+11.4 °C** et la rupture SPC du sous-groupe 20
- L'état du tableau est de **16 alertes ouvertes** : **1 critique, 8 avertissements, 7 informations, 2 acquittées**

Cet ordre protège d'abord la sécurité et la disponibilité, capte ensuite le plus grand levier maîtrisable de coût et de carbone d'aujourd'hui, puis traite le risque qualité le plus visible côté client.""",
    "persona-plant-manager-q4": """**84.1%** à cet instant, contre un objectif de **85%**.

- Le débit est de **128.4 t/h** contre **130 t/h**
- La livraison à l'heure est de **96.4%** contre 97%
- L'intensité énergétique est de **€312/t** contre **€300/t**
- Le frein de performance visible est concentré dans la fenêtre de tension **17:00-20:00**, où le réchauffage tourne à environ **114-122 t/h**

L'usine est donc proche de l'objectif OEE, sans l'atteindre. L'élément important est que l'écart est acheté de manière maîtrisée pour éviter une électricité à **€280/MWh**, et non parce que la ligne serait tombée dans un fonctionnement instable. La conséquence opérationnelle est de garder explicite l'arbitrage énergétique plutôt que de le traiter comme une perte de débit cachée.""",
    # -- furnace-operator ----------------------------------------------------
    "persona-furnace-operator-q1": """**Le profil du creuset BF-01 est asymétrique, pas uniformément chaud.** Le point à surveiller est **SECTOR-07**.

- **SECTOR-07** monte à **3.4 °C/h** depuis environ **652 °C**
- Les autres secteurs ne bougent qu'autour de **0.4 °C/h**, donc le problème est la divergence, pas un décalage de tout le creuset
- Le flux de chaleur local est de **118 kW/m²**
- Le refroidissement semble toujours nominal à **198 m³/h** avec un **ΔT d'eau de 9.4 °C**
- L'estimation du réfractaire passe de **372 mm** à **363 mm** sur 24 heures

Cette combinaison explique pourquoi le modèle pondère **heat_flux_6h_slope** à **29%**, **sector_to_ring_temp_delta** à **24%** et **cooling_efficiency_residual** à **18%**. La conséquence est que vous devez traiter cela comme un vrai signal d'usure localisée, pas comme une montée en température inoffensive de l'ensemble du fourneau.""",
    "persona-furnace-operator-q2": """**La démo ne comporte pas de capteur étiqueté T12-North.** L'élément en direct le plus proche est **TC-114** en dérive, avec l'enveloppe sur **SECTOR-07** qui s'écarte de ses voisines.

- **TC-114** dérive à **1.8 °C/h**
- **SECTOR-07** monte à **3.4 °C/h** depuis **652 °C**, tandis que les secteurs voisins restent près de **0.4 °C/h**
- Le flux de chaleur est déjà de **118 kW/m²**
- L'eau de refroidissement reste à **198 m³/h** avec **ΔT 9.4 °C**, donc une simple perte d'eau n'explique pas ce profil

L'explication la mieux étayée n'est donc pas « un capteur nord défaillant », mais un véritable changement thermique local qui apparaît aussi dans le score fondé sur la physique. La conséquence opérationnelle est de vérifier TC-114 par rapport aux thermocouples adjacents, tout en continuant à agir comme si le signal du creuset était réel tant que cette vérification ne l'a pas levé.""",
    "persona-furnace-operator-q3": """**Il n'y a pas de table en direct des paramètres de coulée dans cette plateforme.** L'élément gouverné le plus proche est **PROC-DEMO-0002**, plus le fait que l'anomalie d'aujourd'hui relève du comportement thermique du creuset plutôt que d'une fenêtre de chimie de coulée.

- **PROC-DEMO-0002** est la procédure approuvée : statut **APPROVED**, version **3**
- **PROC-DEMO-0001** est toujours **IN_REVIEW**, donc elle peut orienter les vérifications mais ne doit pas être traitée comme une autorité opératoire
- Le contexte actuel est thermique : flux de chaleur **118 kW/m²**, refroidissement **198 m³/h**, **ΔT 9.4 °C**, et secteur 07 en hausse à **3.4 °C/h**
- La chaîne de procédé reste haut-fourneau vers aciérie vers machine de coulée continue ; rien dans les éléments ne dit d'improviser la prochaine coulée

N'inventez donc pas un ajustement de coulée à partir de cet écran. La conséquence est procédurale : exécutez d'abord les étapes d'inspection et de confirmation approuvées, puis ne modifiez la pratique de coulée que si une instruction gouvernée du BOF ou de la machine de coulée continue vous le demande explicitement.""",
    "persona-furnace-operator-q4": """**La plateforme ne quantifie pas une courbe autonome taux de coke/usure.** Ce qu'elle montre, c'est qu'aujourd'hui le signal d'usure est dominé par la contrainte thermique.

- Le principal facteur du modèle est **heat_flux_6h_slope à 29%**
- Ensuite vient **sector_to_ring_temp_delta à 24%**
- Puis **cooling_efficiency_residual à 18%**
- L'état thermique en direct derrière cela est un flux de chaleur de **118 kW/m²**, un débit de refroidissement de **198 m³/h** et un **ΔT d'eau de 9.4 °C**
- L'estimation est déjà descendue à **363 mm** d'épaisseur de revêtement réfractaire contre un minimum sûr de **300 mm**

La réponse honnête est donc que le taux de coke peut compter comme covariable, mais que le score actuel n'est pas piloté par une élasticité taux de coke clairement démontrée. La conséquence opérationnelle est de maîtriser ce qui est directement étayé maintenant - charge thermique, déséquilibre entre secteurs et efficacité du refroidissement - plutôt que de courir après une explication uniquement liée au coke, non étayée.""",
    # -- maintenance-engineer ------------------------------------------------
    "persona-maintenance-engineer-q1": """**LUX-BF-01 / HEARTH-SECTOR-07** est de loin le risque principal cette semaine.

- Score de risque **0.8995** avec **P50 19.65 jours**, **P10 18.69**, **P90 20.61**
- Épaisseur estimée **363 mm** contre un minimum de **300 mm**
- La dégradation progresse à environ **3.0 mm/jour**
- L'actif nommé suivant dans le pack, **LUX-RHF-01**, n'est qu'à environ **34%** de risque avec environ **120 jours** restants
- L'ordre de travail **WO-DEMO-LUX-1042** existe déjà pour une inspection planifiée

Il n'y a pas de second risque proche dans le même niveau d'urgence. La conséquence est de verrouiller d'abord la fenêtre d'inspection et de réfection autour de BF-01 ; tout le reste relève de la surveillance, pas d'une intervention cette semaine.""",
    "persona-maintenance-engineer-q2": """**Parce que l'image thermique en direct est plus marquée que lors des épisodes d'alerte historiques.** Le modèle voit un signal de détérioration locale plus rapide, pas simplement la répétition de l'ancienne trajectoire moyenne.

- L'estimation du réfractaire passe de **372 mm** à **363 mm** sur 24 heures
- **SECTOR-07** monte à **3.4 °C/h** tandis que les secteurs voisins restent près de **0.4 °C/h**
- Le score reste ancré par la même pile de facteurs : **29%** pente du flux de chaleur, **24%** delta secteur-à-anneau, **18%** résidu d'efficacité du refroidissement
- Le refroidissement reste nominal à **198 m³/h** et **ΔT 9.4 °C**, ce qui rend la divergence sectorielle plus difficile à écarter comme simple bruit d'instrumentation

Historiquement, les épisodes d'alerte de juillet prouvent que le système peut tenir une réfection planifiée avec **21.0 jours** d'avance. La chute d'aujourd'hui à **P50 19.65 jours** signifie que la signature d'usure actuelle est déjà à l'intérieur de cette marge de confort. La conséquence est de resserrer la cadence de planification et d'inspection, pas d'attendre que l'historique la lisse.""",
    "persona-maintenance-engineer-q3": """**Planifiez dès maintenant la séquence d'inspection de BF-01, et maintenez la fenêtre de réfection entre les jours 18 et 24.** C'est le plan gouverné étayé par les éléments actuels.

- **WO-DEMO-LUX-1042** est l'objet de maintenance en direct
- Jours d'inspection **1-4** : confirmer les thermocouples, les températures d'entrée et de sortie du refroidissement, et l'historique local
- Jours **5-8** pour l'ultrason et la confirmation d'épaisseur
- Fenêtre de réfection planifiée **jours 18-24**
- Chiffres d'ancrage : risque **0.8995**, **P50 19.65 jours** et revêtement réfractaire **363 mm** contre un minimum de **300 mm**

Utilisez **PROC-DEMO-0002** comme procédure opératoire approuvée ; **PROC-DEMO-0001** est toujours en revue et doit rester consultative. La conséquence est que vous avez encore le temps d'en faire un arrêt planifié, mais seulement si la séquence d'inspection démarre immédiatement.""",
    "persona-maintenance-engineer-q4": """**P50 est de 19.65 jours ; P90 est de 20.61 jours.** Ce ne sont pas deux futurs différents, mais deux points de confiance différents sur la même distribution prédite de durée de vie restante.

- **P10 18.69 jours** - une borne basse prudente
- **P50 19.65 jours** - l'estimation médiane, la valeur que la plupart des gens utilisent pour la planification au quotidien
- **P90 20.61 jours** - une borne haute optimiste avec plus de durée de vie restante que la médiane
- L'écart est serré : seulement **0.96 jours** entre P50 et P90

Face à un objectif de programme de **21 jours** d'alerte anticipée, les trois chiffres racontent la même histoire : vous êtes déjà, de fait, dans la fenêtre d'action. La conséquence opérationnelle est de planifier avec P50, de tester la robustesse avec P10 et de n'utiliser P90 que pour comprendre le potentiel favorable - pas pour justifier l'attente.""",
    # -- energy-manager ------------------------------------------------------
    "persona-energy-manager-q1": """**02:00-05:00** est la prochaine fenêtre bas carbone présente dans la démo, aidée par le bloc PPA éolien de **12 MWh**.

- La fenêtre chère et plus carbonée est **17:00-20:00**, avec des prix montant jusqu'à **€280/MWh**
- La recommandation de plan de charge déplace le réchauffage flexible hors de cette période de tension
- Un déplacement visible est **REHEAT-BATCH-06** du créneau **75** à **18:45** vers le créneau **67** à **16:45**
- L'impact à la journée est une base de **€37,109.10** vers un optimisé de **€34,420.40**, soit **€2,688.70** ou **7.25%** d'économies

La prochaine fenêtre propre n'est donc pas seulement une électricité moins chère ; c'est la partie de la journée où le planning peut absorber de la charge sans payer la prime carbone du pic du soir. La conséquence est d'avancer ou de repousser le chauffage et la fusion flexibles, et non de les laisser dans la bande 17:00-20:00.""",
    "persona-energy-manager-q2": """**Parce que le tonnage a baissé alors que la charge fixe n'a pas bougé.** Le pic d'intensité énergétique du dernier poste s'explique au mieux par le décalage délibéré de charge de réchauffage à travers la fenêtre de tension.

- L'intensité énergétique est de **€312/t** contre un objectif de **€300/t**
- Le débit est de **128.4 t/h** contre **130 t/h**, mais dans la fenêtre **17:00-20:00** il tombe à environ **114-122 t/h**
- C'est exactement là que le prix spot culmine à **€280/MWh**
- Le plan de charge maintient le tonnage total inchangé à **960 t**, donc le planning achète un soulagement de coût et de carbone au prix d'une brève baisse de cadence

Autrement dit, le pic est un effet arithmétique d'une production instantanée plus faible face à une charge d'usine largement fixe, et non la preuve que l'usine serait soudain devenue intrinsèquement inefficace. La conséquence opérationnelle est de juger le €/t avec l'objectif du plan de charge, et non de l'isoler.""",
    "persona-energy-manager-q3": """**REC-DEMO-LUX-240725** est la plus grande économie visible du pack, et le mouvement clé est le lot de réchauffage qui quitte le créneau de 18:45.

- Base **€37,109.10** vers optimisé **€34,420.40** - économie de **€2,688.70** soit **7.25%**
- La demande de pointe passe de **56.0 MW** à **51.58 MW**
- **REHEAT-BATCH-06** passe du créneau **75** à **18:45** et **€280/MWh** au créneau **67** à **16:45** et **€97.24/MWh**
- Ce seul déplacement réduit le coût du lot de **€3,920.00** à **€1,361.36**
- En juillet 2026, **100 sur 116** recommandations ont été acceptées, adoption **0.862** contre un objectif de 0.70

Les opportunités de plus forte valeur sont donc les charges thermiques flexibles qui touchent encore la bande de tension. La conséquence est d'approuver rapidement le plan de charge et de continuer à chercher des déplacements de réchauffage ou de fusion en fenêtre du soir selon le même schéma.""",
    "persona-energy-manager-q4": """**La plateforme ne propose pas sur cette carte de scénario hypothétique heures creuses spécifique à l'EAF.** L'élément mesuré le plus proche est le plan de charge déjà modélisé sur la charge thermique flexible.

- Ce plan de charge réduit le CO₂ de **3.29%** à tonnage inchangé
- Le cas d'optimisation sur le plan complet dans le résumé de durabilité est de **8.7%**
- Le carbone du réseau est en moyenne d'environ **244 gCO₂/kWh**, donc déplacer la charge vers des heures plus propres réduit le Scope 2 sans changer la production d'acier
- Le même plan de charge réduit aussi la demande de pointe de **56.0 MW** à **51.58 MW**

Je ne citerais donc pas un chiffre séparé sur les coulées EAF que le pack ne démontre pas. Ce que la plateforme démontre, c'est le mécanisme : le déplacement vers les heures creuses réduit directement les émissions d'électricité achetée. La conséquence opérationnelle est de traiter le décalage de charge comme un vrai levier Scope 2, même lorsque le débit et le tonnage restent stables.""",
    # -- quality-engineer ----------------------------------------------------
    "persona-quality-engineer-q1": """**COIL-LUX-260725-017** est le seul **FAIL** actuel sur le tableau Luxembourg en direct, et c'est celui à traiter en premier.

- Nuance **NS-AUTO-DP780**
- Score de risque **0.429**
- Biais de température de bobinage **+11.4 °C**, l'écart visible le plus important
- Limite d'élasticité mesurée **452.4 MPa** contre une spécification de **380-520 MPa**
- Statut laboratoire **REVIEW**, et l'alerte qualité reste acquittée mais ouverte

La plateforme n'expose pas sur cet écran une liste FAIL distincte multi-bobines « surface uniquement », donc c'est la réponse la plus fidèle à un appel de défaut qualité. La conséquence opérationnelle est de mettre cette bobine en quarantaine ou en revue avant libération, puis de remonter la dérive via le réchauffage et le bobinage plutôt que de supposer un problème général de laboratoire.""",
    "persona-quality-engineer-q2": """**Il n'y a pas d'actif nommé Line 3 dans le modèle de démo.** L'élément réel le plus proche côté ligne est **LUX-HSM-01**, et la dérive est portée par la température de bobinage plutôt que par un changement global du mix produit.

- Juillet 2026 enregistre **86 défauts** dans le périmètre
- **34 défauts (39.5%)** sont des dérives de température de bobinage, devant les fissures de bord **21**, les incrustations de surface **14**, l'écart d'épaisseur **9**, le revêtement **5** et autres **3**
- Le point actuel de cause spéciale est le sous-groupe **20** à **11.4**, au-dessus de la **8.5** limite de contrôle supérieure
- La bobine affectée est **COIL-LUX-260725-017** avec un biais de **+11.4 °C** sur **LUX-HSM-01**

La tendance ne se lit donc pas au mieux comme « Line 3 se dégrade » ; il vaut mieux y voir un mode de défaillance dominant sur la route du laminoir à chaud. La conséquence opérationnelle est de stabiliser d'abord le contrôle du bobinage, parce que c'est là que pointent à la fois la rupture en direct et le mix mensuel des défauts.""",
    "persona-quality-engineer-q3": """**La plateforme n'évalue pas la ségrégation axiale comme KPI à part entière.** L'élément réel le plus proche se trouve dans les entrées de la machine de coulée continue et dans la généalogie derrière la bobine affectée.

- Les variables en direct de la machine de coulée continue disponibles pour ce type de triage sont **superheat**, **casting_speed** et **secondary_cooling_flow** sur **LUX-CC-01**
- La généalogie est complète : **LOT-FE-017 → H-LUX-260725-0040 → LADLE-017 → SLAB-017 → REHEAT-017 → COIL-LUX-260725-017 → SMP-017 → SHIP-DEMO-017**
- La limite d'élasticité mesurée de la bobine est de **452.4 MPa**, toujours dans la plage **380-520 MPa**, avec un statut laboratoire **REVIEW**

J'utiliserais donc le trio de la machine de coulée continue comme ensemble de corrélation, tout en gardant la généalogie ouverte à travers le réchauffage et le bobinage. La conséquence opérationnelle est d'enquêter sur un risque de type ségrégation comme sur un problème de route couvrant la pratique thermique de la machine de coulée continue et le réchauffage en aval, pas comme sur un chiffre de laboratoire isolé apparu de nulle part.""",
    "persona-quality-engineer-q4": """**Le SPC sur cet écran ne porte pas directement sur l'épaisseur ; il porte sur le biais de température de bobinage.** Ce qu'il vous dit reste néanmoins important sur le plan opérationnel.

- Moyenne **1.9**, sigma **2.2**, limite de contrôle supérieure **8.5**, limite de contrôle inférieure **-4.7**
- Le sous-groupe **20** est à **11.4**, donc hors contrôle côté haut
- La capabilité du procédé est de **Cpk 1.18** contre un objectif de **1.33**
- La même valeur **11.4** correspond au biais de bobinage sur **COIL-LUX-260725-017**

Le SPC vous dit donc qu'il y a une cause spéciale récente dans le traitement thermique, pas que tout le centre de procédé aurait dérivé progressivement. La conséquence est d'enquêter d'abord sur la cause assignable de température de bobinage ; ce n'est qu'ensuite que vous devriez déduire quoi que ce soit sur la performance d'épaisseur à partir de la même marche de production.""",
    # -- sustainability-officer ---------------------------------------------
    "persona-sustainability-officer-q1": """**Dans l'ensemble oui, mais le trimestre n'est plus confortable.** L'utilisation des quotas est déjà de **71%**, et la marge n'est plus que de **6.2%**.

- Le prix actuel du quota est de **€86/t**
- L'exposition prévisionnelle est d'environ **€248,000** au point de fonctionnement actuel
- L'intensité actuelle de la configuration est de **1.42 tCO₂e/t** contre un objectif de **1.35**
- L'alerte du registre en direct pour cela est l'alerte ouverte **ALERT-ETS-ALLOWANCE-Q3**
- La clôture de juillet 2026 reste solide à **1.019 tCO₂e/t** contre un objectif de **1.638** et une base de **2.10**

Le programme est donc dans les clous sur le tableau de bord historique, mais le coussin du trimestre en cours est faible. La conséquence opérationnelle est de continuer à utiliser dès maintenant le décalage de charge et les autres leviers de court terme, parce que quelques mauvaises journées d'exploitation brûleraient rapidement les 6.2% de marge restants.""",
    "persona-sustainability-officer-q2": """**La plateforme ne porte pas de colonne d'exposition spécifique au CBAM.** Le proxy prouvé le plus proche est l'exposition ETS, plus l'intensité Scope 1 actuelle.

- La charge Scope 1 d'aujourd'hui est de **1,368 t CO₂e/jour** pour **960 t** d'acier, soit environ **1,425 kg/t**
- Une hausse franche de production de **10%** à intensité inchangée ajouterait environ **136.8 t CO₂e/jour**
- L'utilisation des quotas est déjà de **71%**, avec une exposition prévisionnelle de **€248,000** et une marge de **6.2%**
- L'intensité opérationnelle actuelle est de **1.42 tCO₂e/t** contre un objectif de **1.35**

Je n'affirmerais donc pas un montant de facture CBAM que le pack de données ne contient pas. Ce que les éléments disent, c'est qu'une hausse de tonnage de 10% augmenterait sensiblement l'exposition au carbone tarifé, à moins que l'intensité ne s'améliore en même temps. La conséquence opérationnelle est d'associer toute hausse de production à une action d'efficacité ou de plan de charge, et non de laisser les tonnes monter sur un profil d'émissions inchangé.""",
    "persona-sustainability-officer-q3": """**1.42 tCO₂e/t** sur la configuration opérationnelle actuelle.

- C'est la valeur en direct du jour, pas la moyenne mensuelle en clôture
- Elle se situe au-dessus de l'objectif de **1.35** pour le mode de fonctionnement actuel
- Pour le dernier mois clôturé, juillet 2026, la valeur plateforme était de **1.019 tCO₂e/t**
- Ce résultat de juillet dépassait largement l'objectif de **1.638** et la base de **2.10**
- La répartition Scope pour juillet est de **355,336 t** en Scope 1 et **147,868 t** en Scope 2

Votre intensité actuelle est donc plus mauvaise que la clôture mensuelle gold, même si la tendance du programme reste en avance sur l'objectif. La conséquence opérationnelle est de lire la valeur 1.42 comme un signal de correction en direct - surtout autour de la charge thermique et du timing électrique - et non comme une raison de douter du registre de fin de mois.""",
    "persona-sustainability-officer-q4": """**Par rapport à la référence, le programme est en avance sur le mois et en retard sur la journée en direct.** Les deux sont vrais en même temps.

- Configuration actuelle : **1.42 tCO₂e/t** contre un objectif de **1.35**, donc environ **0.07 tCO₂e/t** au-dessus
- Juillet 2026 en clôture : **1.019 tCO₂e/t** contre un objectif de **1.638** et une base de **2.10**
- Contexte du trimestre actuel : utilisation des quotas **71%**, marge **6.2%**, exposition prévisionnelle **€248,000** à **€86/t**
- Le plan de charge reste le levier le plus rapide, en réduisant le CO₂ de **3.29%** sur le planning démontré

Par rapport à la référence, le système gagne donc dans le registre historique mais est sous pression dans la fenêtre opérationnelle actuelle. La conséquence opérationnelle est de continuer à présenter les deux chiffres ensemble : le score mensuel prouve que le programme fonctionne, tandis que la valeur en direct dit qu'aujourd'hui exige encore une intervention active.""",
    # -- knowledge-engineer --------------------------------------------------
    "persona-knowledge-engineer-q1": """**Le pack de données ne stocke pas la fréquence de consultation du glossaire par terme.** L'élément réel le plus proche est la demande et la couverture par domaine de connaissances.

- Couverture haut-fourneau **82%**
- Laboratoire qualité **77%**
- Laminoir à chaud **71%**
- Four de réchauffage **64%**
- Énergie et utilités **58%**
- Les statuts de procédure sont répartis entre **PROC-DEMO-0001 IN_REVIEW v2**, **PROC-DEMO-0002 APPROVED v3** et **PROC-DEMO-0003 DRAFT v1**

Je ne peux donc pas nommer honnêtement le terme de glossaire le plus consulté à partir de ce pack. Ce que je peux dire, c'est que les domaines à la couverture la plus faible sont les points de pression de consultation les plus probables, en particulier l'énergie et le réchauffage. La conséquence opérationnelle est d'améliorer d'abord la capture et l'approbation à ces endroits, parce que c'est là que les questions non étayées risquent le plus de s'accumuler.""",
    "persona-knowledge-engineer-q2": """**Il cite les sources qui sont à la fois pertinentes et gouvernables, pas simplement n'importe quel texte récupéré.** Sur cette plateforme, la chaîne de preuves est délibérément auditable.

- Le registre de décisions montre **AUD-0001** à **AUD-0005**, et les cinq ont **complete_audit_flag true**
- Les procédures ne se valent pas : **PROC-DEMO-0002** est **APPROVED v3**, tandis que **PROC-DEMO-0001** est **IN_REVIEW v2** et **PROC-DEMO-0003** est **DRAFT v1**
- Pour les questions persona prédéfinies, le Copilot utilise des cartes Fabric fixes, donc les jeux de données cités sont déterministes plutôt qu'improvisés

Le système préfère donc les connaissances approuvées et les chaînes d'audit complètes à un texte simplement disponible. La conséquence opérationnelle est qu'une source non approuvée à l'apparence utile doit quand même rester hors de la réponse finale si elle ne peut pas satisfaire au même niveau de gouvernance que les éléments approuvés ou audités.""",
    "persona-knowledge-engineer-q3": """**L'architecture d'ancrage est en couches et délibérément étroite.** L'élément réel le plus proche est la combinaison de procédures gouvernées, de faits Fabric et du chemin d'ontologie qui relie les actifs à travers la route de procédé.

- Couche texte gouvernée : **PROC-DEMO-0002 APPROVED v3**, avec **PROC-DEMO-0001 IN_REVIEW v2** et **PROC-DEMO-0003 DRAFT v1** encore hors du même niveau de confiance
- Couche analytique : faits gold Fabric pour l'historique des KPI et vues chaudes KQL pour l'état en direct
- Couche structurelle : l'ontologie peut tracer des chemins tels que **LUX-BF-01** en aval à travers la chaîne de fabrication de l'acier jusqu'à **LUX-HSM-01**
- Couche décision : **AUD-0001..AUD-0005**, tous avec **complete_audit_flag true**

La plateforme fonde donc les réponses sur un petit nombre de routes de récupération explicites, plutôt que sur une synthèse libre. La conséquence opérationnelle est la prévisibilité : vous pouvez inspecter quel niveau de données, quel statut de procédure ou quel chemin de graphe a étayé la réponse, au lieu de faire confiance à un résumé boîte noire.""",
    "persona-knowledge-engineer-q4": """**La plateforme n'expose pas de table Fabric dédiée de « score d'injection de prompt ».** L'élément opérationnel le plus proche est qu'elle impose déjà un ancrage limité aux sources approuvées, des enregistrements d'audit complets et une relecture humaine avant toute action.

- Les cinq lignes d'audit **AUD-0001** à **AUD-0005** sont complètes
- Seule **PROC-DEMO-0002** est approuvée pour un usage opérationnel direct ; **PROC-DEMO-0001** et **PROC-DEMO-0003** restent sous ce seuil
- Les recommandations telles que **REC-DEMO-LUX-240725** restent en attente d'une approbation humaine plutôt que d'être engagées automatiquement

Les véritables garde-fous que vous pouvez prouver à partir des données sont donc des frontières de gouvernance, de la traçabilité et un contrôle humain dans la boucle. La conséquence opérationnelle est importante : même si un texte non fiable était récupéré, il lui manquerait encore une voie directe pour approuver un planning, modifier une action de contrôle ou effacer la piste d'audit.""",
    # -- ot-systems-engineer -------------------------------------------------
    "persona-ot-systems-engineer-q1": """**Aucun n'est significativement en retard ou manquant actuellement.** Le parc en direct est sain selon les mesures que la plateforme porte réellement.

- **17 équipements** et **91 signaux** sont en ligne
- La fraîcheur des signaux est inférieure à **5 s** pour les flux rapides en direct
- La fraîcheur de bout en bout est d'environ **12 s**
- Les incidents actifs sont à **0**
- Le seuil d'alerte de quarantaine est de **2% par 15 minutes**, et rien n'indique ici que ce seuil ait été dépassé

Il faut simplement se rappeler que tous les signaux ne sont pas censés se mettre à jour au même rythme : **hearth_refractory_estimate** est un signal à **900,000 ms** par conception, pas un flux 5-secondes en retard. La conséquence opérationnelle est que vous n'avez pas besoin de faire du triage de flux maintenant ; vous devez préserver ce chemin sain tout en traitant séparément les alertes de procédé.""",
    "persona-ot-systems-engineer-q2": """**5,000 ms** pour les signaux rapides du creuset, avec une fraîcheur globale de plateforme d'environ **12 s** de bout en bout.

- **hearth_shell_temperature** publie toutes les **5,000 ms**
- **local_heat_flux** publie toutes les **5,000 ms**
- **hearth_refractory_estimate** est volontairement plus lent à **900,000 ms**
- Le parc reste globalement sain : **17 équipements**, **91 signaux**, **0 incidents**
- **TC-114** en dérive à **1.8 °C/h** est un problème de signal thermique, pas une preuve de latence réseau

Le réseau de capteurs du fourneau n'est donc pas le goulot d'étranglement. La conséquence opérationnelle est de séparer la latence du chemin de données du comportement de procédé : les flux à 5 secondes arrivent à l'heure, donc la tendance anormale du creuset doit être traitée comme une condition d'usine, pas comme un artefact de transport.""",
    "persona-ot-systems-engineer-q3": """**La plateforme ne fournit pas d'assistant intégré de provisionnement des tags PLC.** L'objet faisant autorité le plus proche est le contrat d'événement de télémétrie que la passerelle doit publier.

- L'enveloppe porte **source_id**, **asset_id**, **plant_id**, **sequence**, **schema_name** et **schema_version**
- Le nom du schéma de télémétrie est **novasteel.telemetry.v1**
- Un bon source id ressemble à **LUX-BF-01-TC-H07-03**, de sorte que l'identité de l'actif et du signal reste explicite à travers la passerelle
- Les tags rapides doivent s'aligner sur la bonne cadence, par exemple **5,000 ms** pour la température d'enveloppe du creuset, tandis que les estimations plus lentes peuvent tourner à **900,000 ms**
- Les payloads mal formés sont censés atterrir en quarantaine plutôt que de glisser en silver sans être vus

Configurer ici un nouveau tag PLC signifie donc le mapper proprement dans l'enveloppe publiée et le registre des signaux, pas modifier une table analytique cachée. La conséquence opérationnelle est que la conformité au contrat compte autant que le tag lui-même, parce qu'une mauvaise forme sera rejetée volontairement.""",
    "persona-ot-systems-engineer-q4": """**Le protocole filaire n'est pas stocké dans Fabric.** Ce que la plateforme prouve, c'est le schéma médié par la passerelle qui se trouve au-dessus.

- Le parc en direct montre **17 équipements** et **91 signaux** avec **0 incidents**
- Les événements arrivent dans des enveloppes versionnées avec des source ids tels que **LUX-BF-01-TC-H07-03**
- La santé se mesure par l'état de connexion de la passerelle, la fraîcheur et le comportement de file, pas par une colonne de protocole
- La fraîcheur de bout en bout est d'environ **12 s**, et les signaux thermiques rapides publient toujours toutes les **5,000 ms**

Je ne prétendrais donc pas que la couche analytique peut vous dire si la matrice thermique est en Modbus, Profinet ou autre chose. La réponse la plus fidèle est que le protocole est abstrait derrière le schéma de passerelle d'usine, et que les éléments dont vous disposez ici montrent que le pont est assez sain pour livrer la télémétrie du fourneau à l'heure. La conséquence opérationnelle est d'aller chercher les détails de protocole dans le registre OT, pas dans les faits Fabric.""",
}


