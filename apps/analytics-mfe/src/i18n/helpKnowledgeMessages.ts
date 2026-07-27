import type { HelpCatalog } from '../components/help/helpTypes'

/**
 * Help topics for the Knowledge Hub acquisition workflow.
 *
 * Satellite catalog, spread into `HELP_CATALOGS` in `helpCatalogs.ts`, so a
 * whole-file rewrite of any locale catalog cannot silently drop these entries.
 */
export const HELP_KNOWLEDGE: Record<string, HelpCatalog> = {
  en: {
    'knowledge:createEntry': {
      title: 'Capture a new procedure',
      what: 'Opens a form where an experienced operator records a piece of know-how as a draft procedure.',
      steel:
        'Much of what keeps a steel plant running safely lives only in the heads of people who have worked the furnace for thirty years. When they retire it walks out of the gate with them. This is where that knowledge gets written down while they are still here to explain it.',
      useIt:
        'Give the procedure a clear title, pick the plant and the equipment it applies to, then describe the steps. It is saved as a DRAFT — nothing you write here is treated as official until a reviewer approves it.',
    },
    'knowledge:consent': {
      title: 'Consent notice',
      what: 'A reminder that the person being recorded has agreed to it, and that they can ask to be erased later.',
      steel:
        'Capturing know-how usually means recording a real person talking. European privacy law (GDPR) says you may only do that with their permission, and that they can change their mind afterwards.',
      useIt:
        'Read it before you record. If the contributor later asks to be removed, the erasure request removes their personal identifiers while keeping the technical content the plant still needs.',
    },
    'knowledge:reviewAction': {
      title: 'Review actions',
      what: 'The approve and request-changes buttons a reviewer uses to move a draft forward or send it back.',
      steel:
        'A wrong procedure is more dangerous than no procedure. A second experienced person always checks the draft before it becomes something a colleague will follow at three in the morning.',
      useIt:
        'Only users with the reviewer role see these buttons. Approving moves the entry to APPROVED and makes it searchable; requesting changes sends it back to the author with your comment attached.',
    },
    'knowledge:pipeline': {
      title: 'Acquisition pipeline',
      what: 'A board showing every procedure and which stage of review it has reached.',
      steel:
        'Knowledge capture is not a single action, it is a short assembly line: someone writes it, someone checks it, then it becomes official. This board shows what is sitting at each station.',
      useIt:
        'Columns follow the workflow DRAFT to IN REVIEW to APPROVED. A column that keeps growing tells you the bottleneck — usually that reviewers have not had time.',
    },
    'knowledge:search': {
      title: 'Search the knowledge base',
      what: 'Finds approved procedures by words in their title, body or tags.',
      steel:
        'The point of writing know-how down is being able to find it in a hurry. An operator facing an unusual furnace reading should reach the right procedure in seconds, not browse a folder tree.',
      useIt:
        'Type any part of a procedure name, an equipment code such as BF-01, or a symptom. Results carry citations back to the source entry so you can check where an answer came from.',
    },
    'knowledge:demoSeed': {
      title: 'Load sample entries',
      what: 'Fills the knowledge base with a set of realistic example procedures.',
      steel:
        'So the screen can be explored with content in it, rather than looking at an empty list.',
      useIt:
        'Press once to load the samples. Everything it creates is synthetic demonstration data, clearly marked as such, and never mixed with real plant records.',
    },
    'knowledge:demoReset': {
      title: 'Reset the demonstration',
      what: 'Removes the sample entries and returns the knowledge base to its starting state.',
      steel:
        'Useful between demonstrations so the next person starts from the same clean position.',
      useIt:
        'Press to clear the samples. Only demonstration data is affected — it will ask you to confirm first.',
    },
  },
  fr: {
    'knowledge:createEntry': {
      title: 'Saisir une nouvelle proc\u00e9dure',
      what: 'Ouvre un formulaire o\u00f9 un op\u00e9rateur exp\u00e9riment\u00e9 consigne un savoir-faire sous forme de proc\u00e9dure provisoire.',
      steel:
        'Une grande partie de ce qui fait tourner une aci\u00e9rie en s\u00e9curit\u00e9 n\u2019existe que dans la t\u00eate de gens qui travaillent au haut fourneau depuis trente ans. \u00c0 leur d\u00e9part en retraite, ce savoir franchit le portail avec eux. C\u2019est ici qu\u2019on l\u2019\u00e9crit pendant qu\u2019ils sont encore l\u00e0 pour l\u2019expliquer.',
      useIt:
        'Donnez un titre clair, choisissez le site et l\u2019\u00e9quipement concern\u00e9s, puis d\u00e9crivez les \u00e9tapes. L\u2019entr\u00e9e est enregistr\u00e9e en BROUILLON : rien de ce que vous \u00e9crivez ici n\u2019est officiel tant qu\u2019un relecteur ne l\u2019a pas approuv\u00e9.',
    },
    'knowledge:consent': {
      title: 'Avis de consentement',
      what: 'Un rappel que la personne enregistr\u00e9e a donn\u00e9 son accord et qu\u2019elle peut demander son effacement plus tard.',
      steel:
        'Recueillir un savoir-faire suppose g\u00e9n\u00e9ralement d\u2019enregistrer une personne r\u00e9elle qui parle. Le droit europ\u00e9en de la vie priv\u00e9e (RGPD) ne l\u2019autorise qu\u2019avec son accord, et lui permet de changer d\u2019avis ensuite.',
      useIt:
        'Lisez-le avant d\u2019enregistrer. Si le contributeur demande ensuite son retrait, la demande d\u2019effacement supprime ses identifiants personnels tout en conservant le contenu technique dont l\u2019usine a besoin.',
    },
    'knowledge:reviewAction': {
      title: 'Actions de relecture',
      what: 'Les boutons d\u2019approbation et de demande de modification permettant de faire avancer un brouillon ou de le renvoyer.',
      steel:
        'Une proc\u00e9dure erron\u00e9e est plus dangereuse que pas de proc\u00e9dure du tout. Une deuxi\u00e8me personne exp\u00e9riment\u00e9e v\u00e9rifie toujours le brouillon avant qu\u2019un coll\u00e8gue ne l\u2019applique \u00e0 trois heures du matin.',
      useIt:
        'Seuls les utilisateurs ayant le r\u00f4le de relecteur voient ces boutons. L\u2019approbation fait passer l\u2019entr\u00e9e en APPROUV\u00c9E et la rend consultable ; la demande de modification la renvoie \u00e0 l\u2019auteur avec votre commentaire.',
    },
    'knowledge:pipeline': {
      title: 'Cha\u00eene d\u2019acquisition',
      what: 'Un tableau montrant chaque proc\u00e9dure et l\u2019\u00e9tape de relecture qu\u2019elle a atteinte.',
      steel:
        'La capture du savoir n\u2019est pas un geste unique, c\u2019est une petite cha\u00eene de montage : quelqu\u2019un r\u00e9dige, quelqu\u2019un v\u00e9rifie, puis cela devient officiel. Ce tableau montre ce qui attend \u00e0 chaque poste.',
      useIt:
        'Les colonnes suivent le flux BROUILLON, EN RELECTURE, APPROUV\u00c9E. Une colonne qui gonfle indique le goulot d\u2019\u00e9tranglement, le plus souvent le manque de temps des relecteurs.',
    },
    'knowledge:search': {
      title: 'Rechercher dans la base de connaissances',
      what: 'Retrouve les proc\u00e9dures approuv\u00e9es par mots du titre, du texte ou des \u00e9tiquettes.',
      steel:
        'L\u2019int\u00e9r\u00eat d\u2019\u00e9crire un savoir-faire est de pouvoir le retrouver dans l\u2019urgence. Face \u00e0 une mesure inhabituelle, un op\u00e9rateur doit atteindre la bonne proc\u00e9dure en quelques secondes.',
      useIt:
        'Tapez une partie du nom d\u2019une proc\u00e9dure, un code d\u2019\u00e9quipement comme BF-01, ou un sympt\u00f4me. Les r\u00e9sultats portent des citations vers l\u2019entr\u00e9e d\u2019origine afin de v\u00e9rifier d\u2019o\u00f9 vient une r\u00e9ponse.',
    },
    'knowledge:demoSeed': {
      title: 'Charger des exemples',
      what: 'Remplit la base de connaissances avec un jeu de proc\u00e9dures d\u2019exemple r\u00e9alistes.',
      steel:
        'Pour que l\u2019\u00e9cran puisse \u00eatre explor\u00e9 avec du contenu, plut\u00f4t qu\u2019une liste vide.',
      useIt:
        'Appuyez une fois pour charger les exemples. Tout ce qui est cr\u00e9\u00e9 est une donn\u00e9e de d\u00e9monstration synth\u00e9tique, clairement identifi\u00e9e, jamais m\u00eal\u00e9e aux dossiers r\u00e9els de l\u2019usine.',
    },
    'knowledge:demoReset': {
      title: 'R\u00e9initialiser la d\u00e9monstration',
      what: 'Supprime les exemples et remet la base de connaissances dans son \u00e9tat initial.',
      steel:
        'Utile entre deux d\u00e9monstrations pour que la personne suivante reparte du m\u00eame point.',
      useIt:
        'Appuyez pour effacer les exemples. Seules les donn\u00e9es de d\u00e9monstration sont concern\u00e9es ; une confirmation vous sera demand\u00e9e.',
    },
  },
  de: {
    'knowledge:createEntry': {
      title: 'Neue Arbeitsanweisung erfassen',
      what: '\u00d6ffnet ein Formular, in dem eine erfahrene Fachkraft ihr Wissen als Entwurf einer Arbeitsanweisung festh\u00e4lt.',
      steel:
        'Vieles von dem, was ein Stahlwerk sicher am Laufen h\u00e4lt, steckt allein in den K\u00f6pfen von Menschen, die seit drei\u00dfig Jahren am Hochofen arbeiten. Mit ihrem Ruhestand geht es zum Werkstor hinaus. Hier wird es aufgeschrieben, solange sie es noch erkl\u00e4ren k\u00f6nnen.',
      useIt:
        'Vergeben Sie einen klaren Titel, w\u00e4hlen Sie Werk und Anlage aus und beschreiben Sie die Schritte. Der Eintrag wird als ENTWURF gespeichert: Nichts davon gilt als verbindlich, bevor ein Pr\u00fcfer es freigegeben hat.',
    },
    'knowledge:consent': {
      title: 'Einwilligungshinweis',
      what: 'Ein Hinweis darauf, dass die aufgezeichnete Person zugestimmt hat und ihre L\u00f6schung sp\u00e4ter verlangen kann.',
      steel:
        'Wissen zu erfassen bedeutet meist, eine reale Person beim Sprechen aufzunehmen. Das europ\u00e4ische Datenschutzrecht (DSGVO) erlaubt das nur mit ihrer Zustimmung, und sie darf es sich sp\u00e4ter anders \u00fcberlegen.',
      useIt:
        'Lesen Sie ihn vor der Aufnahme. Verlangt die beitragende Person sp\u00e4ter ihre Entfernung, l\u00f6scht der Erasure-Antrag ihre pers\u00f6nlichen Kennzeichen und bewahrt zugleich den fachlichen Inhalt, den das Werk weiter braucht.',
    },
    'knowledge:reviewAction': {
      title: 'Pr\u00fcfaktionen',
      what: 'Die Schaltfl\u00e4chen zum Freigeben oder Zur\u00fcckweisen, mit denen ein Pr\u00fcfer einen Entwurf weiterbewegt.',
      steel:
        'Eine falsche Anweisung ist gef\u00e4hrlicher als gar keine. Eine zweite erfahrene Person pr\u00fcft den Entwurf stets, bevor eine Kollegin ihm um drei Uhr nachts folgt.',
      useIt:
        'Nur Benutzer mit der Pr\u00fcferrolle sehen diese Schaltfl\u00e4chen. Die Freigabe setzt den Eintrag auf FREIGEGEBEN und macht ihn durchsuchbar; eine \u00c4nderungsanforderung geht mit Ihrem Kommentar an die Verfasserin zur\u00fcck.',
    },
    'knowledge:pipeline': {
      title: 'Erfassungskette',
      what: 'Eine Tafel, die jede Arbeitsanweisung und ihren Pr\u00fcfstand zeigt.',
      steel:
        'Wissenserfassung ist kein einzelner Handgriff, sondern ein kurzes Flie\u00dfband: Jemand schreibt, jemand pr\u00fcft, dann wird es verbindlich. Diese Tafel zeigt, was an welcher Station liegt.',
      useIt:
        'Die Spalten folgen dem Ablauf ENTWURF, IN PR\u00dcFUNG, FREIGEGEBEN. Eine st\u00e4ndig wachsende Spalte zeigt den Engpass, meist fehlende Zeit der Pr\u00fcfer.',
    },
    'knowledge:search': {
      title: 'Wissensbasis durchsuchen',
      what: 'Findet freigegebene Anweisungen \u00fcber W\u00f6rter in Titel, Text oder Schlagworten.',
      steel:
        'Wissen aufzuschreiben lohnt nur, wenn man es in der Eile wiederfindet. Wer vor einem ungew\u00f6hnlichen Ofenwert steht, muss die richtige Anweisung in Sekunden erreichen.',
      useIt:
        'Geben Sie einen Teil eines Anweisungsnamens, einen Anlagencode wie BF-01 oder ein Symptom ein. Die Treffer tragen Quellenangaben zum Ursprungseintrag, damit Sie pr\u00fcfen k\u00f6nnen, woher eine Antwort stammt.',
    },
    'knowledge:demoSeed': {
      title: 'Beispieleintr\u00e4ge laden',
      what: 'F\u00fcllt die Wissensbasis mit realistischen Beispielanweisungen.',
      steel:
        'Damit der Bildschirm mit Inhalt erkundet werden kann statt mit einer leeren Liste.',
      useIt:
        'Einmal dr\u00fccken, um die Beispiele zu laden. Alles Erzeugte sind synthetische Demonstrationsdaten, deutlich gekennzeichnet und nie mit echten Werksunterlagen vermischt.',
    },
    'knowledge:demoReset': {
      title: 'Demonstration zur\u00fccksetzen',
      what: 'Entfernt die Beispieleintr\u00e4ge und stellt den Ausgangszustand der Wissensbasis wieder her.',
      steel:
        'N\u00fctzlich zwischen zwei Vorf\u00fchrungen, damit die n\u00e4chste Person am selben Punkt beginnt.',
      useIt:
        'Dr\u00fccken, um die Beispiele zu l\u00f6schen. Betroffen sind nur Demonstrationsdaten; Sie werden zuvor um Best\u00e4tigung gebeten.',
    },
  },
  nl: {
    'knowledge:createEntry': {
      title: 'Een nieuwe procedure vastleggen',
      what: 'Opent een formulier waarin een ervaren operator vakkennis vastlegt als een voorlopige procedure.',
      steel:
        'Veel van wat een staalfabriek veilig draaiende houdt, zit alleen in het hoofd van mensen die al dertig jaar aan de hoogoven werken. Bij hun pensioen loopt die kennis met hen de poort uit. Hier wordt ze opgeschreven terwijl zij er nog zijn om ze uit te leggen.',
      useIt:
        'Geef een duidelijke titel, kies de vestiging en de installatie, en beschrijf de stappen. De invoer wordt bewaard als CONCEPT: niets ervan geldt als offici\u00eble instructie voordat een beoordelaar het heeft goedgekeurd.',
    },
    'knowledge:consent': {
      title: 'Toestemmingsmelding',
      what: 'Een herinnering dat de opgenomen persoon toestemming gaf en later om verwijdering kan vragen.',
      steel:
        'Kennis vastleggen betekent meestal een echte persoon opnemen die spreekt. De Europese privacywet (AVG) staat dat alleen toe met hun toestemming, en zij mogen zich later bedenken.',
      useIt:
        'Lees dit v\u00f3\u00f3r de opname. Vraagt de bijdrager later om verwijdering, dan wist het wisverzoek hun persoonsgegevens terwijl de technische inhoud die de fabriek nodig heeft bewaard blijft.',
    },
    'knowledge:reviewAction': {
      title: 'Beoordelingsacties',
      what: 'De knoppen om goed te keuren of wijzigingen te vragen, waarmee een beoordelaar een concept verderhelpt.',
      steel:
        'Een foute procedure is gevaarlijker dan geen procedure. Een tweede ervaren persoon controleert het concept altijd voordat een collega het om drie uur \u2019s nachts volgt.',
      useIt:
        'Alleen gebruikers met de beoordelaarsrol zien deze knoppen. Goedkeuren zet de invoer op GOEDGEKEURD en maakt ze doorzoekbaar; wijzigingen vragen stuurt ze met uw opmerking terug naar de auteur.',
    },
    'knowledge:pipeline': {
      title: 'Verwervingsketen',
      what: 'Een bord dat elke procedure toont en in welke beoordelingsfase ze zit.',
      steel:
        'Kennis vastleggen is geen enkele handeling maar een korte lopende band: iemand schrijft, iemand controleert, daarna wordt het offici\u00eble instructie. Dit bord toont wat bij elke post ligt.',
      useIt:
        'De kolommen volgen de stroom CONCEPT, IN BEOORDELING, GOEDGEKEURD. Een kolom die blijft groeien wijst het knelpunt aan, meestal tijdgebrek bij de beoordelaars.',
    },
    'knowledge:search': {
      title: 'De kennisbank doorzoeken',
      what: 'Vindt goedgekeurde procedures op woorden in titel, tekst of labels.',
      steel:
        'Kennis opschrijven heeft alleen zin als je ze in de haast terugvindt. Wie voor een ongewone ovenmeting staat, moet de juiste procedure in seconden bereiken.',
      useIt:
        'Typ een deel van een proceduretitel, een installatiecode zoals BF-01, of een symptoom. Resultaten dragen bronverwijzingen naar de oorspronkelijke invoer zodat u kunt nagaan waar een antwoord vandaan komt.',
    },
    'knowledge:demoSeed': {
      title: 'Voorbeelden laden',
      what: 'Vult de kennisbank met een reeks realistische voorbeeldprocedures.',
      steel:
        'Zodat het scherm met inhoud verkend kan worden in plaats van met een lege lijst.',
      useIt:
        'Druk \u00e9\u00e9nmaal om de voorbeelden te laden. Alles wat wordt aangemaakt is synthetische demonstratiedata, duidelijk gemarkeerd en nooit vermengd met echte fabrieksdossiers.',
    },
    'knowledge:demoReset': {
      title: 'Demonstratie herstellen',
      what: 'Verwijdert de voorbeelden en zet de kennisbank terug in haar begintoestand.',
      steel:
        'Handig tussen twee demonstraties, zodat de volgende persoon vanaf hetzelfde punt begint.',
      useIt:
        'Druk om de voorbeelden te wissen. Alleen demonstratiedata wordt geraakt; er wordt eerst om bevestiging gevraagd.',
    },
  },
  es: {
    'knowledge:createEntry': {
      title: 'Registrar un procedimiento nuevo',
      what: 'Abre un formulario donde un operador con experiencia deja por escrito su saber hacer como procedimiento provisional.',
      steel:
        'Buena parte de lo que mantiene una acer\u00eda funcionando con seguridad vive solo en la cabeza de quienes llevan treinta a\u00f1os en el alto horno. Al jubilarse, ese saber cruza la puerta con ellos. Aqu\u00ed se escribe mientras todav\u00eda est\u00e1n para explicarlo.',
      useIt:
        'Ponga un t\u00edtulo claro, elija la planta y el equipo, y describa los pasos. Se guarda como BORRADOR: nada de lo que escriba aqu\u00ed es oficial hasta que un revisor lo apruebe.',
    },
    'knowledge:consent': {
      title: 'Aviso de consentimiento',
      what: 'Un recordatorio de que la persona grabada dio su permiso y de que puede pedir su supresi\u00f3n m\u00e1s adelante.',
      steel:
        'Capturar saber hacer suele implicar grabar a una persona real hablando. La ley europea de privacidad (RGPD) solo lo permite con su permiso, y le deja cambiar de opini\u00f3n despu\u00e9s.',
      useIt:
        'L\u00e9alo antes de grabar. Si m\u00e1s tarde el colaborador pide ser retirado, la solicitud de supresi\u00f3n elimina sus identificadores personales y conserva el contenido t\u00e9cnico que la planta sigue necesitando.',
    },
    'knowledge:reviewAction': {
      title: 'Acciones de revisi\u00f3n',
      what: 'Los botones de aprobar y solicitar cambios que usa un revisor para avanzar o devolver un borrador.',
      steel:
        'Un procedimiento equivocado es m\u00e1s peligroso que ninguno. Una segunda persona con experiencia siempre revisa el borrador antes de que un compa\u00f1ero lo siga a las tres de la madrugada.',
      useIt:
        'Solo los usuarios con rol de revisor ven estos botones. Aprobar pasa la entrada a APROBADO y la hace consultable; solicitar cambios la devuelve al autor con su comentario.',
    },
    'knowledge:pipeline': {
      title: 'Cadena de adquisici\u00f3n',
      what: 'Un tablero que muestra cada procedimiento y la fase de revisi\u00f3n en que se encuentra.',
      steel:
        'Capturar conocimiento no es un solo gesto sino una peque\u00f1a cadena de montaje: alguien redacta, alguien comprueba, y luego pasa a ser oficial. Este tablero muestra qu\u00e9 hay en cada puesto.',
      useIt:
        'Las columnas siguen el flujo BORRADOR, EN REVISI\u00d3N, APROBADO. Una columna que no deja de crecer se\u00f1ala el cuello de botella, casi siempre falta de tiempo de los revisores.',
    },
    'knowledge:search': {
      title: 'Buscar en la base de conocimiento',
      what: 'Encuentra procedimientos aprobados por palabras del t\u00edtulo, del texto o de las etiquetas.',
      steel:
        'Escribir el saber hacer solo sirve si se encuentra con prisa. Ante una lectura inusual del horno, un operador debe llegar al procedimiento correcto en segundos.',
      useIt:
        'Escriba parte del nombre de un procedimiento, un c\u00f3digo de equipo como BF-01, o un s\u00edntoma. Los resultados llevan citas a la entrada de origen para comprobar de d\u00f3nde sale una respuesta.',
    },
    'knowledge:demoSeed': {
      title: 'Cargar entradas de ejemplo',
      what: 'Rellena la base de conocimiento con procedimientos de ejemplo realistas.',
      steel:
        'Para poder explorar la pantalla con contenido en vez de una lista vac\u00eda.',
      useIt:
        'Pulse una vez para cargar los ejemplos. Todo lo que crea son datos sint\u00e9ticos de demostraci\u00f3n, claramente marcados y nunca mezclados con registros reales de la planta.',
    },
    'knowledge:demoReset': {
      title: 'Reiniciar la demostraci\u00f3n',
      what: 'Elimina las entradas de ejemplo y devuelve la base de conocimiento a su estado inicial.',
      steel:
        '\u00datil entre demostraciones para que la siguiente persona empiece desde el mismo punto.',
      useIt:
        'Pulse para borrar los ejemplos. Solo afecta a los datos de demostraci\u00f3n; se le pedir\u00e1 confirmaci\u00f3n antes.',
    },
  },
}
