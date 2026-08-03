"""French answers served for the Copilot's predefined questions.

Translated from ``fabric_answers_en``: numbers, identifiers, table names and
model versions are byte-identical to the English pack; only the prose differs.

Formatting note: the Copilot panel renders paragraphs, ``**bold**`` and
``_italic_`` only. Do not use tables, headings or code spans.
"""

from __future__ import annotations

from typing import Final

ANSWERS: Final[dict[str, str]] = {
    # -- command-center ----------------------------------------------------
    "command-center-q1": """**ALERT-HEARTH-SECTOR-07-260725** est l'alerte à traiter en priorité : c'est la seule alerte CRITICAL ouverte, et la seule associée à une réfection.

- Équipement **LUX-BF-01**, composant **HEARTH-SECTOR-07**, site NS-DEMO-LUX-01
- Durée de vie résiduelle **P50 19.65 jours**, score de risque **0.90**, confiance du modèle 0.78
- Déclenchée à **17:58**, toujours OPEN

Seize alertes sont ouvertes sur les quatre sites : **1 critique, 8 avertissements, 7 informations, 2 acquittées**. Tout le reste est au niveau avertissement ou inférieur - la pointe de prix du soir à €280/MWh, la dérive de bobinage DP780 sur COIL-LUX-260725-017, et la marge ETS Q3 à 6.2%.

L'ordre de travail **WO-DEMO-LUX-1042** est déjà rédigé pour le creuset, la décision en attente porte donc sur la fenêtre d'inspection, pas sur le diagnostic.""",
    "command-center-q2": """Quatre prochaines meilleures actions sont en file d'attente, une par domaine.

- **Haut-fourneau** - planifier l'inspection du creuset de BF-01. Risque 0.90, durée de vie résiduelle P50 19.65 jours, ordre de travail WO-DEMO-LUX-1042 déclenché à 18:00.
- **Énergie** - approuver le décalage de charge 17:00-20:00. Le tableau affiche une économie modélisée d'environ €4.2k ; le plan de charge validé REC-DEMO-LUX-240725 aboutit à **€2,688.70 (7.25%)** avec la puissance de pointe réduite de 56.0 à 51.58 MW.
- **Qualité** - examiner la dérive NS-AUTO-DP780 sur COIL-LUX-260725-017 : biais de bobinage **+11.4 °C**, risque 0.429, statut FAIL.
- **ETS** - la marge de quota Q3 est tombée à **6.2%**, avec 71% des quotas utilisés à €86/t.

L'impact le plus élevé approuvable aujourd'hui est le plan de charge. L'impact le plus élevé évitable est la défaillance du creuset, que le cas d'usage valorise à €8M par événement non planifié.""",
    "command-center-q3": """L'équipe A (06:00-14:00, A. Weber) passe la main à l'équipe B à **13:45**. Depuis la passation de poste précédente :

- **Escaladé** - l'alerte creuset est passée en CRITICAL à 17:58, risque 0.90, durée de vie résiduelle P50 19.65 jours
- **Nouveau** - avertissement de tension énergétique du soir à 15:12 (€280/MWh, 18:30-19:00) et avertissement de marge ETS Q3 à 08:45
- **Acquitté mais toujours ouvert** - dérive de bobinage DP780 (04:00) et dérive du thermocouple TC-114 (21:10)
- **Créé** - ordre de travail WO-DEMO-LUX-1042 à 18:00 ; le plan de charge REC-DEMO-LUX-240725 reste PENDING_APPROVAL
- **Décisions enregistrées** - 5 entrées d'audit, AUD-0001 à AUD-0005, couvrant les domaines haut-fourneau, énergie, qualité, connaissances et capacité

Aucune alerte n'a été clôturée durant le poste, le nombre d'alertes ouvertes reste donc inchangé à **16 alertes**.""",
    "command-center-q4": """**REC-DEMO-LUX-240725**, le plan de charge énergétique, est la recommandation avec l'impact approuvable le plus élevé.

- Coût €37,109.10 de base à **€34,420.40** optimisé - une économie de **€2,688.70 (7.25%)** sur la journée
- Puissance de pointe 56.0 MW à **51.58 MW**, en baisse de 7.89%
- CO₂ en baisse de **3.29%** à tonnage inchangé (960 t)
- **0 violation de contrainte dure** ; statut PENDING_APPROVAL, modèle energy-dispatch-deterministic:2.1.0

À titre de contexte, sur juillet 2026 la flotte a accepté **100 des 116** recommandations - adoption 0.862 contre un objectif de 0.70 - pour **11,431 t** de CO₂ évité attendu et zéro violation de contrainte.

L'inspection du fourneau représente une valeur encore plus élevée, mais ce n'est pas une recommandation à approuver : elle protège contre le cas de défaillance non planifiée à €8M via une fenêtre de maintenance.""",
    # -- operations --------------------------------------------------------
    "operations-q1": """Légèrement en dessous de l'objectif. Le débit est de **128.4 t/h** contre un objectif de **130 t/h** - 1.6 t/h en dessous, bien que **+3.2%** par rapport à la période précédente.

- OEE **84.1%** contre 85%
- Livraison à l'heure **96.4%** contre 97%
- Intensité énergétique **€312/t** contre €300/t, en amélioration de 4.1%

Le profil de débit présente une chute d'environ **6 t/h entre 17:00 et 20:00**. Cette chute est délibérée : il s'agit d'une charge de réchauffage déplacée hors de la fenêtre de tension à €280/MWh. En dehors de ces trois heures, la ligne tourne à l'objectif ou au-dessus.""",
    "operations-q2": """**LUX-RHF-01**, le four de réchauffage, durant la fenêtre 17:00-20:00.

- Le débit passe d'environ 130 t/h à **114-122 t/h** sur ces trois heures
- REHEAT-BATCH-06 (NS-AUTO-HSLA420, 120 t) a été avancé de 18:45 à **16:45** pour éviter le créneau à €280/MWh
- En aval, LUX-HSM-01 porte la dérive de bobinage DP780 sur COIL-LUX-260725-017

Sur les autres sites : le stand F4 du BE-HSM-01 tourne **5.8% au-dessus sur la force de laminage**, et le brûleur zone 02 de ES-RHF-01 est **4% riche en air/carburant**, représentant environ 180 kWh/h de perte évitable.

La généalogie de la ligne est LUX-BF-01 vers LUX-BOF-01 vers LUX-CC-01 vers LUX-RHF-01 vers LUX-HSM-01, donc l'arrêt de réchauffage est ce que le laminoir perçoit comme des heures perdues - pas une défaillance du laminoir.""",
    "operations-q3": """**Passation de poste - Équipe A (06:00-14:00, A. Weber) vers Équipe B (14:00-22:00, M. Dupont). Passation à 13:45 ; l'Équipe C prend le relais à 22:00.**

Production : débit **128.4 t/h** contre 130, OEE **84.1%** contre 85%, livraison à l'heure **96.4%** contre 97%, intensité énergétique **€312/t** contre 300.

Incidents ouverts - 16 alertes : 1 critique, 8 avertissements, 7 informations, 2 acquittées.
- CRITICAL ALERT-HEARTH-SECTOR-07-260725 - LUX-BF-01, durée de vie résiduelle P50 19.65 jours, risque 0.90
- WARNING ALERT-ENERGY-SCARCITY-1830 - €280/MWh entre 18:30 et 19:00
- WARNING ALERT-QUALITY-DRIFT-DP780 - COIL-LUX-260725-017, acquitté à 04:00
- WARNING ALERT-ETS-ALLOWANCE-Q3 - marge de quota 6.2%

Actions et décisions en cours :
- WO-DEMO-LUX-1042, inspection planifiée sur HEARTH-SECTOR-07, créé à 18:00
- Plan de charge REC-DEMO-LUX-240725 toujours PENDING_APPROVAL - €2,688.70, 7.25%
- 5 enregistrements de décision AUD-0001 à AUD-0005, tous avec traçabilité complète""",
    "operations-q4": """La prédiction de creuset sur **LUX-BF-01** doit être remontée en priorité.

- ALERT-HEARTH-SECTOR-07-260725, CRITICAL, ouverte depuis 17:58
- Durée de vie résiduelle **P50 19.65 jours** (P10 18.69 / P90 20.61), risque **0.90**
- Revêtement réfractaire à **363 mm** contre un minimum sûr de 300 mm, s'amincissant d'environ **3.0 mm/jour**
- Une fenêtre de réfection est nécessaire dans **18-24 jours**, ce qui est une décision de plan de production plutôt que de maintenance

En deuxième position figure la marge ETS Q3 à **6.2%** - une exposition commerciale à €86/t plutôt qu'opérationnelle. Tout le reste sur le tableau relève du triage habituel du poste.""",
    # -- furnace-health ----------------------------------------------------
    "furnace-health-q1": """La signature thermique correspond au profil que forment cinq secteurs du creuset quand on les observe ensemble plutôt qu'un à un.

- SECTOR-05, -06, -08 et -09 dérivent à **0.4 °C/h** depuis 640-664 °C
- **SECTOR-07 monte à 3.4 °C/h** depuis 652 °C et dépasse le seuil d'anomalie de **700 °C** vers l'heure 14 ; les cellules à 720 °C ou au-dessus sont signalées critiques
- Le refroidissement semble normal - delta T de **9.4 °C** à **198 m³/h** - ce qui est précisément ce qui rend la divergence du secteur significative plutôt qu'une défaillance du refroidissement
- Flux de chaleur **118 kW/m²**, proxy thermique de l'eau de refroidissement **214.7 kW**, résistance thermique apparente **8.73**
- L'estimation du revêtement réfractaire sur le secteur passe de **372.0 mm à 363 mm** sur la fenêtre de 24 heures

Le modèle **lining-rul-piml/1.3.0-demo** convertit cela en durée de vie résiduelle, en pondérant heat_flux_6h_slope à 29%, sector_to_ring_temp_delta à 24% et cooling_efficiency_residual à 18%.""",
    "furnace-health-q2": """**ÉLEVÉ - score de risque 0.8995 (90%)** sur le composant HEARTH-SECTOR-07.

- Durée de vie résiduelle **P50 19.65 jours**, P10 18.69, P90 20.61 - une plage serrée
- Épaisseur du revêtement réfractaire **363 mm** contre un minimum estimé à **300 mm**, se dégradant d'environ 3.0 mm/jour
- Modèle lining-rul-piml/1.3.0-demo, scoré à 18:45 aujourd'hui
- La deuxième unité, **LUX-RHF-01**, présente un risque de 34% avec environ 120 jours restants - WATCH, pas d'action

L'objectif du programme (KPI-FUR-01) est d'au moins **21 jours** d'avance. Dans l'historique de juillet 2026, chaque épisode d'alerte s'est déclenché exactement à **21.0 jours** - BE-EAF-01 le 2026-06-19 pour une date de défaillance au 2026-07-10, LUX-RHF-01 le 2026-06-09 pour le 2026-06-30 - et unplanned_outage_flag était **false sur chaque ligne**.""",
    "furnace-health-q3": """Trois facteurs portent 71% du score.

- **heat_flux_6h_slope - 29%.** Flux de chaleur local à 118 kW/m² avec une pente horaire sur six heures croissante : la chaleur atteint l'enveloppe plus rapidement que ne le permettrait un revêtement réfractaire intact.
- **sector_to_ring_temp_delta - 24%.** SECTOR-07 monte à 3.4 °C/h tandis que ses voisins dérivent à 0.4 °C/h. La divergence, pas la température absolue, est le signal.
- **cooling_efficiency_residual - 18%.** Le delta T de refroidissement de 9.4 °C à 198 m³/h évacue moins de chaleur que ne le laisse supposer le débit, de sorte que la résistance thermique apparente est tombée à 8.73.

Les 29% restants sont répartis entre des facteurs plus lents. L'épaisseur lit actuellement **363 mm** contre un minimum de 300 mm, et à environ 3.0 mm/jour, c'est ce qui fixe le P50 à **19.65 jours**.""",
    "furnace-health-q4": """**WO-DEMO-LUX-1042 - inspection planifiée, HEARTH-SECTOR-07, LUX-BF-01.**

Justification : le modèle de revêtement réfractaire à base de physique (lining-rul-piml/1.3.0-demo) évalue le secteur 07 à **risque 0.8995** avec **durée de vie résiduelle P50 19.65 jours** (P10 18.69 / P90 20.61). L'épaisseur estimée est de **363 mm** contre un minimum sûr de **300 mm** et diminue d'environ **3.0 mm/jour**. Les facteurs déterminants sont une pente croissante du flux de chaleur sur six heures (29%), un delta de température secteur-à-anneau de 3.4 °C/h contre 0.4 °C/h sur les secteurs voisins (24%), et un résidu d'efficacité de refroidissement (18%). Le débit de refroidissement est nominal à 198 m³/h avec un delta T de 9.4 °C, une défaillance du refroidissement n'explique donc pas le signal.

Périmètre : vérifier les thermocouples de l'enveloppe par rapport aux secteurs voisins, enregistrer le delta T d'entrée et de sortie du refroidissement avec l'historique récent des débits, et confirmer l'estimation d'épaisseur avant l'ouverture de la fenêtre de réfection. **PROC-DEMO-0002** (inspection du circuit de refroidissement et escalade par ultrasons, approuvée v3) s'applique ; **PROC-DEMO-0001** (vérification de surchauffe du secteur du creuset) est toujours en relecture.

Calendrier : inspection jours 1-4, ultrasons jours 5-8, fenêtre de réfection **jours 18-24**. Agir dans cette fenêtre est ce qui maintient cet événement comme planifié - dans l'historique de juillet 2026, chaque épisode d'alerte s'est terminé par une réfection planifiée avec unplanned_outage_flag false.""",
    # -- energy-optimization -----------------------------------------------
    "energy-optimization-q1": """**REC-DEMO-LUX-240725** - déplacer le réchauffage flexible hors de la fenêtre de tension du soir.

- Base **€37,109.10** vers optimisé **€34,420.40**, une économie de **€2,688.70 (7.25%)**
- Puissance de pointe **56.0 MW à 51.58 MW**, en baisse de 7.89% ; charge déplaçable 18 MW
- Le déplacement rentable : REHEAT-BATCH-06 hors du créneau 75 (18:45, **€280.00/MWh**, €3,920.00) vers le créneau 67 (16:45, €97.24/MWh, **€1,361.36**)
- Tonnage inchangé à **960 t** sur 8 lots de 120 t / 14 MWh sur LUX-RHF-01
- **0 violation de contrainte dure** ; statut PENDING_APPROVAL, modèle energy-dispatch-deterministic:2.1.0

REHEAT-BATCH-03 reste fixé à 09:45 car il est signalé urgent. Deux lots sont avancés de 15-30 minutes, et les lots 00 et 07 passent en créneaux nocturnes moins chers.""",
    "energy-optimization-q2": """Parce qu'un créneau coûte plus que la majeure partie du reste de la journée à lui seul.

- La courbe prix J-1 culmine à **€280.00/MWh à 18:45**, contre 54.85-€112.64/MWh partout ailleurs
- Réchauffer un seul lot de 120 t / 14 MWh dans ce créneau coûte **€3,920.00** ; le même lot à 16:45 (€97.24/MWh) coûte **€1,361.36** - une différence de €2,558.64 pour un seul lot
- La fenêtre de tension court de **17:00 à 20:00**, ce qui correspond également à la chute de 6 t/h dans le profil de débit des opérations
- Un surplus PPA éolien de **12 MWh** est prévu de 02:00 à 05:00, raison pour laquelle le lot 07 passe à 23:30 et le lot 00 à 02:15

Le coût total des lots flexibles passe de €12,369.70 à €9,681.00. La charge fixe de l'installation de €24,739.40 est au même prix dans les deux plannings, l'économie totale de **€2,688.70** provient donc entièrement des huit lots de réchauffage.""",
    "energy-optimization-q3": """Les cinq contraintes indiquent toutes SATISFIED, avec **0 violation dure**.

- **equal_planned_tonnage** - 960.00 t planifiés, 960.00 t planifiés. L'optimiseur peut déplacer l'acier, jamais le supprimer.
- **urgent_batch_fixed** - REHEAT-BATCH-03 (NS-AUTO-HSLA420, urgent) reste dans le créneau 39 à 09:45, non déplacé.
- **minimum_soak_time** - 60 minutes de temps de maintien préservées sur chaque lot.
- **maximum_hold_time** - aucun lot retenu au-delà de la limite de 120 minutes ; le déplacement le plus important est le lot 06 à -120 minutes.
- **equipment_capacity** - au plus 2 lots simultanés sur LUX-RHF-01.

C'est ce qui rend le résultat approuvable : l'économie de **€2,688.70** est obtenue entièrement dans l'ensemble des contraintes, et la recommandation est versionnée (v1) et auditable sous **AUD-0002**.""",
    "energy-optimization-q4": """**En baisse de 3.29%** sur ce plan de charge - obtenu en déplaçant la charge vers des créneaux moins carbonés, pas en produisant moins.

- L'intensité carbone du réseau est en moyenne d'environ **244 gCO₂/kWh** sur les 96 créneaux quart-horaires, oscillant approximativement entre 140 et 310
- Le tonnage est inchangé à **960 t**, la réduction est donc du pur arbitrage carbone
- La puissance de pointe baisse également de **56.0 à 51.58 MW**, là où se situe habituellement le carbone des heures de tension
- La réduction modélisée du plan de charge complet dans le bilan de durabilité est de **8.7%**

À l'échelle de la flotte en juillet 2026, les **100 recommandations acceptées** (sur 116, adoption 0.862 contre un objectif de 0.70) représentent **11,431 t** de CO₂ évité attendu.""",
    # -- quality -----------------------------------------------------------
    "quality-q1": """**COIL-LUX-260725-017**, nuance NS-AUTO-DP780 - le seul lot actuellement en FAIL.

- Score de risque **0.429**, caractéristique YIELD_STRENGTH
- Biais de température de bobinage **+11.4 °C**, le plus élevé du tableau ; le suivant est +3.0 °C
- Limite d'élasticité mesurée **452.4 MPa** contre une spécification de 380-520 MPa - dans les spécifications, mais le résultat de laboratoire est en REVIEW
- Coulée source H-LUX-260725-0040, laminoir LUX-HSM-01
- ALERT-QUALITY-DRIFT-DP780 a été acquitté à 04:00 et est toujours ouvert

Sur les 20 lots au tableau, c'est celui qu'un client automobile verrait. La dérive a été signalée avant le premier résultat de laboratoire hors spécification, ce qui est précisément l'intérêt du signal.""",
    "quality-q2": """Un seul point est hors contrôle, et c'est le plus récent.

- Moyenne **1.9**, sigma **2.2**, donc LSC **8.5** et LCI **-4.7**
- Le sous-groupe 20 donne **11.4** - au-dessus de la limite de contrôle supérieure, et le même biais de **+11.4 °C** de température de bobinage que porte COIL-LUX-260725-017
- Les sous-groupes 1-19 restent dans les limites, avec un pic à 5.8. Il n'y a aucune série, tendance ou dérive vers les limites avant ce point
- Capabilité du procédé **Cpk 1.18** contre un objectif de **1.33** - capable, mais sans marge confortable

Sur 30 jours, on recense **86 défauts**, dont les dérives de température de bobinage représentent **34 (39.5%)**, devant les fissures de bord (21), les incrustations de surface (14), les écarts d'épaisseur (9), la porosité de revêtement (5) et autres (3). Un seul point de cause spéciale sur la famille de défauts dominante pointe vers une cause assignable, pas vers un recentrage du procédé.""",
    "quality-q3": """La chaîne derrière COIL-LUX-260725-017 est intacte de bout en bout, ce qui permet de localiser l'écart.

- Lot de matière première LOT-FE-017 vers coulée **H-LUX-260725-0040** vers traitement en poche LADLE-017 vers brame SLAB-017
- Réchauffage à **LUX-RHF-01** (REHEAT-017) vers bobine COIL-LUX-260725-017 vers échantillon SMP-017 vers essai YIELD_STRENGTH **452.4 MPa** (REVIEW) vers expédition SHIP-DEMO-017
- Équivalent carbone 0.420 en tête de séquence, augmentant de 0.002 par lot

L'étape qui a bougé est le réchauffage : ce four retenait des lots hors de la fenêtre de tension 17:00-20:00, et le biais de bobinage est ressorti à **+11.4 °C**. L'écart se rattache donc aux étapes de réchauffage et de bobinage, pas à la fusion - rien en amont de la poche ne montre de signal correspondant.""",
    "quality-q4": """Température de bobinage **-8 °C** avec force de laminage **-3%** - le scénario hypothétique encadré que cet écran exécute déjà.

- Le rendement au premier passage prédit passe d'environ **88% à environ 95%**, contre des bornes de scénario inférieures à 0.90 avant et au moins 0.93 après
- Modèle **quality-yield-gbm/2.1.0-demo** ; l'exécution est enregistrée sous l'audit **AUD-0003**
- Elle reste dans les spécifications : la limite d'élasticité de 452.4 MPa se situe en milieu de plage dans la fenêtre 380-520 MPa, donc la suppression du biais de +11.4 °C ne menace pas la limite basse
- Au tableau aujourd'hui, le rendement haute qualité est de 94.8% contre un objectif de 95% et le rendement au premier passage de 97.1% contre 97%

Par rapport aux KPI du programme, le rendement haute qualité au premier passage de juillet 2026 était de **0.9494** contre l'objectif de **0.972**, depuis une base de 0.90 - le seul résultat encore en déficit, d'environ 2.3 points. Les pertes ce mois-là ont été de 4,498 t déclassées, 8,996 t réusinées et 1,499 t mises au rebut sur 464 défauts.""",
    # -- sustainability-compliance -----------------------------------------
    "sustainability-compliance-q1": """**71% des quotas utilisés**, avec la marge Q3 tombée à **6.2%**.

- Prix du quota **€86.00/t**
- Exposition prévisionnelle de la période **€248,000** à l'intensité d'émission actuelle
- Le Scope 1 tourne à **1,368 t CO₂e/jour** pour 960 t d'acier ; le Scope 2 suit le réseau, avec une moyenne d'environ 244 gCO₂/kWh sur les 96 intervalles
- CO₂ par tonne d'acier **1.42 t/t** contre un objectif de **1.35**
- ALERT-ETS-ALLOWANCE-Q3 est ouverte dans le registre

Pour le dernier mois avec les comptes clôturés, juillet 2026 : intensité CO₂ **1.019 tCO₂e/t** contre un objectif de 1.638 et une base de 2.10, donc KPI-CO₂-01 est atteint - avec Scope 1 **355,336 t**, Scope 2 **147,868 t** et exposition ETS totale de **€3,974,153**.""",
    "sustainability-compliance-q2": """**Au mois 5**, sur la trajectoire actuelle.

- La consommation est à **71%** et la projection ajoute environ **3.1 points par mois**
- Le mois 4 arrive à 83.4% - toujours sous le seuil de guidance de **85%**
- Le mois 5 arrive à **86.5%**, ce qui est le dépassement
- Le plafond à 100% n'est pas atteint avant environ le mois 10, le dépassement du seuil de guidance arrive donc d'abord, d'environ cinq mois
- La marge Q3 est déjà tombée à **6.2%**, ce que ALERT-ETS-ALLOWANCE-Q3 suit

L'acceptation du plan de charge actuel déplace la courbe : **-3.29%** de CO₂ sur ce planning, et une réduction modélisée de **8.7%** si l'optimisation du plan de charge s'étend sur l'ensemble du plan.""",
    "sustainability-compliance-q3": """Les deux figurent dans le même registre append-only, mais ils répondent à des questions différentes.

- **Scope 1 - direct.** Émissions de combustion et de procédé sur site : **1,368 t CO₂e** pour 960 t d'acier aujourd'hui, soit effectivement 1,425 kg par tonne. Il évolue quand le procédé change, et il est insensible à l'état du réseau.
- **Scope 2 - indirect, électricité achetée.** Calculé par quart-heure : consommation sur l'intervalle multipliée par l'intensité carbone du réseau sur ce même intervalle - environ **244 gCO₂/kWh** en moyenne, oscillant approximativement entre 40 et 480 sur la journée. Il évolue quand on déplace la charge dans le temps, même à tonnage identique.

C'est pourquoi la recommandation du plan de charge réduit le CO₂ de **3.29%** sans produire moins d'acier : elle touche uniquement le Scope 2. Le registre contient **96 lignes d'intervalles immuables**, et l'exposition ETS est dérivée de leur somme à €86/t.

En juillet 2026, la répartition était Scope 1 **355,336 t** et Scope 2 **147,868 t**.""",
    "sustainability-compliance-q4": """Approuver le plan de charge - c'est le seul levier qui agit aujourd'hui.

- **REC-DEMO-LUX-240725** - CO₂ **-3.29%** immédiatement, à tonnage inchangé (960 t), 0 violation de contrainte dure, toujours PENDING_APPROVAL
- L'exécution de l'optimisation du plan de charge sur l'ensemble du plan est modélisée à **8.7%**
- Levier suivant le plus rapide : le brûleur zone 02 de ES-RHF-01 est **4% riche en air/carburant**, représentant environ 180 kWh/h de perte évitable
- Le plus lent mais le plus important : la voie de procédé Scope 1 elle-même, qu'aucun changement de planning n'atteint

À **€86/t** et avec une marge à 6.2%, le plan de charge est ce qui empêche le dépassement du seuil de guidance d'arriver avant le mois 5. En juillet 2026, les 100 recommandations acceptées ont apporté **11,431 t** de CO₂ évité attendu.""",
    # -- knowledge-hub -----------------------------------------------------
    "knowledge-hub-q1": """**PROC-DEMO-0002 - inspection du circuit de refroidissement et escalade par ultrasons.** Statut APPROVED, version 3, capturée dans la session SESS-DEMO-015 et citée vers transcript:SESS-DEMO-015#seg-2. C'est la seule procédure approuvée de la bibliothèque, et c'est celle qui s'applique à l'alerte de creuset ouverte.

Plus proche voisin, pas encore utilisable : **PROC-DEMO-0001 - vérification de surchauffe du secteur du creuset**, version 2, IN_REVIEW, citée vers transcript:SESS-DEMO-014#seg-4 et #seg-7. Elle indique de comparer les thermocouples de l'enveloppe des secteurs voisins avant d'agir, de lire le delta T d'entrée et de sortie du refroidissement avec l'historique récent des débits plutôt que le débit seul, et de ne jamais contourner les alarmes ni modifier les réglages sur la foi d'une guidance d'entretien.

Les réponses fondées sont tirées exclusivement des procédures approuvées, donc PROC-DEMO-0001 peut être lue mais ne sera pas citée comme réponse tant qu'un expert ne l'aura pas validée.""",
    "knowledge-hub-q2": """**L'énergie et les utilités est le domaine lacunaire - 58% de couverture**, le plus bas des cinq domaines.

- Haut-fourneau **82%**
- Laboratoire qualité **77%**
- Laminoir à chaud **71%**
- Four de réchauffage **64%**
- Énergie et utilités **58%**

Trois procédures capturées ont dépassé le SLA de relecture de 5 jours (ALERT-KNOWLEDGE-REVIEW-QUEUE), et seulement une des trois procédures de la bibliothèque est approuvée - la couverture utilisable est donc inférieure à la couverture capturée dans chaque domaine.

Le manque se fait sentir le plus là où les départs en retraite se produisent : l'expertise du creuset derrière PROC-DEMO-0001 est capturée mais non approuvée, tandis que le domaine énergie - celui qui porte la décision de plan de charge à €2,688.70/jour - a le moins de contenu capturé au départ.""",
    "knowledge-hub-q3": """Deux des trois procédures ne sont pas encore utilisables.

- **PROC-DEMO-0001 - vérification de surchauffe du secteur du creuset.** IN_REVIEW, version 2, session SESS-DEMO-014, deux segments de transcript cités (#seg-4, #seg-7). Directement pertinent pour l'alerte LUX-BF-01 ouverte.
- **PROC-DEMO-0003 - récupération de soak de zone du four de réchauffage.** DRAFT, version 1, session SESS-DEMO-016, un segment cité (#seg-1).
- Déjà approuvée : **PROC-DEMO-0002**, version 3, inspection du circuit de refroidissement et escalade par ultrasons.

**ALERT-KNOWLEDGE-REVIEW-QUEUE** signale trois procédures capturées au-delà du SLA de relecture de 5 jours. L'approbation est une étape humaine par conception : l'approbation de PROC-DEMO-0002 est enregistrée sous l'audit **AUD-0004** avec l'acteur ke-demo à 10:15, de sorte que la chaîne du transcript opérateur à la procédure publiée reste auditable.""",
    "knowledge-hub-q4": """Guide d'entretien, fondé sur PROC-DEMO-0001 et la signature actuelle de LUX-BF-01. Sujet **OP-DEMO-014**, opérateur senior de haut-fourneau ; la capture est soumise à consentement et le transcript est conservé dans ce périmètre de consentement.

- Quand un secteur du creuset se réchauffe mais que le débit de refroidissement est normal, que vérifiez-vous en premier, et dans quel ordre ?
- Quels thermocouples de l'enveloppe des secteurs voisins comparez-vous, et quelle amplitude de delta vous pousse à agir ? SECTOR-07 monte actuellement à 3.4 °C/h contre 0.4 °C/h sur ses voisins.
- Comment distinguez-vous la dégradation du revêtement réfractaire d'un capteur dérivant ? PROC-DEMO-0001 cite la persistance entre les coulées et un refroidissement post-coulée plus lent - que regardez-vous d'autre ?
- Que révèlent le delta T d'entrée et de sortie du refroidissement associé à l'historique récent des débits, que le débit seul ne révèle pas ? Aujourd'hui : 9.4 °C à 198 m³/h.
- À une épaisseur estimée de 363 mm contre un minimum de 300 mm, qu'est-ce qui vous ferait avancer la fenêtre de réfection ?
- Qu'est-il arrivé sur ce fourneau par le passé qu'un nouvel opérateur ne prévoirait pas ?

Limite de sécurité à réaffirmer : ne jamais contourner les alarmes ni modifier les réglages du fourneau ou du refroidissement sur la foi d'une guidance d'entretien.""",
    # -- executive-overview ------------------------------------------------
    "executive-overview-q1": """Trois des quatre résultats cibles sont atteints, un est en déficit. Les chiffres sont le bilan de clôture de juillet 2026 sur les tables gold.

- **Intensité énergétique (KPI-ENE-01)** - **10.63 GJ/t** contre un objectif de 16.77, depuis une base de 19.5. **Atteint**, avec un coût énergétique d'environ €46.5M contre une base de €54.1M.
- **Intensité CO₂ (KPI-CO₂-01)** - **1.019 tCO₂e/t** contre un objectif de 1.638, depuis une base de 2.10. **Atteint**.
- **Avance d'alerte de revêtement réfractaire (KPI-FUR-01)** - chaque épisode d'alerte s'est déclenché exactement à **21.0 jours**, le minimum déclaré, avec unplanned_outage_flag false sur chaque ligne. **Atteint**.
- **Rendement haute qualité au premier passage (KPI-QUA-01)** - **0.9494** contre un objectif de 0.972, depuis une base de 0.90. **Non atteint**, d'environ 2.3 points.
- Indicateur support : adoption du plan de charge **0.862** (100 sur 116 acceptées) contre un minimum de 0.70. **Atteint**.

Les barres de progression sur cet écran affichent 92, 88, 96 et 100 sur 100 pour l'énergie, le CO₂, le rendement et le délai d'alerte. La qualité est le vrai déficit, et c'est là que pointe le travail de capture des connaissances.""",
    "executive-overview-q2": """**Saarbrucken (DE)** en termes de performance, **Moselle (LU)** en termes de risque.

- Moselle (LU) - énergie -14.2%, CO₂ -22.4%, rendement +8.1%, **3 alertes ouvertes** dont la seule critique
- Saarbrucken (DE) - énergie **-11.8%**, CO₂ **-18.6%**, rendement **+6.4%**, 2 alertes ouvertes : dernier sur les trois axes
- Liege (BE) - énergie -13.1%, CO₂ -20.2%, rendement +7.2%, 1 alerte ouverte
- Asturias (ES) - énergie -12.5%, CO₂ -19.4%, rendement +7.9%, 2 alertes ouvertes

Saarbrucken est le seul site en dessous de l'objectif du programme sur les trois axes, et ses points en suspens sont de nature économique : oscillation du niveau de métal en lingotière au-dessus de la plage de 4.5 mm, et mélange de charge de ferraille 3.1% au-dessus de la recette à moindre coût.

Moselle est en tête sur tous les axes mais porte la prédiction de creuset de LUX-BF-01 - risque 0.90, 19.65 jours - la question à €8M de cette semaine.""",
    "executive-overview-q3": """Quatre résultats engagés, mesurés sur un jeu de données pilote synthétique, exprimés comme objectifs là où ce sont des objectifs.

- **Objectifs** - énergie par tonne -14%, CO₂ par tonne -22%, rendement haute qualité +8%, au moins 21 jours d'alerte de revêtement réfractaire.
- **Mesurés dans les données pilote** - intensité énergétique 10.63 GJ/t et intensité CO₂ 1.019 tCO₂e/t en juillet 2026 ; chaque alerte de revêtement réfractaire émise exactement à 21.0 jours sans arrêt non planifié ; rendement haute qualité au premier passage 0.9494, toujours en dessous de l'objectif de 0.972.
- **Mesurés sur un seul plan de charge aujourd'hui** - €2,688.70 économisés (7.25%), puissance de pointe -7.89%, CO₂ -3.29%, zéro violation de contrainte.
- **Modélisés, pas réalisés** - une défaillance évitée, valorisée dans le cas d'usage à €8M par défaillance non planifiée de creuset.

La gouvernance a le même poids que les chiffres : cinq enregistrements de décision sur cinq domaines, trois d'entre eux liés à un modèle, 100% d'immuabilité, et chaque recommandation nécessitant une décision humaine avant d'agir.""",
    "executive-overview-q4": """La séparation est nette, et les tuiles l'indiquent dans leurs infobulles.

**Objectifs, pas mesures :** énergie par tonne -14%, CO₂ par tonne -22%, rendement haute qualité +8%, au moins 21 jours d'avance. Ce sont les engagements du cas d'usage au niveau de la flotte.

**Mesurés dans cette démo :**
- Plan de charge - **€2,688.70 (7.25%)** économisés, pointe 56.0 à 51.58 MW, CO₂ **-3.29%**, 0 violation dure
- Fourneau - risque 0.8995 avec **P50 19.65 jours** d'avance sur LUX-BF-01, en dessous de l'objectif de 21 jours sur cet épisode en direct
- Scénario hypothétique qualité - rendement au premier passage prédit d'environ 88% à environ 95%, modèle quality-yield-gbm/2.1.0-demo
- Bilan gold de juillet 2026 - 10.63 GJ/t, 1.019 tCO₂e/t, alerte à 21.0 jours sur chaque épisode, rendement haute qualité au premier passage 0.9494

**Modélisés :** la valeur de défaillance évitée à €8M et le compteur de défaillances évitées.

Le seul chiffre à ne jamais présenter comme atteint est l'objectif CO₂ : l'objectif de la flotte est -22%, tandis que cette démo de site unique mesure -3.29% sur un seul plan de charge.""",
    # -- platform-ops ------------------------------------------------------
    "platform-ops-q1": """**En cours (Running)** - capacité **cap-novasteel-demo-sc**, SKU **F2**, région Sweden Central, environnement demo.

- Reprise ce matin : Paused vers Resuming à 07:27, Resuming vers ReadinessCheck à 07:28, ReadinessCheck vers Running à 07:30 - toutes par demo-platform-ops avec la raison "rehearsal"
- Politique de cycle de vie : vérification de pause nocturne à **01:00 Europe/Luxembourg**
- Le SKU est commutable entre F2, F4 et F8 ; le changement d'état est enregistré sous l'audit **AUD-0005**
- L'espace de travail NovaSteelV3-Demo porte le lakehouse lh_novasteelv3_core, la base de données KQL kql-ns-operations et l'ontologie onto_novasteelv3

Il s'agit d'une capacité hors production, et le cycle de vie est délibérément limité au démarrage, à la mise en pause et au changement de SKU - chacun audité.""",
    "platform-ops-q2": """**Aucune en échec.** Quatre des cinq exécutions récentes ont réussi et une est toujours en cours.

- RUN-4821 bronze-to-silver - SUCCEEDED, 17:45, **214 s**
- RUN-4820 silver-to-gold - SUCCEEDED, 17:30, **176 s**
- RUN-4819 semantic-refresh - **RUNNING**, démarrée à 18:40, 62 s en cours
- RUN-4818 contract-assertions - SUCCEEDED, 17:10, 41 s
- RUN-4817 quarantine-negative-tests - SUCCEEDED, 16:55, 33 s

Les deux tâches de garde ont réussi : les assertions de contrat sur les enveloppes d'événements, et les tests négatifs qui prouvent que les payloads non conformes atterrissent en quarantaine plutôt qu'en silver. La fraîcheur de bout en bout est de **12 s**. Le seul point en suspens est le semantic refresh.""",
    "platform-ops-q3": """Stable et modeste - il s'agit d'un F2 portant une charge de travail de démo.

- Coût par heure **€2.80**, oscillant d'environ €0.40 dans les deux sens sur la fenêtre 06:00-18:00
- L'utilisation est en moyenne d'environ **38%**, suivant un profil lisse entre approximativement 26% et 50%
- La dépense à ce jour est la somme des 13 points horaires de la tendance
- Fraîcheur de la télémétrie **12 s**

La forme importe plus que le total : l'utilisation culmine avec les exécutions silver-to-gold et semantic-refresh, raison pour laquelle la vérification de pause nocturne à 01:00 ne coûte rien en débit. Sur un F2, la capacité elle-même est le plancher de la facture, donc la mise en pause entre les démos est le seul levier réel.""",
    "platform-ops-q4": """**Pas encore - RUN-4819 (semantic-refresh) est toujours en cours**, 62 s, démarrée à 18:40.

- Les quatre autres exécutions sont terminées : bronze-to-silver, silver-to-gold, contract-assertions et quarantine-negative-tests ont toutes SUCCEEDED entre 16:55 et 17:45
- Mettre en pause pendant un semantic-model refresh laisse le modèle non rafraîchi, les tableaux de bord serviraient donc le précédent snapshot gold à la reprise
- La capacité **cap-novasteel-demo-sc** est F2, Running depuis 07:30, environnement demo
- La politique de cycle de vie exécute déjà sa vérification de pause à **01:00 Europe/Luxembourg**, heure à laquelle cette exécution sera largement terminée

Attendre que RUN-4819 signale SUCCEEDED, puis mettre en pause. La transition est enregistrée comme les autres, avec acteur et raison.""",
    # -- device-operations -------------------------------------------------
    "device-operations-q1": """**Aucun.** Les **17 équipements** sont en communication et il y a **0 incident actif** injecté.

- Flotte : 6 au Luxembourg (LUX-BF-01, LUX-BOF-01, LUX-CC-01, LUX-RHF-01, LUX-HSM-01, LUX-UTIL-01), 4 en Allemagne, 4 en Belgique, 3 en Espagne
- **91 signaux capteurs** en ligne sur la flotte
- Disponibilité entre **99.10% et 99.95%** par équipement
- Simulateur : scénario **demo-full**, seed 240726, tick 720, environ 6 heures écoulées à 5 s par tick

Le seul équipement portant une alerte ouverte est **LUX-BF-01** - la prédiction du creuset - et il s'agit d'une condition de procédé, pas d'une défaillance d'équipement : ses thermocouples, ses signaux de flux de chaleur et de refroidissement publient tous selon le calendrier prévu. La santé sur cet écran est mesurée par la fraîcheur des signaux et le nombre d'alarmes, ainsi un équipement sain peut se trouver derrière une alerte de procédé critique.""",
    "device-operations-q2": """Il mesure la santé de l'équipement, pas la santé du procédé. Trois entrées :

- **Disponibilité (Uptime)** - la part de la fenêtre pendant laquelle l'équipement a publié. La flotte se situe entre **99.10% et 99.95%**.
- **Fraîcheur des signaux** - chaque signal a une période d'émission attendue et devient obsolète dès qu'il la dépasse. Les périodes vont de **1 s** (arc_current sur DE-EAF-01) et 5 s (hearth_shell_temperature, local_heat_flux) jusqu'à **900 s** (hearth_refractory_estimate, spot_price, grid_carbon_intensity). Un signal est piloté par événement sans période du tout : hot_metal_temperature, émis uniquement à une coulée.
- **Nombre d'alarmes** - alarmes d'équipement actives sur la fenêtre, pondérées par gravité.

Un équipement est sain quand les trois tiennent, dégradé quand la fraîcheur ou les alarmes glissent, et en défaillance quand il cesse de publier. Au tick 720 sans incident injecté, les **17 équipements et 91 signaux** sont tous sains - c'est pourquoi l'alerte de procédé LUX-BF-01 se trouve à côté d'un score d'équipement propre.""",
    "device-operations-q3": """**Aucun signal n'est obsolète en ce moment** - les **91 signaux** sont dans leur période attendue au tick 720.

L'obsolescence est évaluée par signal, et les périodes varient considérablement :
- **1-5 s** - arc_current (DE-EAF-01), hearth_shell_temperature et local_heat_flux (LUX-BF-01), zinc_bath_temperature (BE-GAL-01)
- **10 s** - bath_temperature sur LUX-BOF-01 et DE-EAF-01
- **60 s** - production_rate
- **900 s** - hearth_refractory_estimate, spot_price, grid_carbon_intensity
- **Piloté par événement** - hot_metal_temperature, émis uniquement à une coulée

Cela importe car un modèle n'est à jour que si son entrée la plus lente l'est. Le score de revêtement réfractaire dépend de hearth_refractory_estimate et local_heat_flux : si l'estimation réfractaire à 900 s devient obsolète, la **durée de vie résiduelle P50 de 19.65 jours** cesse d'évoluer tandis que le fourneau continue de s'amincir à environ 3.0 mm/jour. Le plan de charge a la même exposition via spot_price et grid_carbon_intensity, tous deux également sur 900 s.""",
    "device-operations-q4": """Deux façons, selon la durée souhaitée.

**Incident unique - degrading-furnace.** Gravité haute, durée par défaut **30 minutes**, cible **LUX-BF-01**, pilotant local_heat_flux, hearth_refractory_estimate et hearth_shell_temperature. Sélectionnez-le dans le panneau d'incidents sur cet écran, confirmez l'équipement et la durée, puis injectez.

**Scénario complet - lining-degradation-21d.** Redémarrez le simulateur sur ce scénario plutôt que demo-full pour jouer l'arc de dégradation complet plutôt qu'une excursion de 30 minutes.

- État actuel : scénario **demo-full**, seed **240726**, tick 720, environ 6 heures écoulées, ticks de 5 s, **0 incident actif**
- Autres scénarios disponibles : healthy-baseline, energy-price-spike, quality-drift, edge-outage-recovery
- Autres incidents : cooling-water-loss (critique, 15 min), sensor-drift (60 min), sensor-dropout (10 min), energy-price-spike (45 min, LUX-UTIL-01), quality-drift (45 min, LUX-CC-01 et LUX-HSM-01), edge-outage-recovery (20 min)

L'effet sur la santé du fourneau devrait se manifester en quelques ticks : score de risque au-dessus de 0.80 et durée de vie résiduelle P50 entre **19 et 23 jours**, ce qui correspond à la plage dans laquelle le scénario est délimité.""",
    # -- dashboards --------------------------------------------------------
    "dashboards-q1": """**Passation de poste du matin** - Responsable d'usine, environ **6 minutes**, tagué daily et triage.

Elle couvre le centre de commande, puis les opérations, puis les alertes ouvertes - c'est l'ordre dont une passation a réellement besoin : ce qui est critique, ce que la ligne a fait, ce qui est encore ouvert.

Ce qu'elle montrerait en ce moment : **16 alertes ouvertes** (1 critique, 8 avertissements, 7 informations, 2 acquittées), débit **128.4 t/h** contre 130, OEE **84.1%**, et un ordre de travail - WO-DEMO-LUX-1042 - créé contre la prédiction du creuset.

Si la passation porte spécifiquement sur le fourneau, utilisez **Investigation du risque fourneau** (environ 8 minutes) à la place ; c'est la plus approfondie des deux.""",
    "dashboards-q2": """**Dossier de preuves de conformité** - Responsable développement durable et Auditeur, environ **7 minutes**, tagué compliance, audit et eu-ai-act.

Il rassemble la piste de preuves plutôt que les métriques :
- **5 enregistrements de décision**, AUD-0001 à AUD-0005, couvrant tous les **5 domaines** : haut-fourneau, énergie, qualité, connaissances et capacité
- **3 d'entre eux liés à un modèle** - lining-rul-piml/1.3.0-demo, energy-dispatch-milp/1.2.0-demo et quality-yield-gbm/2.1.0-demo
- **100% d'immuabilité**, avec l'identifiant de corrélation run-demo-full-240725 liant les décisions haut-fourneau, énergie et qualité à une seule exécution
- Le registre d'émissions derrière elles : 96 lignes d'intervalles append-only, Scope 1 et Scope 2 séparés, ETS tarifé à €86/t
- Points de décision humains : chaque recommandation porte un acteur et un horodatage, ce sur quoi repose l'argument de traçabilité de l'EU AI Act

C'est le dossier : ce qui a été décidé, par quelle version de modèle, sur quelles données, et approuvé par qui.""",
    "dashboards-q3": """Six collections, chacune étant un parcours fixe à travers des écrans déjà existants.

- **Passation de poste du matin** - Responsable d'usine, environ 6 min, daily et triage. Ce qui est critique, ce que la ligne a fait, ce qui est encore ouvert.
- **Investigation du risque fourneau** - Ingénieur maintenance et fiabilité, environ 8 min, reliability et root-cause. Le risque de revêtement réfractaire est-il réel, qu'est-ce qui le cause, quand doit-on agir.
- **Revue énergie et coût** - Responsable énergie, environ 7 min, energy et cost. Ce que le planning coûte, ce que l'alternative économise, ce qui le contraint.
- **Revue d'échappement qualité** - Ingénieur qualité, environ 6 min, quality et root-cause. Quel lot, quelle étape, quel ajustement.
- **Dossier de preuves de conformité** - Responsable développement durable et Auditeur, environ 7 min, compliance, audit et eu-ai-act. Ce qui a été décidé, par quel modèle, approuvé par qui.
- **Santé et dépenses de la plateforme** - Opérations plateforme, environ 5 min, platform et cost. Le pipeline est-il sain, quel est son coût.

Chaque collection comprend trois ou quatre écrans ordonnés et n'ajoute aucune donnée propre - les chiffres restent la propriété des écrans qu'elle relie.""",
    "dashboards-q4": """**Investigation du risque fourneau** - Ingénieur maintenance et fiabilité, environ **8 minutes**, tagué reliability et root-cause. Elle couvre la prévision du revêtement réfractaire, puis l'explorateur thermique, puis le planificateur de maintenance - l'ordre dans lequel les preuves se construisent.

Ce qu'elle montrerait en ce moment :
- Prévision revêtement réfractaire - LUX-BF-01 / HEARTH-SECTOR-07 à risque **0.8995**, durée de vie résiduelle **P50 19.65 jours** (P10 18.69 / P90 20.61)
- Explorateur thermique - SECTOR-07 montant à **3.4 °C/h** contre 0.4 °C/h sur ses voisins, dépassant le seuil d'anomalie de 700 °C
- Planificateur de maintenance - **WO-DEMO-LUX-1042** ouvert sur le secteur, fenêtre de réfection aux jours 18-24

Pour la passation plus large, utilisez Passation de poste du matin (environ 6 min) ; pour le cadrage d'audit plutôt que l'aspect ingénierie, le Dossier de preuves de conformité porte la piste de décision derrière le même appel.""",
}