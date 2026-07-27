import type { HelpCatalog } from '../components/help/helpTypes'

export const HELP_FR: HelpCatalog = {
  // ---------------------------------------------------------------- generic
  'generic.kpi': {
    title: 'Chiffre clé',
    what: 'Une tuile montre une mesure, sa flèche de tendance et son écart à la cible.',
    steel:
      'Une aciérie se pilote avec quelques chiffres. Les afficher côte à côte permet au chef de poste de comprendre l\u2019état de l\u2019usine en quelques secondes au lieu de lire des rapports.',
    useIt: 'Une tuile avec un curseur en forme de flèche peut être cliquée pour ouvrir le détail derrière le chiffre.',
  },
  'generic.chart': {
    title: 'Graphique',
    what: 'Une image de l\u2019évolution d\u2019une mesure dans le temps ou de sa répartition entre les parties de l\u2019usine.',
    steel:
      'Un chiffre isolé cache l\u2019histoire. Un four dont la température moyenne est sûre peut quand même connaître des pics dangereux, que seul un graphique montre.',
    useIt: 'Survolez un point pour voir sa valeur exacte. Les graphiques dans un panneau peuvent être agrandis avec le bouton maximiser de la barre d\u2019onglets.',
  },
  'generic.table': {
    title: 'Table de données',
    what: 'Les enregistrements individuels derrière les chiffres de synthèse, un par ligne.',
    steel: 'Quand un chiffre semble faux, la table indique le lot, le capteur ou l\u2019ordre de travail précis qui l\u2019a causé.',
    useIt: 'Cliquez sur un en-tête de colonne pour trier, utilisez les contrôles d\u2019en-tête pour filtrer et la zone de recherche pour trouver du texte dans toute la table.',
  },
  'generic.tableRow': {
    title: 'Un enregistrement',
    what: 'Un élément unique : un lot, une mesure de capteur, un ordre de travail ou une alerte.',
    steel: 'Tout ce qui se passe dans l\u2019usine finit par être écrit comme un enregistrement de ce type, ce qui rend un audit possible.',
    useIt: 'Quand une ligne est cliquable, elle ouvre le détail complet de cet élément.',
  },
  'generic.tableHeader': {
    title: 'En-tête de colonne',
    what: 'Le nom d\u2019une colonne et le contrôle qui trie et filtre la table selon celle-ci.',
    steel: 'Trier par risque ou par date permet à un ingénieur de transformer une longue liste en courte liste d\u2019actions pour aujourd\u2019hui.',
    useIt: 'Cliquez une fois pour trier par ordre croissant, puis encore pour l\u2019ordre décroissant. Les filtres réduisent la table aux seules lignes correspondantes.',
  },
  'generic.panel': {
    title: 'Panneau de travail',
    what: 'Une section déplaçable de l\u2019écran. Les panneaux peuvent être glissés par leur onglet vers un bord, redimensionnés ou empilés.',
    steel: 'Les opérateurs de salle de contrôle ne surveillent pas tous les mêmes choses. La mise en page s\u2019adapte donc à la personne, et non l\u2019inverse.',
    useIt: 'Glissez l\u2019onglet pour réorganiser. Réinitialiser la mise en page dans l\u2019en-tête remet tout en place.',
  },
  'generic.dockTab': {
    title: 'Onglet de panneau',
    what: 'La poignée d\u2019un panneau. Elle nomme le panneau et permet de le déplacer.',
    steel: 'Les panneaux qui doivent rester visibles n\u2019ont pas de bouton de fermeture, afin qu\u2019une vue critique ne soit pas perdue par accident.',
    useIt: 'Glissez-le pour déplacer le panneau, ou cliquez sur le bouton maximiser pour qu\u2019il remplisse l\u2019espace de travail.',
  },
  'generic.button': {
    title: 'Action',
    what: 'Un contrôle qui change ce qui est affiché ou demande à la plateforme de faire quelque chose.',
    steel:
      'Tout ce qui pourrait changer le comportement de l\u2019usine reste ici une proposition. Un humain l\u2019approuve encore avant que cela atteigne les équipements.',
    useIt: 'Survolez pour afficher une info-bulle décrivant ce que fait l\u2019action.',
  },

  // ------------------------------------------------------------ chart types
  'chart.line': {
    title: 'Graphique en courbe',
    what: 'Le temps va de gauche à droite, et la mesure de bas en haut. La ligne relie les mesures successives.',
    steel: 'Les procédés sidérurgiques dérivent lentement, donc la pente compte plus qu\u2019une mesure isolée. Une ligne qui monte est un avertissement précoce.',
    useIt: 'Cherchez les ruptures soudaines et une pente qui continue dans la même direction.',
  },
  'chart.area': {
    title: 'Graphique en aires',
    what: 'Un graphique en courbe dont l\u2019espace sous la ligne est rempli, ce qui facilite la comparaison des totaux.',
    steel: 'Utile pour des quantités qui s\u2019accumulent, comme l\u2019énergie consommée ou les émissions rejetées pendant un poste.',
    useIt: 'Comparez la taille des zones remplies plutôt que la hauteur de la ligne.',
  },
  'chart.bar': {
    title: 'Graphique en barres',
    what: 'Une barre par catégorie. Plus la barre est haute, plus la valeur est grande.',
    steel: 'Pratique pour comparer d\u2019un coup d\u2019œil des fours, des nuances d\u2019acier ou des postes.',
    useIt: 'Cherchez la barre qui sort du lot : c\u2019est souvent là que se trouve le problème ou l\u2019occasion.',
  },
  'chart.heatmap': {
    title: 'Carte thermique',
    what: 'Une grille où la couleur représente une valeur. Les couleurs plus foncées ou plus chaudes indiquent des mesures plus élevées.',
    steel:
      'Un haut fourneau est garni de centaines de capteurs. Une carte thermique les montre tous à la fois, afin qu\u2019un point chaud sur la virole se voie immédiatement.',
    useIt: 'Cherchez les cellules claires isolées. Une cellule chaude entourée de cellules froides indique souvent une usure locale.',
  },
  'chart.gauge': {
    title: 'Jauge',
    what: 'Un cadran qui montre une valeur par rapport à sa plage sûre.',
    steel: 'Elle reprend les instruments analogiques utilisés depuis des décennies au pied de l\u2019usine, donc elle se comprend vite sur un écran de contrôle.',
    useIt: 'La bande colorée indique si la valeur actuelle est confortable, limite ou hors tolérance.',
  },
  'chart.control': {
    title: 'Carte de contrôle',
    what: 'Un graphique temporel avec une ligne centrale pour la cible et deux lignes extérieures pour la plage acceptable.',
    steel:
      'C\u2019est l\u2019outil qualité classique. Un procédé qui reste entre les lignes extérieures est prévisible ; un point dehors signifie que quelque chose a changé et doit être étudié.',
    useIt: 'Surveillez les points hors limites et les longues séries de points du même côté de la ligne centrale.',
  },
  'chart.pareto': {
    title: 'Diagramme de Pareto',
    what: 'Des barres triées de la plus grande à la plus petite, avec une ligne montante qui montre le cumul.',
    steel:
      'La plupart des rebuts et retouches viennent d\u2019un petit nombre de causes. Corriger les deux ou trois premières barres supprime souvent la majeure partie de la perte.',
    useIt: 'Trouvez où la ligne atteint 80 pour cent : les barres à gauche sont votre liste de priorités.',
  },
  'chart.donut': {
    title: 'Diagramme en anneau',
    what: 'Un anneau découpé en parts, chaque part représentant une fraction du total.',
    steel: 'Il sert aux répartitions, par exemple l\u2019origine des émissions, quand une part se juge plus facilement qu\u2019un pourcentage dans une table.',
    useIt: 'Comparez la taille des parts ; survolez pour voir la part exacte.',
  },
  'chart.gantt': {
    title: 'Diagramme de planning',
    what: 'Chaque barre est une activité, placée et dimensionnée selon sa date de début et sa durée.',
    steel:
      'Les regarnissages de four et les arrêts de maintenance doivent s\u2019insérer entre les campagnes de production. Les voir sur une seule chronologie aide les planificateurs à éviter les conflits.',
    useIt: 'Cherchez les chevauchements et les vides qui pourraient recevoir une fenêtre de maintenance.',
  },
  'chart.priceLoad': {
    title: 'Graphique prix et charge',
    what: 'Deux éléments sur une même chronologie : le prix de l\u2019électricité et la puissance que l\u2019usine prévoit d\u2019appeler.',
    steel:
      'L\u2019électricité est l\u2019un des plus grands coûts de la sidérurgie et son prix change chaque heure. Faire les tâches très énergivores quand le prix est bas économise de l\u2019argent réel.',
    useIt: 'Vérifiez que les grandes barres de charge se trouvent sous les points bas de la courbe de prix.',
  },
  'chart.bullet': {
    title: 'Barre de progression',
    what: 'Une barre qui montre où la valeur actuelle se situe entre zéro et sa cible.',
    steel: 'Elle donne une idée rapide de la part déjà utilisée d\u2019un engagement, par exemple un budget annuel d\u2019émissions.',
    useIt: 'Le repère sur la barre est la cible ; la partie remplie montre où vous en êtes réellement.',
  },
  'chart.sparkline': {
    title: 'Mini-tendance',
    what: 'Un très petit graphique en courbe sans axes, qui montre seulement la forme récente de la mesure.',
    steel: 'Il tient dans une tuile de synthèse et donne la direction sans quitter l\u2019écran récapitulatif.',
    useIt: 'Lisez la forme, pas les valeurs. Cliquez sur la tuile pour voir le graphique complet.',
  },

  // ------------------------------------------------------- executive layer
  'kpi:energy': {
    title: 'Intensité énergétique',
    what: 'Électricité et combustible utilisés pour produire une tonne d\u2019acier, en kilowattheures par tonne.',
    steel:
      'Produire de l\u2019acier signifie chauffer du minerai de fer ou de la ferraille à environ 1 600 degrés Celsius. L\u2019énergie est donc à la fois le plus gros coût et la plus grande source d\u2019émissions.',
    useIt: 'Comparez avec la ligne cible. Une baisse ici se traduit directement en coût et en carbone.',
  },
  'kpi:co2': {
    title: 'Émissions de dioxyde de carbone',
    what: 'Tonnes de CO2 rejetées, ou réduction obtenue par rapport à la période de référence.',
    steel:
      'L\u2019acier représente environ sept pour cent du CO2 mondial. En Europe, une usine doit restituer un quota d\u2019émission pour chaque tonne rejetée, donc ce chiffre a un prix.',
    useIt: 'Lisez-le avec l\u2019intensité énergétique : la plupart des baisses viennent d\u2019une électricité moindre ou plus propre.',
  },
  'kpi:yield': {
    title: 'Rendement en haute qualité',
    what: 'La part de la production qui respecte la spécification premium du premier coup.',
    steel:
      'L\u2019acier hors spécification n\u2019est pas un déchet : il est refondu. Mais la refonte consomme l\u2019énergie deux fois, donc le rendement est aussi une mesure cachée de coût et d\u2019énergie.',
    useIt: 'Une baisse ici apparaît généralement peu après dans les écrans qualité.',
  },
  'kpi:warning': {
    title: 'Préavis d\u2019alerte',
    what: 'Le nombre de jours d\u2019avance que les modèles donnent avant qu\u2019un problème prévu ne survienne.',
    steel:
      'Commander des briques réfractaires et réserver une équipe de réparation prend des semaines. Une alerte trop tardive ne vaut rien, donc le préavis compte autant que la précision.',
    useIt: 'La cible du pilote est au moins 21 jours. Moins que cela ne laisse pas le temps de planifier un arrêt.',
  },
  'kpi:failures': {
    title: 'Arrêts non planifiés',
    what: 'Nombre de fois où la production s\u2019est arrêtée sans que ce soit prévu.',
    steel:
      'Un arrêt non planifié de haut fourneau coûte extrêmement cher : il faut garder la cuve chaude, les laminoirs en aval manquent de matière et le redémarrage consomme de l\u2019énergie.',
    useIt: 'L\u2019objectif de toute la plateforme est de transformer ces arrêts en arrêts planifiés.',
  },

  // ---------------------------------------------------------- furnace health
  'kpi:risk': {
    title: 'Risque du garnissage',
    what: 'Un score de 0 à 1 qui estime la probabilité que le garnissage du four atteigne bientôt sa limite d\u2019usure.',
    steel:
      'Un haut fourneau est une coque d\u2019acier garnie de briques résistantes à la chaleur, appelées réfractaires. La brique s\u2019érode lentement ; si elle perce, le métal en fusion atteint la coque. Ce score est l\u2019alerte précoce de l\u2019usine.',
    useIt: 'Au-dessus de 0,8, le planificateur de maintenance devrait réserver une fenêtre de réparation.',
  },
  'kpi:days': {
    title: 'Durée de vie utile restante',
    what: 'Nombre estimé de jours de fonctionnement avant que le garnissage atteigne sa limite d\u2019usure, au rythme actuel.',
    steel:
      'Dans l\u2019industrie, on l\u2019appelle RUL. Remplacer un garnissage est une campagne de plusieurs semaines, donc connaître la date des mois à l\u2019avance transforme une crise en projet.',
    useIt: 'Utilisez le niveau de confiance à côté : une durée courte avec une faible confiance demande plus de mesures, pas une action immédiate.',
  },
  'kpi:confidence': {
    title: 'Confiance du modèle',
    what: 'Le degré de certitude du modèle sur sa propre prévision, compte tenu des données disponibles.',
    steel: 'Les capteurs tombent en panne et les mesures dérivent. Publier la confiance avec la réponse évite qu\u2019un ingénieur fasse confiance à un chiffre basé sur peu de données.',
    useIt: 'Une faible confiance signale qu\u2019il faut vérifier la santé des capteurs avant d\u2019agir sur la prévision.',
  },
  'kpi:failDate': {
    title: 'Date projetée de fin de vie',
    what: 'La date calendaire indiquée par l\u2019estimation de durée restante.',
    steel: 'Transformer "tant de jours" en date permet aux planificateurs de l\u2019aligner avec les congés, la disponibilité des sous-traitants et le carnet de commandes.',
    useIt: 'Comparez-la avec la fenêtre de maintenance prévue sur l\u2019écran de planification.',
  },
  'kpi:anomalies': {
    title: 'Anomalies thermiques',
    what: 'Nombre de mesures qui se sont écartées du schéma attendu dans la fenêtre sélectionnée.',
    steel:
      'Un point chaud local sur la virole du four est généralement le premier signe physique que la brique derrière lui s\u2019est amincie.',
    useIt: 'Ouvrez la carte thermique pour voir où les anomalies sont regroupées sur la virole.',
  },
  'kpi:cooling': {
    title: 'Performance du refroidissement à eau',
    what: 'L\u2019efficacité avec laquelle le système de refroidissement évacue la chaleur de la virole du four.',
    steel:
      'Des boîtes de refroidissement à eau se trouvent entre la brique et la coque d\u2019acier. Si le refroidissement faiblit, la coque chauffe, donc c\u2019est une mesure de sécurité, pas seulement d\u2019efficacité.',
    useIt: 'La combinaison importante est une valeur qui baisse avec une température de coque qui monte.',
  },
  'kpi:slope': {
    title: 'Tendance de température',
    what: 'La vitesse à laquelle la température monte ou descend, en degrés par jour.',
    steel: 'L\u2019usure réfractaire est lente, donc une pente montante persistante, même d\u2019une fraction de degré par jour, compte.',
    useIt: 'Le signe compte plus que la taille. Une pente positive durable sur un secteur mérite un examen.',
  },
  'kpi:sensor': {
    title: 'Couverture des capteurs',
    what: 'Combien de capteurs thermiques envoient actuellement des données saines.',
    steel: 'Les prévisions ne valent que par leurs entrées. Un secteur avec des capteurs morts est de fait non surveillé.',
    useIt: 'Vérifiez avec l\u2019écran du parc d\u2019appareils lorsque le nombre baisse.',
  },
  'furnace-health/thermal-explorer:kpi:peak': {
    title: 'Température maximale de coque',
    what: 'La température la plus élevée mesurée sur la coque du four pendant la période sélectionnée.',
    steel:
      'La coque doit rester bien plus froide que l\u2019intérieur en fusion. Un pic qui monte signifie que la chaleur trouve un chemin à travers le garnissage réfractaire.',
    useIt: 'Utilisez la carte thermique pour trouver quel secteur a produit le pic.',
  },
  'kpi:open': {
    title: 'Ordres de travail ouverts',
    what: 'Travaux de maintenance créés mais pas encore terminés.',
    steel: 'Les aciéries fonctionnent en continu, donc la maintenance entre en concurrence avec la production pour le temps. Le retard est le coût visible du report.',
    useIt: 'Triez la table des ordres de travail par priorité pour voir ce qui devrait entrer dans la prochaine fenêtre.',
  },
  'kpi:urgent': {
    title: 'Ordres de travail urgents',
    what: 'Travaux marqués comme devant être traités avant le prochain arrêt planifié.',
    steel: 'Ce sont ceux qui décident si le prochain arrêt sera planifié ou forcé.',
    useIt: 'Tout élément ici doit être comparé à la durée de la fenêtre de maintenance.',
  },
  'kpi:completed': {
    title: 'Ordres de travail terminés',
    what: 'Travaux clôturés pendant la période actuelle.',
    steel: 'Le taux de clôture par rapport au retard indique si la capacité de maintenance correspond aux besoins de l\u2019usine.',
    useIt: 'Lisez-le avec le nombre d\u2019ordres ouverts : les deux en baisse, c\u2019est bon ; seulement les terminés en baisse, non.',
  },
  'kpi:window': {
    title: 'Fenêtre de maintenance',
    what: 'La durée du prochain arrêt de production planifié disponible pour les réparations.',
    steel:
      'Regarnir une partie d\u2019un four peut prendre des jours et la cuve doit d\u2019abord refroidir. Faire tenir le travail dans la fenêtre est le problème central du planificateur.',
    useIt: 'Comparez-la avec la durée totale des ordres de travail urgents.',
  },

  // ------------------------------------------------------------------ energy
  'kpi:price': {
    title: 'Prix spot de l\u2019électricité',
    what: 'Le coût actuel d\u2019un mégawattheure d\u2019électricité sur le marché de gros.',
    steel:
      'Les prix européens de l\u2019électricité changent chaque heure et peuvent varier plusieurs fois dans une journée. Une usine capable de déplacer une charge flexible vers les heures bon marché réduit sa facture sans produire moins.',
    useIt: 'Alignez-le avec la charge prévue sur le graphique prix et charge.',
  },
  'kpi:savings': {
    title: 'Économies projetées',
    what: 'Argent que le planning proposé économiserait par rapport à l\u2019exécution des mêmes travaux à tarif plat.',
    steel: 'L\u2019économie vient uniquement du moment choisi. Les mêmes tonnes sont produites, mais pendant des heures moins chères.',
    useIt: 'C\u2019est une proposition. Elle ne devient réelle qu\u2019après approbation du planning par un opérateur.',
  },
  'kpi:shiftable': {
    title: 'Charge déplaçable',
    what: 'La part de la demande électrique de l\u2019usine qui peut être déplacée vers une autre heure.',
    steel:
      'Un haut fourneau ne peut pas être mis en pause, mais les fours de réchauffage, les laminoirs et les usines d\u2019oxygène ont une certaine flexibilité. Seule cette part flexible peut suivre l\u2019électricité bon marché.',
    useIt: 'Elle fixe le plafond de ce que toute optimisation peut atteindre.',
  },
  'kpi:baseline': {
    title: 'Scénario de référence',
    what: 'Ce que seraient le coût et les émissions sans aucun déplacement de charge.',
    steel: 'Toute amélioration annoncée doit être mesurée contre quelque chose. Ceci est cette référence.',
    useIt: 'Comparez-le au scénario optimisé pour lire le bénéfice.',
  },
  'kpi:optimized': {
    title: 'Scénario optimisé',
    what: 'Coût et émissions selon le planning proposé par l\u2019optimiseur.',
    steel: 'L\u2019optimiseur respecte les vraies contraintes de l\u2019usine : durées minimales de marche, vitesses de rampe et limites de raccordement au réseau, pas seulement le prix.',
    useIt: 'Vérifiez la tuile des violations de contraintes avant de faire confiance au chiffre.',
  },
  'kpi:estimate': {
    title: 'Estimation de scénario',
    what: 'Le résultat des réglages de simulation actuellement sélectionnés sur cet écran.',
    steel: 'Elle permet à un planificateur de tester une idée avant d\u2019engager l\u2019usine.',
    useIt: 'Modifiez les curseurs et observez la réaction de ce chiffre.',
  },
  'kpi:violations': {
    title: 'Violations de contraintes',
    what: 'Le nombre de règles de l\u2019usine que le scénario actuel enfreindrait.',
    steel:
      'Les contraintes codent la réalité physique : un four qui doit rester au-dessus d\u2019une température, un laminoir qui ne peut pas démarrer et s\u2019arrêter sans cesse. Un planning bon marché qui les enfreint n\u2019est pas un planning.',
    useIt: 'Ce nombre doit être zéro avant qu\u2019un scénario puisse être proposé pour approbation.',
  },
  'energy-optimization/load-shift-simulator:kpi:peak': {
    title: 'Demande de pointe',
    what: 'Le plus fort appel d\u2019électricité que le scénario atteindrait.',
    steel:
      'Les raccordements au réseau sont facturés en partie sur la plus haute pointe atteinte, donc écrêter la pointe économise de l\u2019argent même si la consommation totale ne change pas.',
    useIt: 'Surveillez-la en déplaçant la charge : déplacer un travail peut créer par accident une nouvelle pointe plus élevée.',
  },
  'kpi:server': {
    title: 'État du solveur',
    what: 'Indique si le moteur d\u2019optimisation a trouvé une réponse valide, et sa qualité.',
    steel: 'Dire clairement si le calcul mathématique a convergé distingue un outil d\u2019aide à la décision d\u2019une boîte noire.',
    useIt: 'Un résultat infaisable signifie que les contraintes ne peuvent pas toutes être satisfaites : relâchez-en une et relancez.',
  },

  // ----------------------------------------------------------------- quality
  'kpi:firstpass': {
    title: 'Taux de premier passage',
    what: 'Part des lots qui ont respecté la spécification sans retouche.',
    steel: 'La retouche signifie refonte, qui consomme l\u2019énergie deux fois et retarde la commande. Le taux de premier passage est le point de rencontre entre qualité et coût.',
    useIt: 'Une baisse ici devrait pouvoir être reliée à une cause sur le diagramme de Pareto.',
  },
  'kpi:defect': {
    title: 'Taux de défauts',
    what: 'Part de la production avec un défaut enregistré.',
    steel: 'Les défauts typiques sont les fissures de surface, les inclusions de laitier ou une composition chimique sortie de la plage du client.',
    useIt: 'Utilisez le diagramme de Pareto pour trouver les quelques types de défauts qui dominent.',
  },
  'kpi:ncr': {
    title: 'Rapports de non-conformité',
    what: 'Enregistrements formels créés quand un lot ne respecte pas sa spécification.',
    steel: 'Les clients de l\u2019automobile et de la construction auditent ces enregistrements, donc ils sont une obligation de conformité autant qu\u2019un signal qualité.',
    useIt: 'Ouvrez la table pour voir quelles nuances de produit sont touchées.',
  },
  'kpi:cpk': {
    title: 'Capabilité du procédé (Cpk)',
    what: 'Un chiffre unique qui indique avec quelle marge le procédé tient dans la tolérance du client.',
    steel:
      'Au-dessus de 1,33, le procédé est généralement considéré comme capable ; en dessous de 1,0, des défauts sont attendus par nature plutôt que par accident.',
    useIt: 'Lisez-le avec la carte de contrôle : Cpk résume ce que le graphique montre en détail.',
  },
  'kpi:ooc': {
    title: 'Points hors contrôle',
    what: 'Mesures tombées en dehors des limites statistiques de la carte de contrôle.',
    steel:
      'Hors contrôle ne veut pas dire hors spécification. Cela signifie que le procédé a changé, ce qui justifie une enquête avant que le client ne le remarque.',
    useIt: 'Chaque point devrait avoir une cause assignée enregistrée en face de lui.',
  },
  'kpi:total': {
    title: 'Nombre total de mesures',
    what: 'Le nombre de mesures sur lesquelles reposent les statistiques de cet écran.',
    steel: 'Les règles statistiques ont besoin de suffisamment de données pour avoir du sens. Un indicateur de capabilité tiré de quelques échantillons n\u2019est pas fiable.',
    useIt: 'Élargissez la plage de temps si ce nombre est faible.',
  },
  'kpi:top': {
    title: 'Principal contributeur',
    what: 'La catégorie unique responsable de la plus grande part du problème.',
    steel: 'Les programmes d\u2019amélioration réussissent en corrigeant une cause dominante à la fois, plutôt que tout en même temps.',
    useIt: 'C\u2019est la première barre du diagramme de Pareto.',
  },

  // -------------------------------------------------------- sustainability
  'kpi:allowance': {
    title: 'Quotas d\u2019émission',
    what: 'Permis détenus, chacun couvrant une tonne de CO2.',
    steel:
      'Dans le système d\u2019échange de quotas d\u2019émission de l\u2019Union européenne (SEQE-UE), une usine doit restituer un quota par tonne émise. Certains sont alloués gratuitement, le reste doit être acheté.',
    useIt: 'Comparez avec le plafond et les émissions réelles pour voir l\u2019écart.',
  },
  'kpi:cap': {
    title: 'Plafond de quotas',
    what: 'L\u2019allocation gratuite que l\u2019usine reçoit pour l\u2019année de conformité.',
    steel: 'Le plafond diminue chaque année par conception, ce qui est le mécanisme qui force le secteur à se décarboner.',
    useIt: 'Les émissions au-dessus du plafond doivent être couvertes par des quotas achetés.',
  },
  'kpi:used': {
    title: 'Quotas utilisés',
    what: 'La part de l\u2019allocation déjà consommée depuis le début de l\u2019année.',
    steel: 'La consommation n\u2019est pas régulière sur l\u2019année : un hiver froid ou une longue campagne la déplace.',
    useIt: 'Comparez le pourcentage utilisé avec le pourcentage de l\u2019année écoulé.',
  },
  'kpi:overage': {
    title: 'Déficit projeté',
    what: 'Quotas dont l\u2019usine devrait manquer à la fin de l\u2019année.',
    steel: 'Un déficit doit être acheté sur le marché au prix du carbone du moment, donc c\u2019est une exposition financière directe.',
    useIt: 'Multipliez par le prix du carbone pour voir le coût, affiché dans la tuile d\u2019exposition.',
  },
  'kpi:exposure': {
    title: 'Exposition au coût carbone',
    what: 'La valeur monétaire du déficit de quotas projeté.',
    steel: 'Cela transforme un chiffre environnemental en ligne que le directeur financier comprend, ce qui permet de financer la décarbonation.',
    useIt: 'Elle varie avec les émissions de l\u2019usine et le prix du carbone sur le marché.',
  },
  'kpi:intensity': {
    title: 'Intensité des émissions',
    what: 'CO2 rejeté par tonne d\u2019acier produite.',
    steel:
      'L\u2019intensité est la bonne façon de comparer les usines et les années, car les émissions totales baissent simplement si l\u2019on produit moins. L\u2019intensité ne baisse que si le procédé s\u2019améliore.',
    useIt: 'Utilisez-la plutôt que les tonnes totales pour juger les progrès.',
  },
  'kpi:target': {
    title: 'Cible',
    what: 'La valeur que l\u2019usine s\u2019est engagée à atteindre, affichée à côté de la valeur réelle.',
    steel: 'Les cibles de cette démonstration sont des engagements pilotes, pas des résultats mesurés. La valeur mesurée est toujours affichée à côté.',
    useIt: 'L\u2019écart entre les deux est ce que le programme d\u2019amélioration doit fermer.',
  },
  'kpi:records': {
    title: 'Enregistrements d\u2019audit',
    what: 'Le nombre d\u2019événements écrits dans le journal d\u2019audit infalsifiable.',
    steel: 'Les régulateurs et les clients demandent tous deux comment un chiffre déclaré a été produit. Chaque calcul ici laisse un enregistrement qui répond à cette question.',
    useIt: 'Ouvrez la table pour examiner les entrées individuelles.',
  },
  'kpi:immutable': {
    title: 'Intégrité de la chaîne',
    what: 'Indique si le journal d\u2019audit se vérifie de bout en bout.',
    steel:
      'Chaque entrée porte une empreinte cryptographique de la précédente. Modifier un ancien enregistrement casse donc toutes les empreintes après lui et devient immédiatement visible.',
    useIt: 'Tout état autre que vérifié signifie que le journal ne doit pas être utilisé comme référence.',
  },
  'kpi:models': {
    title: 'Modèles enregistrés',
    what: 'Le nombre de modèles de prévision enregistrés avec une version consignée.',
    steel: 'Si une prévision a influencé une décision, il faut savoir exactement quelle version de quel modèle l\u2019a produite.',
    useIt: 'La version du modèle apparaît à côté de chaque prévision dans la table d\u2019audit.',
  },
  'kpi:domains': {
    title: 'Domaines couverts',
    what: 'Le nombre de zones de l\u2019usine représentées dans la piste d\u2019audit.',
    steel: 'Une couverture partielle est un écart de conformité. Le but est que chaque zone pertinente pour les décisions écrive dans le même journal.',
    useIt: 'Filtrez la table d\u2019audit par domaine pour examiner une zone.',
  },

  // --------------------------------------------------------------- knowledge
  'kpi:sessions': {
    title: 'Sessions de capture',
    what: 'Entretiens enregistrés avec des opérateurs expérimentés puis transformés en projets de procédures.',
    steel:
      'Une grande partie du savoir-faire d\u2019une aciérie vit dans la tête de personnes qui ont conduit le four pendant trente ans. Le capturer avant leur départ en retraite est un vrai problème industriel.',
    useIt: 'Ouvrez une session pour voir la transcription à côté du projet qu\u2019elle a produit.',
  },
  'kpi:coverage': {
    title: 'Couverture des procédures',
    what: 'Part des tâches critiques qui disposent maintenant d\u2019une procédure écrite et approuvée.',
    steel: 'Les manques de couverture sont les endroits où l\u2019usine dépend de la disponibilité d\u2019une seule personne.',
    useIt: 'Utilisez-la pour prioriser les entretiens à mener ensuite.',
  },
  'kpi:approved': {
    title: 'Procédures approuvées',
    what: 'Projets qu\u2019un humain qualifié a relus et validés.',
    steel: 'Une procédure écrite par une machine et jamais vérifiée est une responsabilité. L\u2019approbation est le contrôle qui rend le résultat utilisable.',
    useIt: 'Seules les procédures approuvées sont renvoyées comme réponses par l\u2019assistant.',
  },
  'kpi:review': {
    title: 'En attente de revue',
    what: 'Projets en attente d\u2019acceptation, de correction ou de rejet par un humain.',
    steel: 'Cette file est le point de contrôle humain dans la boucle. Rien ne le contourne.',
    useIt: 'Une file qui grandit signifie que la capacité de revue, et non la capacité de capture, est le goulot d\u2019étranglement.',
  },

  // -------------------------------------------------------------- operations
  'kpi:oee': {
    title: 'Efficacité globale des équipements (OEE)',
    what: 'Un chiffre qui combine le temps de fonctionnement des équipements, leur vitesse et la part de production bonne.',
    steel: 'C\u2019est le tableau de bord standard de la fabrication. Il empêche une usine de revendiquer le succès sur la disponibilité tout en rebutant discrètement du produit.',
    useIt: 'Quand il baisse, vérifiez laquelle des trois parties l\u2019a causé.',
  },
  'kpi:throughput': {
    title: 'Débit de production',
    what: 'Tonnes d\u2019acier produites pendant la période.',
    steel: 'C\u2019est la production de l\u2019usine et le dénominateur de presque toutes les autres mesures de ce portail.',
    useIt: 'Lisez toujours les mesures d\u2019intensité avec lui : une faible production embellit les émissions totales.',
  },
  'kpi:ontime': {
    title: 'Livraison à temps',
    what: 'Part des commandes clients expédiées à la date promise.',
    steel: 'L\u2019acier alimente ensuite des lignes de production planifiées, donc une livraison en retard arrête l\u2019usine de quelqu\u2019un d\u2019autre.',
    useIt: 'Les retards de livraison remontent souvent à des arrêts non planifiés ou à des retouches.',
  },
  'kpi:alerts': {
    title: 'Alertes actives',
    what: 'Conditions actuellement signalées comme nécessitant une attention.',
    steel: 'La fatigue d\u2019alerte est un vrai risque de sécurité, donc cette plateforme vise peu d\u2019alertes mais pertinentes plutôt qu\u2019un grand nombre.',
    useIt: 'Cliquez pour voir le signal sous-jacent de chaque alerte.',
  },

  // ---------------------------------------------------------- platform ops
  'kpi:util': {
    title: 'Utilisation de la capacité',
    what: 'La part de la capacité de calcul analytique réservée qui est utilisée.',
    steel: 'La plateforme fonctionne sur une capacité volontairement petite et facturée à l\u2019heure, afin qu\u2019un environnement de démonstration ne coûte pas comme un environnement de production.',
    useIt: 'Une utilisation élevée durable signale qu\u2019il faut augmenter la capacité avant que les tâches ne commencent à faire la queue.',
  },
  'kpi:utilization': {
    title: 'Utilisation de la capacité',
    what: 'La part de la capacité de calcul analytique réservée qui est utilisée.',
    steel: 'La capacité analytique est facturée à l\u2019heure, qu\u2019elle soit occupée ou non, donc la capacité inactive est une perte pure.',
    useIt: 'Utilisez-la avec la tuile de coût pour juger si la taille actuelle est correcte.',
  },
  'kpi:spend': {
    title: 'Dépense de plateforme',
    what: 'Ce que la plateforme analytique a coûté sur la période affichée.',
    steel: 'Un système d\u2019aide à la décision doit coûter moins que les pertes qu\u2019il évite. Afficher le coût ouvertement fait partie de cet argument.',
    useIt: 'Comparez avec les économies indiquées sur les écrans énergie.',
  },
  'kpi:cost': {
    title: 'Coût',
    what: 'Le montant d\u2019argent pour l\u2019élément affiché sur cette tuile.',
    steel: 'Chaque choix technique sur cette plateforme a un prix, et il est volontairement visible plutôt que caché.',
    useIt: 'Ouvrez la table des coûts pour voir le détail par service.',
  },
  'kpi:rate': {
    title: 'Cadence de traitement',
    what: 'Le nombre d\u2019enregistrements que le pipeline traite par unité de temps.',
    steel: 'Les données de capteurs arrivent en continu. Si le pipeline traite moins vite que les données n\u2019arrivent, les tableaux de bord prennent du retard sans le montrer.',
    useIt: 'Lisez-la avec la fraîcheur des données : une cadence saine mais des données anciennes signifient que quelque chose s\u2019est arrêté en amont.',
  },
  'kpi:fresh': {
    title: 'Fraîcheur des données',
    what: 'Le temps écoulé depuis l\u2019arrivée du point de données le plus récent.',
    steel: 'Un écran de salle de contrôle montrant les températures d\u2019hier est pire qu\u2019aucun écran, parce qu\u2019il paraît actuel.',
    useIt: 'Si cette durée augmente, traitez tous les autres chiffres du portail comme suspects jusqu\u2019à son rétablissement.',
  },
}
