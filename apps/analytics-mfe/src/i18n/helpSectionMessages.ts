import type { HelpCatalog } from '../components/help/helpTypes'

/**
 * Screen-level explanations reached from the info button next to the page
 * title. Where the rest of the help catalog explains a single control, these
 * answer the business question the whole screen exists for: how energy is
 * saved, how CO2 is cut, how failures are anticipated, how quality improves,
 * and how know-how is captured.
 *
 * Written for a reader with no steel-industry background. Keyed by
 * `section:<personaRoutes section id>` so a section without an entry simply
 * shows no button. Spread into `HELP_CATALOGS` in `helpCatalogs.ts`.
 */
export const HELP_SECTION: Record<string, HelpCatalog> = {
  en: {
    'section:command-center': {
      title: 'How this platform creates value',
      what: 'One screen carrying the five outcomes the platform is judged on: less energy, less CO2, fewer breakdowns, better quality, and know-how that stays in the company.',
      steel:
        'A steel plant leaks money in five places at once. It buys electricity at the wrong hour. It emits CO2 it then has to pay for. It stops without warning when the furnace lining gives up. It scraps coils that drifted out of specification. And it loses decades of operator judgement at every retirement. Each tile here is one of those five, measured against the pre-platform baseline so the gap is visible rather than claimed.',
      useIt:
        'Read the tiles as a triage list and open the screen behind whichever number moved. Nothing here writes to the plant: every figure is a proposal or an observation that a named human still has to approve.',
    },
    'section:energy-optimization': {
      title: 'How energy is optimised',
      what: 'A proposed re-timing of exactly the same production, moved into the cheapest and cleanest quarter-hours of the day.',
      steel:
        'The furnace is the largest single consumer on the site, and the price of electricity changes every 15 minutes: it can be several times higher at 18:00 than at 03:00. The platform never asks the plant to melt less steel. It solves a schedule that melts the same tonnage at better moments, and that also flattens the short peak the grid bills separately. It is the dishwasher-at-night argument: same dishes, smaller bill.',
      useIt:
        'Compare the proposed curve against the baseline, check that every constraint is still satisfied, then use the simulator to test your own assumptions before an energy manager approves the plan.',
    },
    'section:sustainability-compliance': {
      title: 'How CO2 is reduced',
      what: 'The emissions ledger, the carbon cost exposure that follows from it, and the audit trail behind every decision.',
      steel:
        'In Europe CO2 is a purchased input: every tonne emitted must be covered by an allowance with a market price. The carbon intensity of the grid also changes hour by hour, so moving consumption into a cleaner hour removes emissions without removing production. The same schedule that cuts the energy bill cuts the carbon bill. Be honest about the scope: this covers the electricity the plant buys, not the coal chemistry of the process itself.',
      useIt:
        'Follow one number from the ledger to the carbon exposure, then to the audit record showing which decision produced it, who approved it, and when.',
    },
    'section:furnace-health': {
      title: 'How failures are anticipated',
      what: 'How much life is left in the furnace lining, expressed as a range of days rather than a single confident date.',
      steel:
        'The inside of a furnace is protected by a refractory lining that 1,600 degree metal slowly eats away. Replace it too early and you throw away money and production; replace it too late and molten steel finds the shell, which is the accident nobody accepts. The platform measures how fast the lining is thinning and extrapolates that trend, the way brake-pad wear tells you roughly how many thousand kilometres are left. It returns a pessimistic, a likely and an optimistic date instead of pretending to know one.',
      useIt:
        'Plan the stop against the pessimistic date, not the likely one. Open the thermal explorer to see which zone is driving the wear, and the maintenance planner to place the outage where it costs the least production.',
    },
    'section:quality': {
      title: 'How steel quality improves',
      what: 'Batch-level quality scoring, the genealogy from charge to coil, and the control charts behind both.',
      steel:
        'Most quality losses are not sudden faults, they are slow drifts. The coiling temperature creeps down, the chemistry shifts by a fraction, the rolling forces stop being symmetrical. Each of those alone is still inside tolerance; the damage happens where they combine. Watching the combination instead of the individual limits buys roughly two hours of warning before the first out-of-specification coil is produced, which is enough time to correct instead of to scrap.',
      useIt:
        'Start from a batch that scored badly, walk its genealogy back to the charge that produced it, then check the control chart to see whether the pattern is a one-off or a trend.',
    },
    'section:knowledge-hub': {
      title: 'How know-how is captured',
      what: 'Approved operating procedures, and the consent-bound workflow that turns an expert\u2019s spoken experience into one of them.',
      steel:
        'A large share of what keeps a furnace running was never written down. It lives in the ears and hands of operators who have spent thirty years next to it, and it leaves the site with them when they retire. The platform records that experience with explicit consent, transcribes it, drafts a structured procedure with every claim traced back to a timestamp in the recording, and then refuses to publish it until a named human has reviewed and approved it. The machine writes the first draft; the expert stays the author.',
      useIt:
        'Search the approved procedures the way you would ask a colleague, and open the capture status view to see where each draft sits in the consent, review and approval chain.',
    },
  },
  fr: {
    'section:command-center': {
      title: 'Comment cette plateforme cr\u00e9e de la valeur',
      what: 'Un seul \u00e9cran portant les cinq r\u00e9sultats sur lesquels la plateforme est jug\u00e9e : moins d\u2019\u00e9nergie, moins de CO2, moins de pannes, une meilleure qualit\u00e9 et un savoir-faire qui reste dans l\u2019entreprise.',
      steel:
        'Une aci\u00e9rie perd de l\u2019argent \u00e0 cinq endroits \u00e0 la fois. Elle ach\u00e8te l\u2019\u00e9lectricit\u00e9 au mauvais moment. Elle \u00e9met du CO2 qu\u2019elle doit ensuite payer. Elle s\u2019arr\u00eate sans pr\u00e9venir quand le garnissage du four l\u00e2che. Elle met au rebut des bobines qui ont d\u00e9riv\u00e9 hors sp\u00e9cification. Et elle perd des d\u00e9cennies de jugement op\u00e9rateur \u00e0 chaque d\u00e9part en retraite. Chaque tuile ici correspond \u00e0 l\u2019un de ces cinq points, mesur\u00e9 par rapport \u00e0 la r\u00e9f\u00e9rence d\u2019avant la plateforme, pour que l\u2019\u00e9cart soit visible et non affirm\u00e9.',
      useIt:
        'Lisez les tuiles comme une liste de tri et ouvrez l\u2019\u00e9cran derri\u00e8re le chiffre qui a boug\u00e9. Rien ici n\u2019\u00e9crit dans l\u2019usine : chaque valeur est une proposition ou une observation qu\u2019un humain identifi\u00e9 doit encore approuver.',
    },
    'section:energy-optimization': {
      title: 'Comment l\u2019\u00e9nergie est optimis\u00e9e',
      what: 'Une proposition de red\u00e9coupage horaire de la m\u00eame production, d\u00e9plac\u00e9e vers les quarts d\u2019heure les moins chers et les moins carbon\u00e9s de la journ\u00e9e.',
      steel:
        'Le four est le plus gros consommateur du site, et le prix de l\u2019\u00e9lectricit\u00e9 change toutes les 15 minutes : il peut \u00eatre plusieurs fois plus \u00e9lev\u00e9 \u00e0 18 h qu\u2019\u00e0 3 h du matin. La plateforme ne demande jamais de fondre moins d\u2019acier. Elle r\u00e9sout un planning qui fond le m\u00eame tonnage \u00e0 de meilleurs moments, et qui aplatit au passage la pointe courte que le r\u00e9seau facture s\u00e9par\u00e9ment. C\u2019est l\u2019argument du lave-vaisselle la nuit : m\u00eame vaisselle, facture plus faible.',
      useIt:
        'Comparez la courbe propos\u00e9e \u00e0 la r\u00e9f\u00e9rence, v\u00e9rifiez que toutes les contraintes restent respect\u00e9es, puis utilisez le simulateur pour tester vos propres hypoth\u00e8ses avant qu\u2019un responsable \u00e9nergie n\u2019approuve le plan.',
    },
    'section:sustainability-compliance': {
      title: 'Comment le CO2 est r\u00e9duit',
      what: 'Le registre des \u00e9missions, l\u2019exposition au co\u00fbt carbone qui en d\u00e9coule, et la piste d\u2019audit derri\u00e8re chaque d\u00e9cision.',
      steel:
        'En Europe, le CO2 est un intrant achet\u00e9 : chaque tonne \u00e9mise doit \u00eatre couverte par un quota qui a un prix de march\u00e9. L\u2019intensit\u00e9 carbone du r\u00e9seau change elle aussi d\u2019heure en heure, donc d\u00e9placer la consommation vers une heure plus propre supprime des \u00e9missions sans supprimer de production. Le planning qui r\u00e9duit la facture d\u2019\u00e9nergie r\u00e9duit la facture carbone. Soyons honn\u00eates sur le p\u00e9rim\u00e8tre : cela couvre l\u2019\u00e9lectricit\u00e9 achet\u00e9e, pas la chimie du charbon du proc\u00e9d\u00e9 lui-m\u00eame.',
      useIt:
        'Suivez un chiffre du registre jusqu\u2019\u00e0 l\u2019exposition carbone, puis jusqu\u2019\u00e0 l\u2019enregistrement d\u2019audit qui montre quelle d\u00e9cision l\u2019a produit, qui l\u2019a approuv\u00e9e et quand.',
    },
    'section:furnace-health': {
      title: 'Comment les pannes sont anticip\u00e9es',
      what: 'La dur\u00e9e de vie restante du garnissage du four, exprim\u00e9e sous forme de plage de jours plut\u00f4t que d\u2019une date unique et p\u00e9remptoire.',
      steel:
        'L\u2019int\u00e9rieur d\u2019un four est prot\u00e9g\u00e9 par un garnissage r\u00e9fractaire que le m\u00e9tal \u00e0 1 600 degr\u00e9s ronge lentement. Le remplacer trop t\u00f4t, c\u2019est jeter de l\u2019argent et de la production ; le remplacer trop tard, c\u2019est laisser l\u2019acier liquide atteindre la coque, l\u2019accident que personne n\u2019accepte. La plateforme mesure la vitesse d\u2019amincissement et extrapole la tendance, comme l\u2019usure des plaquettes de frein indique le nombre de milliers de kilom\u00e8tres restants. Elle rend une date pessimiste, une date probable et une date optimiste, au lieu de faire semblant d\u2019en conna\u00eetre une seule.',
      useIt:
        'Planifiez l\u2019arr\u00eat sur la date pessimiste, pas sur la date probable. Ouvrez l\u2019explorateur thermique pour voir quelle zone provoque l\u2019usure, et le planificateur de maintenance pour placer l\u2019arr\u00eat l\u00e0 o\u00f9 il co\u00fbte le moins de production.',
    },
    'section:quality': {
      title: 'Comment la qualit\u00e9 de l\u2019acier s\u2019am\u00e9liore',
      what: 'La notation qualit\u00e9 par lot, la g\u00e9n\u00e9alogie de la charge \u00e0 la bobine, et les cartes de contr\u00f4le qui les sous-tendent.',
      steel:
        'La plupart des pertes de qualit\u00e9 ne sont pas des d\u00e9fauts soudains, ce sont des d\u00e9rives lentes. La temp\u00e9rature de bobinage baisse doucement, la chimie se d\u00e9cale d\u2019une fraction, les efforts de laminage cessent d\u2019\u00eatre sym\u00e9triques. Chacun de ces \u00e9carts reste dans la tol\u00e9rance ; le d\u00e9g\u00e2t na\u00eet de leur combinaison. Surveiller la combinaison plut\u00f4t que les limites individuelles donne environ deux heures d\u2019avance avant la premi\u00e8re bobine hors sp\u00e9cification, assez de temps pour corriger plut\u00f4t que pour mettre au rebut.',
      useIt:
        'Partez d\u2019un lot mal not\u00e9, remontez sa g\u00e9n\u00e9alogie jusqu\u2019\u00e0 la charge qui l\u2019a produit, puis regardez la carte de contr\u00f4le pour savoir si le motif est isol\u00e9 ou s\u2019il s\u2019agit d\u2019une tendance.',
    },
    'section:knowledge-hub': {
      title: 'Comment le savoir-faire est captur\u00e9',
      what: 'Les proc\u00e9dures approuv\u00e9es, et le circuit soumis au consentement qui transforme l\u2019exp\u00e9rience orale d\u2019un expert en l\u2019une d\u2019elles.',
      steel:
        'Une grande partie de ce qui fait tourner un four n\u2019a jamais \u00e9t\u00e9 \u00e9crite. Elle vit dans les oreilles et les mains d\u2019op\u00e9rateurs qui ont pass\u00e9 trente ans \u00e0 c\u00f4t\u00e9, et elle quitte le site avec eux au moment de la retraite. La plateforme enregistre cette exp\u00e9rience avec un consentement explicite, la transcrit, r\u00e9dige une proc\u00e9dure structur\u00e9e dont chaque affirmation renvoie \u00e0 un horodatage de l\u2019enregistrement, puis refuse de la publier tant qu\u2019un humain identifi\u00e9 ne l\u2019a pas relue et approuv\u00e9e. La machine \u00e9crit le premier jet ; l\u2019expert reste l\u2019auteur.',
      useIt:
        'Cherchez dans les proc\u00e9dures approuv\u00e9es comme vous interrogeriez un coll\u00e8gue, et ouvrez la vue d\u2019\u00e9tat de capture pour voir o\u00f9 en est chaque brouillon dans la cha\u00eene consentement, revue, approbation.',
    },
  },
  de: {
    'section:command-center': {
      title: 'Wie diese Plattform Wert schafft',
      what: 'Ein Bildschirm mit den f\u00fcnf Ergebnissen, an denen die Plattform gemessen wird: weniger Energie, weniger CO2, weniger Ausf\u00e4lle, bessere Qualit\u00e4t und Wissen, das im Unternehmen bleibt.',
      steel:
        'Ein Stahlwerk verliert an f\u00fcnf Stellen gleichzeitig Geld. Es kauft Strom zur falschen Stunde. Es emittiert CO2, das es anschlie\u00dfend bezahlen muss. Es steht unangek\u00fcndigt still, wenn die Ofenzustellung versagt. Es verschrottet Coils, die aus der Spezifikation gelaufen sind. Und es verliert bei jedem Renteneintritt jahrzehntelange Erfahrung. Jede Kachel steht f\u00fcr einen dieser f\u00fcnf Punkte, gemessen an der Ausgangslage vor der Plattform, damit die L\u00fccke sichtbar und nicht nur behauptet ist.',
      useIt:
        'Lesen Sie die Kacheln als Triage-Liste und \u00f6ffnen Sie den Bildschirm hinter der Zahl, die sich bewegt hat. Nichts hier schreibt in die Anlage: Jede Angabe ist ein Vorschlag oder eine Beobachtung, die ein namentlich benannter Mensch noch freigeben muss.',
    },
    'section:energy-optimization': {
      title: 'Wie Energie optimiert wird',
      what: 'Ein Vorschlag, dieselbe Produktion zeitlich zu verschieben, hinein in die g\u00fcnstigsten und saubersten Viertelstunden des Tages.',
      steel:
        'Der Ofen ist der gr\u00f6\u00dfte Einzelverbraucher des Standorts, und der Strompreis \u00e4ndert sich alle 15 Minuten: Um 18 Uhr kann er ein Vielfaches des Preises um 3 Uhr betragen. Die Plattform verlangt nie, weniger Stahl zu schmelzen. Sie l\u00f6st einen Fahrplan, der dieselbe Tonnage zu besseren Zeitpunkten schmilzt und nebenbei die kurze Lastspitze gl\u00e4ttet, die das Netz separat abrechnet. Es ist das Argument der Sp\u00fclmaschine bei Nacht: dasselbe Geschirr, kleinere Rechnung.',
      useIt:
        'Vergleichen Sie die vorgeschlagene Kurve mit der Ausgangslage, pr\u00fcfen Sie, dass jede Randbedingung weiterhin erf\u00fcllt ist, und testen Sie im Simulator Ihre eigenen Annahmen, bevor ein Energiemanager den Plan freigibt.',
    },
    'section:sustainability-compliance': {
      title: 'Wie CO2 gesenkt wird',
      what: 'Das Emissionsregister, die daraus folgende CO2-Kostenexposition und der Pr\u00fcfpfad hinter jeder Entscheidung.',
      steel:
        'In Europa ist CO2 ein zugekaufter Einsatzstoff: Jede emittierte Tonne muss durch ein Zertifikat mit Marktpreis gedeckt sein. Auch die CO2-Intensit\u00e4t des Netzes \u00e4ndert sich st\u00fcndlich, deshalb entfernt eine Verlagerung des Verbrauchs in eine sauberere Stunde Emissionen, ohne Produktion zu entfernen. Derselbe Fahrplan, der die Energierechnung senkt, senkt die CO2-Rechnung. Ehrlich zum Umfang: Dies betrifft den zugekauften Strom, nicht die Kohlechemie des Prozesses selbst.',
      useIt:
        'Verfolgen Sie eine Zahl vom Register zur CO2-Exposition und weiter zum Pr\u00fcfeintrag, der zeigt, welche Entscheidung sie erzeugt hat, wer sie freigegeben hat und wann.',
    },
    'section:furnace-health': {
      title: 'Wie Ausf\u00e4lle vorhergesehen werden',
      what: 'Wie viel Leben in der Ofenzustellung steckt, angegeben als Spanne von Tagen statt als einzelnes selbstsicheres Datum.',
      steel:
        'Das Innere eines Ofens ist durch eine feuerfeste Zustellung gesch\u00fctzt, die 1.600 Grad hei\u00dfes Metall langsam abtr\u00e4gt. Zu fr\u00fch ersetzt hei\u00dft Geld und Produktion wegwerfen; zu sp\u00e4t ersetzt hei\u00dft, dass fl\u00fcssiger Stahl den Mantel erreicht, und das ist der Unfall, den niemand akzeptiert. Die Plattform misst, wie schnell die Zustellung d\u00fcnner wird, und extrapoliert den Trend, so wie der Bremsbelagverschlei\u00df ungef\u00e4hr sagt, wie viele tausend Kilometer noch bleiben. Sie liefert ein pessimistisches, ein wahrscheinliches und ein optimistisches Datum, statt eines vorzut\u00e4uschen.',
      useIt:
        'Planen Sie den Stillstand auf das pessimistische Datum, nicht auf das wahrscheinliche. \u00d6ffnen Sie den Thermal Explorer, um die treibende Zone zu sehen, und den Wartungsplaner, um den Stillstand dort zu legen, wo er am wenigsten Produktion kostet.',
    },
    'section:quality': {
      title: 'Wie die Stahlqualit\u00e4t steigt',
      what: 'Qualit\u00e4tsbewertung je Charge, die Genealogie von der Charge bis zum Coil und die Regelkarten dahinter.',
      steel:
        'Die meisten Qualit\u00e4tsverluste sind keine pl\u00f6tzlichen Fehler, sondern langsame Driften. Die Haspeltemperatur sinkt schleichend, die Chemie verschiebt sich um einen Bruchteil, die Walzkr\u00e4fte sind nicht mehr symmetrisch. Jede Abweichung f\u00fcr sich liegt noch in der Toleranz; der Schaden entsteht in der Kombination. Die Kombination statt der Einzelgrenzen zu beobachten verschafft rund zwei Stunden Vorwarnung vor dem ersten Coil au\u00dferhalb der Spezifikation, genug Zeit zum Korrigieren statt zum Verschrotten.',
      useIt:
        'Beginnen Sie bei einer schlecht bewerteten Charge, verfolgen Sie ihre Genealogie zur\u00fcck zur erzeugenden Schmelze und pr\u00fcfen Sie dann die Regelkarte, ob das Muster ein Einzelfall oder ein Trend ist.',
    },
    'section:knowledge-hub': {
      title: 'Wie Erfahrungswissen gesichert wird',
      what: 'Freigegebene Betriebsanweisungen und der einwilligungsgebundene Ablauf, der die gesprochene Erfahrung einer Fachkraft in eine solche verwandelt.',
      steel:
        'Ein gro\u00dfer Teil dessen, was einen Ofen am Laufen h\u00e4lt, wurde nie aufgeschrieben. Es lebt in den Ohren und H\u00e4nden von Bedienern, die drei\u00dfig Jahre daneben gestanden haben, und es verl\u00e4sst den Standort mit ihnen. Die Plattform nimmt diese Erfahrung mit ausdr\u00fccklicher Einwilligung auf, transkribiert sie, entwirft eine strukturierte Anweisung, in der jede Aussage auf einen Zeitstempel der Aufnahme zur\u00fcckverweist, und weigert sich dann, sie zu ver\u00f6ffentlichen, bis ein namentlich benannter Mensch sie gepr\u00fcft und freigegeben hat. Die Maschine schreibt den ersten Entwurf; Autor bleibt die Fachkraft.',
      useIt:
        'Durchsuchen Sie die freigegebenen Anweisungen, wie Sie eine Kollegin fragen w\u00fcrden, und \u00f6ffnen Sie die Erfassungs\u00fcbersicht, um zu sehen, wo jeder Entwurf in der Kette aus Einwilligung, Pr\u00fcfung und Freigabe steht.',
    },
  },
  nl: {
    'section:command-center': {
      title: 'Hoe dit platform waarde levert',
      what: 'E\u00e9n scherm met de vijf uitkomsten waarop het platform wordt beoordeeld: minder energie, minder CO2, minder storingen, betere kwaliteit en kennis die in het bedrijf blijft.',
      steel:
        'Een staalfabriek verliest op vijf plaatsen tegelijk geld. Ze koopt stroom op het verkeerde uur. Ze stoot CO2 uit die ze daarna moet betalen. Ze valt onaangekondigd stil wanneer de ovenbekleding het begeeft. Ze schrapt coils die buiten specificatie zijn gedreven. En ze verliest bij elke pensionering decennia aan operatorervaring. Elke tegel hier staat voor \u00e9\u00e9n van die vijf, gemeten tegen de situatie v\u00f3\u00f3r het platform, zodat het verschil zichtbaar is en niet slechts beweerd.',
      useIt:
        'Lees de tegels als een triagelijst en open het scherm achter het getal dat bewoog. Niets hier schrijft naar de fabriek: elk cijfer is een voorstel of een waarneming die een met naam genoemde mens nog moet goedkeuren.',
    },
    'section:energy-optimization': {
      title: 'Hoe energie wordt geoptimaliseerd',
      what: 'Een voorstel om dezelfde productie te verschuiven naar de goedkoopste en schoonste kwartieren van de dag.',
      steel:
        'De oven is de grootste enkele verbruiker op de site, en de stroomprijs verandert elke 15 minuten: om 18 uur kan hij een veelvoud zijn van die om 3 uur. Het platform vraagt nooit om minder staal te smelten. Het lost een planning op die hetzelfde tonnage op betere momenten smelt, en die en passant de korte piek afvlakt die het net apart factureert. Het is het argument van de vaatwasser bij nacht: dezelfde vaat, lagere rekening.',
      useIt:
        'Vergelijk de voorgestelde curve met de referentie, controleer of elke randvoorwaarde nog wordt gehaald, en test in de simulator uw eigen aannames voordat een energiemanager het plan goedkeurt.',
    },
    'section:sustainability-compliance': {
      title: 'Hoe CO2 wordt verlaagd',
      what: 'Het emissieregister, de daaruit volgende koolstofkosten en het auditspoor achter elke beslissing.',
      steel:
        'In Europa is CO2 een ingekochte grondstof: elke uitgestoten ton moet gedekt zijn door een recht met een marktprijs. Ook de koolstofintensiteit van het net wisselt per uur, dus verbruik naar een schoner uur verplaatsen verwijdert uitstoot zonder productie te verwijderen. Dezelfde planning die de energierekening verlaagt, verlaagt de koolstofrekening. Eerlijk over de reikwijdte: dit betreft de ingekochte elektriciteit, niet de koolchemie van het proces zelf.',
      useIt:
        'Volg \u00e9\u00e9n getal van het register naar de koolstofblootstelling en verder naar het auditrecord dat toont welke beslissing het opleverde, wie het goedkeurde en wanneer.',
    },
    'section:furnace-health': {
      title: 'Hoe storingen worden voorzien',
      what: 'Hoeveel leven er nog in de ovenbekleding zit, uitgedrukt als een reeks dagen in plaats van \u00e9\u00e9n zelfverzekerde datum.',
      steel:
        'De binnenkant van een oven wordt beschermd door een vuurvaste bekleding die metaal van 1.600 graden langzaam wegvreet. Te vroeg vervangen kost geld en productie; te laat vervangen laat vloeibaar staal de mantel bereiken, en dat is het ongeval dat niemand accepteert. Het platform meet hoe snel de bekleding dunner wordt en trekt die trend door, zoals remblokslijtage ongeveer aangeeft hoeveel duizend kilometer er nog in zit. Het geeft een pessimistische, een waarschijnlijke en een optimistische datum in plaats van te doen alsof er \u00e9\u00e9n is.',
      useIt:
        'Plan de stop op de pessimistische datum, niet op de waarschijnlijke. Open de thermische verkenner om te zien welke zone de slijtage aandrijft, en de onderhoudsplanner om de stilstand te leggen waar hij de minste productie kost.',
    },
    'section:quality': {
      title: 'Hoe de staalkwaliteit verbetert',
      what: 'Kwaliteitsscores per batch, de genealogie van charge tot coil, en de regelkaarten daarachter.',
      steel:
        'De meeste kwaliteitsverliezen zijn geen plotselinge defecten maar trage driften. De haspeltemperatuur zakt geleidelijk, de chemie verschuift een fractie, de walskrachten zijn niet meer symmetrisch. Elk van die afwijkingen blijft op zich binnen de tolerantie; de schade ontstaat in de combinatie. De combinatie volgen in plaats van de losse grenzen levert ongeveer twee uur waarschuwing op v\u00f3\u00f3r de eerste coil buiten specificatie, genoeg tijd om te corrigeren in plaats van te schrappen.',
      useIt:
        'Begin bij een slecht scorende batch, volg de genealogie terug naar de charge die hem maakte, en kijk dan op de regelkaart of het patroon eenmalig is of een trend.',
    },
    'section:knowledge-hub': {
      title: 'Hoe vakkennis wordt vastgelegd',
      what: 'Goedgekeurde werkinstructies, en de op toestemming gebaseerde workflow die de gesproken ervaring van een expert daarin omzet.',
      steel:
        'Een groot deel van wat een oven draaiende houdt is nooit opgeschreven. Het leeft in de oren en handen van operators die er dertig jaar naast stonden, en het verlaat de site met hen bij hun pensioen. Het platform legt die ervaring met uitdrukkelijke toestemming vast, transcribeert ze, stelt een gestructureerde instructie op waarin elke bewering terugverwijst naar een tijdstempel in de opname, en weigert vervolgens te publiceren tot een met naam genoemde mens ze heeft nagekeken en goedgekeurd. De machine schrijft het eerste concept; de expert blijft de auteur.',
      useIt:
        'Doorzoek de goedgekeurde instructies zoals u een collega zou vragen, en open het overzicht van de vastleggingsstatus om te zien waar elk concept staat in de keten van toestemming, review en goedkeuring.',
    },
  },
  es: {
    'section:command-center': {
      title: 'C\u00f3mo esta plataforma genera valor',
      what: 'Una sola pantalla con los cinco resultados por los que se juzga la plataforma: menos energ\u00eda, menos CO2, menos aver\u00edas, mejor calidad y un saber hacer que se queda en la empresa.',
      steel:
        'Una acer\u00eda pierde dinero en cinco sitios a la vez. Compra electricidad a la hora equivocada. Emite CO2 que luego tiene que pagar. Se para sin aviso cuando cede el revestimiento del horno. Desecha bobinas que se han desviado de la especificaci\u00f3n. Y pierde d\u00e9cadas de criterio de operador en cada jubilaci\u00f3n. Cada tarjeta corresponde a uno de esos cinco puntos, medido contra la referencia anterior a la plataforma para que la diferencia se vea en lugar de afirmarse.',
      useIt:
        'Lea las tarjetas como una lista de triaje y abra la pantalla detr\u00e1s del n\u00famero que se ha movido. Nada de esto escribe en la planta: cada cifra es una propuesta o una observaci\u00f3n que a\u00fan debe aprobar una persona identificada.',
    },
    'section:energy-optimization': {
      title: 'C\u00f3mo se optimiza la energ\u00eda',
      what: 'Una propuesta para reprogramar exactamente la misma producci\u00f3n hacia los cuartos de hora m\u00e1s baratos y m\u00e1s limpios del d\u00eda.',
      steel:
        'El horno es el mayor consumidor individual de la planta, y el precio de la electricidad cambia cada 15 minutos: a las 18:00 puede ser varias veces el de las 03:00. La plataforma nunca pide fundir menos acero. Resuelve una programaci\u00f3n que funde el mismo tonelaje en mejores momentos y que, de paso, aplana el pico corto que la red factura aparte. Es el argumento del lavavajillas de noche: la misma vajilla, menos factura.',
      useIt:
        'Compare la curva propuesta con la referencia, compruebe que se siguen cumpliendo todas las restricciones y use el simulador para probar sus propias hip\u00f3tesis antes de que un responsable de energ\u00eda apruebe el plan.',
    },
    'section:sustainability-compliance': {
      title: 'C\u00f3mo se reduce el CO2',
      what: 'El registro de emisiones, la exposici\u00f3n al coste del carbono que se deriva de \u00e9l y la traza de auditor\u00eda detr\u00e1s de cada decisi\u00f3n.',
      steel:
        'En Europa el CO2 es un insumo comprado: cada tonelada emitida debe estar cubierta por un derecho con precio de mercado. La intensidad de carbono de la red tambi\u00e9n cambia hora a hora, as\u00ed que mover el consumo a una hora m\u00e1s limpia elimina emisiones sin eliminar producci\u00f3n. La misma programaci\u00f3n que baja la factura de energ\u00eda baja la factura de carbono. Seamos honestos con el alcance: esto cubre la electricidad comprada, no la qu\u00edmica del carb\u00f3n del propio proceso.',
      useIt:
        'Siga una cifra desde el registro hasta la exposici\u00f3n de carbono y despu\u00e9s hasta el registro de auditor\u00eda que muestra qu\u00e9 decisi\u00f3n la produjo, qui\u00e9n la aprob\u00f3 y cu\u00e1ndo.',
    },
    'section:furnace-health': {
      title: 'C\u00f3mo se anticipan las aver\u00edas',
      what: 'Cu\u00e1nta vida le queda al revestimiento del horno, expresada como un rango de d\u00edas en lugar de una \u00fanica fecha rotunda.',
      steel:
        'El interior de un horno est\u00e1 protegido por un revestimiento refractario que el metal a 1.600 grados va comiendo poco a poco. Sustituirlo demasiado pronto es tirar dinero y producci\u00f3n; sustituirlo demasiado tarde deja que el acero l\u00edquido alcance la carcasa, que es el accidente que nadie acepta. La plataforma mide a qu\u00e9 velocidad adelgaza el revestimiento y extrapola la tendencia, igual que el desgaste de las pastillas de freno indica m\u00e1s o menos cu\u00e1ntos miles de kil\u00f3metros quedan. Devuelve una fecha pesimista, una probable y una optimista en lugar de fingir que conoce una sola.',
      useIt:
        'Planifique la parada con la fecha pesimista, no con la probable. Abra el explorador t\u00e9rmico para ver qu\u00e9 zona impulsa el desgaste, y el planificador de mantenimiento para situar la parada donde cueste menos producci\u00f3n.',
    },
    'section:quality': {
      title: 'C\u00f3mo mejora la calidad del acero',
      what: 'La puntuaci\u00f3n de calidad por lote, la genealog\u00eda de la colada a la bobina y los gr\u00e1ficos de control que hay detr\u00e1s.',
      steel:
        'La mayor\u00eda de las p\u00e9rdidas de calidad no son fallos repentinos, son derivas lentas. La temperatura de bobinado baja poco a poco, la qu\u00edmica se desplaza una fracci\u00f3n, las fuerzas de laminaci\u00f3n dejan de ser sim\u00e9tricas. Cada desviaci\u00f3n por s\u00ed sola sigue dentro de tolerancia; el da\u00f1o nace de la combinaci\u00f3n. Vigilar la combinaci\u00f3n en vez de los l\u00edmites individuales da unas dos horas de aviso antes de la primera bobina fuera de especificaci\u00f3n, tiempo suficiente para corregir en lugar de desechar.',
      useIt:
        'Empiece por un lote con mala puntuaci\u00f3n, recorra su genealog\u00eda hasta la colada que lo produjo y consulte el gr\u00e1fico de control para ver si el patr\u00f3n es puntual o una tendencia.',
    },
    'section:knowledge-hub': {
      title: 'C\u00f3mo se captura el saber hacer',
      what: 'Los procedimientos aprobados y el circuito sujeto a consentimiento que convierte la experiencia hablada de un experto en uno de ellos.',
      steel:
        'Buena parte de lo que mantiene un horno en marcha nunca se escribi\u00f3. Vive en los o\u00eddos y las manos de operadores que han pasado treinta a\u00f1os a su lado, y se va de la planta con ellos cuando se jubilan. La plataforma graba esa experiencia con consentimiento expl\u00edcito, la transcribe, redacta un procedimiento estructurado en el que cada afirmaci\u00f3n remite a una marca de tiempo de la grabaci\u00f3n y despu\u00e9s se niega a publicarlo hasta que una persona identificada lo ha revisado y aprobado. La m\u00e1quina escribe el primer borrador; el experto sigue siendo el autor.',
      useIt:
        'Busque en los procedimientos aprobados como preguntar\u00eda a un compa\u00f1ero, y abra la vista de estado de captura para ver en qu\u00e9 punto de la cadena de consentimiento, revisi\u00f3n y aprobaci\u00f3n est\u00e1 cada borrador.',
    },
  },
}
