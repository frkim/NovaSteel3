import type { HelpCatalog } from '../components/help/helpTypes'

export const HELP_NL: HelpCatalog = {
  // ---------------------------------------------------------------- generic
  'generic.kpi': {
    title: 'Kerngetal',
    what: 'Een tegel toont één meting, de trendpijl en de vergelijking met het doel.',
    steel:
      'Een staalfabriek draait op een klein aantal cijfers. Door ze naast elkaar te zetten ziet een ploegleider in enkele seconden de toestand van de fabriek, zonder rapporten te lezen.',
    useIt: 'Licht een tegel op wanneer u er met de muis overheen gaat, dan kunt u erop klikken om de details achter het cijfer te openen.',
  },
  'generic.chart': {
    title: 'Grafiek',
    what: 'Een beeld van hoe een meting door de tijd veranderde of hoe zij over delen van de fabriek is verdeeld.',
    steel:
      'Losse cijfers verbergen het verhaal. Een oven met een veilige gemiddelde temperatuur kan toch gevaarlijke pieken hebben, en alleen een grafiek toont die.',
    useIt: 'Beweeg over een punt voor de exacte waarde. Grafieken in een paneel kunnen worden vergroot met de maximaliseerknop op de tabbalk.',
  },
  'generic.table': {
    title: 'Gegevenstabel',
    what: 'De afzonderlijke records achter de samenvattende cijfers, één per rij.',
    steel: 'Als een cijfer verkeerd lijkt, vindt u in de tabel de specifieke batch, sensor of werkorder die het veroorzaakte.',
    useIt: 'Klik op een kolomkop om te sorteren, gebruik de kopbesturingen om te filteren en het zoekvak om tekst overal in de tabel te vinden.',
  },
  'generic.tableRow': {
    title: 'Eén record',
    what: 'Een enkel item: één batch, één sensormeting, één werkorder of één waarschuwing.',
    steel: 'Alles wat in de fabriek gebeurt, wordt uiteindelijk vastgelegd als zo een record. Dat maakt een audit mogelijk.',
    useIt: 'Waar een rij klikbaar is, opent die de volledige details van dat item.',
  },
  'generic.tableHeader': {
    title: 'Kolomkop',
    what: 'De naam van een kolom en de besturing waarmee de tabel daarop sorteert en filtert.',
    steel: 'Sorteren op risico of datum is hoe een ingenieur een lange lijst omzet in een korte lijst van zaken om vandaag aan te pakken.',
    useIt: 'Klik eenmaal om oplopend te sorteren, en nogmaals voor aflopend. Filterbesturingen beperken de tabel tot alleen passende rijen.',
  },
  'generic.panel': {
    title: 'Werkpaneel',
    what: 'Een verplaatsbaar deel van het scherm. Panelen kunnen via hun tab naar elke rand worden gesleept, vergroot of gestapeld.',
    steel: 'Operators in de controlekamer letten niet allemaal op hetzelfde. De indeling past zich daarom aan de persoon aan, niet andersom.',
    useIt: 'Sleep de tab om opnieuw in te delen. Indeling herstellen in de kop zet alles terug.',
  },
  'generic.dockTab': {
    title: 'Paneeltab',
    what: 'De greep van een paneel. Zij geeft het paneel een naam en laat u het verplaatsen.',
    steel: 'Panelen die altijd zichtbaar moeten blijven, hebben geen sluitknop. Zo kan een kritieke weergave niet per ongeluk verdwijnen.',
    useIt: 'Sleep de tab om het paneel te verplaatsen, of klik op maximaliseren om het de werkruimte te laten vullen.',
  },
  'generic.button': {
    title: 'Actie',
    what: 'Een besturing die wijzigt wat wordt getoond of de platformsoftware vraagt iets te doen.',
    steel:
      'Alles wat het gedrag van de fabriek kan veranderen, is hier altijd slechts een voorstel. Een mens keurt het nog goed voordat het de apparatuur bereikt.',
    useIt: 'Beweeg erover voor een tooltip die beschrijft wat de actie doet.',
  },

  // ------------------------------------------------------------ chart types
  'chart.line': {
    title: 'Lijngrafiek',
    what: 'De tijd loopt van links naar rechts, de meting van onder naar boven. De lijn verbindt opeenvolgende metingen.',
    steel: 'Staalprocessen drijven langzaam weg, dus de helling telt meer dan één meting. Een stijgende lijn is een vroege waarschuwing.',
    useIt: 'Let op plotselinge sprongen en op een helling die dezelfde kant op blijft gaan.',
  },
  'chart.area': {
    title: 'Vlakgrafiek',
    what: 'Een lijngrafiek met de ruimte onder de lijn gevuld, waardoor totalen makkelijker te vergelijken zijn.',
    steel: 'Nuttig voor hoeveelheden die optellen, zoals verbruikte energie of uitgestoten emissies tijdens een ploeg.',
    useIt: 'Vergelijk de grootte van de gevulde vlakken, niet de hoogte van de lijn.',
  },
  'chart.bar': {
    title: 'Staafdiagram',
    what: 'Eén staaf per categorie. Hoger betekent meer.',
    steel: 'Goed om hoogovens, staalsoorten of ploegen in één oogopslag met elkaar te vergelijken.',
    useIt: 'Zoek de uitschieterstaaf. Daar zit meestal het probleem of de kans.',
  },
  'chart.heatmap': {
    title: 'Warmtekaart',
    what: 'Een raster waarin kleur voor een waarde staat. Donkere of hetere kleuren betekenen hogere metingen.',
    steel:
      'Een hoogoven is bekleed met honderden sensoren. Een warmtekaart toont ze allemaal tegelijk, zodat een heet punt op de mantel direct opvalt.',
    useIt: 'Zoek naar geïsoleerde heldere cellen. Eén hete cel tussen koele cellen betekent meestal een lokaal slijtageprobleem.',
  },
  'chart.gauge': {
    title: 'Meter',
    what: 'Een wijzerplaat die één waarde tegenover het veilige bereik toont.',
    steel: 'Dit lijkt op de analoge instrumenten die operators al tientallen jaren op de fabrieksvloer gebruiken. Op een controlescherm hoeft dit weinig uitleg.',
    useIt: 'De gekleurde band vertelt of de huidige waarde comfortabel, randvoorwaardelijk of buiten de grenzen is.',
  },
  'chart.control': {
    title: 'Regelkaart',
    what: 'Een tijdgrafiek met een middenlijn voor het doel en twee buitenlijnen voor het acceptabele bereik.',
    steel:
      'Dit is het klassieke kwaliteitsinstrument. Een proces dat binnen de buitenlijnen blijft, is voorspelbaar; een punt erbuiten betekent dat er iets veranderde en onderzocht moet worden.',
    useIt: 'Let op punten buiten de grenzen en op lange reeksen punten aan één kant van de middenlijn.',
  },
  'chart.pareto': {
    title: 'Pareto-grafiek',
    what: 'Staven gesorteerd van groot naar klein, met een stijgende lijn die het lopende totaal toont.',
    steel:
      'De meeste uitval en nabewerking komen door een klein aantal oorzaken. De eerste twee of drie staven oplossen neemt meestal het grootste deel van het verlies weg.',
    useIt: 'Zoek waar de lijn 80 procent kruist. De staven links daarvan zijn uw prioriteitenlijst.',
  },
  'chart.donut': {
    title: 'Donutgrafiek',
    what: 'Een ring verdeeld in stukken, elk stuk een aandeel van het geheel.',
    steel: 'Gebruikt voor verdelingen zoals waar emissies vandaan komen, wanneer een stuk makkelijker te beoordelen is dan een percentage in een tabel.',
    useIt: 'Vergelijk de groottes van stukken; beweeg erover voor het exacte aandeel.',
  },
  'chart.gantt': {
    title: 'Planningsstaafdiagram',
    what: 'Elke staaf is een activiteit, geplaatst en geschaald op basis van startmoment en duur.',
    steel:
      'Ovenherbekledingen en onderhoudsstops moeten tussen productiecampagnes passen. Op één tijdlijn zien planners hoe ze botsingen vermijden.',
    useIt: 'Zoek naar overlappingen en naar gaten die een onderhoudsvenster kunnen opnemen.',
  },
  'chart.priceLoad': {
    title: 'Prijs- en belastingsgrafiek',
    what: 'Twee zaken op één tijdlijn: de elektriciteitsprijs en hoeveel vermogen de fabriek wil afnemen.',
    steel:
      'Elektriciteit is een van de grootste kosten in staalmaken en de prijs verandert elk uur. Energie-intensief werk doen wanneer de prijs laag is, bespaart echt geld.',
    useIt: 'Controleer of de hoge belastingsstaven onder de lage punten van de prijslijn staan.',
  },
  'chart.bullet': {
    title: 'Voortgangsbalk',
    what: 'Een balk die toont waar de huidige waarde tussen nul en het doel ligt.',
    steel: 'Geeft snel een gevoel voor hoeveel van een afspraak, zoals een jaarlijks emissiebudget, al is gebruikt.',
    useIt: 'De markering op de balk is het doel; het gevulde deel is waar u werkelijk staat.',
  },
  'chart.sparkline': {
    title: 'Minitrend',
    what: 'Een heel kleine lijngrafiek zonder assen, die alleen de recente vorm van de meting toont.',
    steel: 'Past in een kerngetaltegel, zodat u de richting ziet zonder het samenvattingsscherm te verlaten.',
    useIt: 'Lees de vorm, niet de waarden. Klik op de tegel voor de volledige grafiek.',
  },

  // ------------------------------------------------------- executive layer
  'kpi:energy': {
    title: 'Energie-intensiteit',
    what: 'Elektriciteit en brandstof gebruikt om één ton staal te maken, in kilowattuur per ton.',
    steel:
      'Staal maken betekent ijzererts of schroot verhitten tot ongeveer 1.600 graden Celsius. Energie is daarom zowel de grootste kostenpost als de grootste bron van emissies.',
    useIt: 'Vergelijk met de doellijn. Een daling hier werkt direct door in kosten en koolstof.',
  },
  'kpi:co2': {
    title: 'Kooldioxide-emissies',
    what: 'Ton CO2 uitgestoten, of de vermindering ten opzichte van de referentieperiode.',
    steel:
      'Staal is goed voor ongeveer zeven procent van de wereldwijde CO2. In Europa moet een fabriek voor elke uitgestoten ton een emissierecht inleveren, dus aan dit cijfer hangt een prijs.',
    useIt: 'Lees dit samen met energie-intensiteit. De meeste verminderingen komen door minder of schonere elektriciteit.',
  },
  'kpi:yield': {
    title: 'Rendement hoge kwaliteit',
    what: 'Het aandeel van de productie dat meteen aan de premium specificatie voldoet.',
    steel:
      'Staal dat niet aan de specificatie voldoet, is geen afval: het wordt opnieuw gesmolten. Maar opnieuw smelten gebruikt de energie twee keer, dus rendement is eigenlijk ook een verborgen energie- en kostenmaat.',
    useIt: 'Een daling hier verschijnt meestal kort daarna in de kwaliteitsschermen.',
  },
  'kpi:warning': {
    title: 'Waarschuwingsvoorlooptijd',
    what: 'Hoeveel dagen vooraf de modellen melden dat een voorspeld probleem zou optreden.',
    steel:
      'Vuurvaste stenen bestellen en een reparatieploeg boeken duurt weken. Een waarschuwing die te laat komt is niets waard, dus voorlooptijd telt net zo zwaar als nauwkeurigheid.',
    useIt: 'Het pilotdoel is minstens 21 dagen. Minder laat geen tijd om een stop te plannen.',
  },
  'kpi:failures': {
    title: 'Ongeplande stops',
    what: 'Aantal keren dat de productie stopte zonder planning.',
    steel:
      'Een ongeplande hoogovenstop is extreem duur: het vat moet warm blijven, downstream walserijen krijgen geen materiaal, en de herstart zelf kost energie.',
    useIt: 'Het doel van het hele platform is om deze om te zetten in geplande stops.',
  },

  // ---------------------------------------------------------- furnace health
  'kpi:risk': {
    title: 'Risico van de bekleding',
    what: 'Een score van 0 tot 1 die schat hoe waarschijnlijk het is dat de ovenbekleding binnenkort haar slijtagelimiet bereikt.',
    steel:
      'Een hoogoven is een stalen mantel met hittebestendige steen, de vuurvaste bekleding. De steen slijt langzaam weg; als hij doorslijt, bereikt vloeibaar metaal de mantel. Deze score is de vroege waarschuwing van de fabriek.',
    useIt: 'Boven 0,8 zou de onderhoudsplanner een reparatievenster moeten boeken.',
  },
  'kpi:days': {
    title: 'Resterende nuttige levensduur',
    what: 'Geschatte dagen bedrijf voordat de bekleding bij het huidige tempo haar slijtagelimiet bereikt.',
    steel:
      'In de industrie staat dit bekend als RUL. Een bekleding vervangen is een campagne van meerdere weken, dus de datum maanden vooraf kennen maakt van een crisis een project.',
    useIt: 'Gebruik het betrouwbaarheidsgetal ernaast. Een korte levensduur met lage betrouwbaarheid vraagt om meer meting, niet om directe actie.',
  },
  'kpi:confidence': {
    title: 'Modelbetrouwbaarheid',
    what: 'Hoe zeker het model is over zijn eigen voorspelling, gegeven de data die het had.',
    steel: 'Sensoren vallen uit en metingen drijven weg. Betrouwbaarheid naast het antwoord publiceren voorkomt dat een ingenieur een cijfer vertrouwt dat op dunne data is gebouwd.',
    useIt: 'Lage betrouwbaarheid is een signaal om de sensorconditie te controleren voordat u op de voorspelling handelt.',
  },
  'kpi:failDate': {
    title: 'Geprojecteerde slijtdatum',
    what: 'De kalenderdatum waar de schatting van resterende levensduur op uitkomt.',
    steel: 'Van "zoveel dagen" een datum maken laat planners die afstemmen op vakanties, beschikbaarheid van aannemers en orderboeken.',
    useIt: 'Vergelijk die met het geplande onderhoudsvenster op het plannerscherm.',
  },
  'kpi:anomalies': {
    title: 'Thermische afwijkingen',
    what: 'Aantal metingen dat in het geselecteerde venster van het verwachte patroon afweek.',
    steel:
      'Een lokaal heet punt op de ovenmantel is meestal het eerste fysieke teken dat de steen erachter dunner is geworden.',
    useIt: 'Open de warmtekaart om te zien waar op de mantel de afwijkingen geclusterd zijn.',
  },
  'kpi:cooling': {
    title: 'Prestaties van koelwater',
    what: 'Hoe effectief het koelsysteem warmte uit de ovenmantel afvoert.',
    steel:
      'Watergekoelde koelplaten zitten tussen de steen en de stalen mantel. Als de koeling verzwakt, warmt de mantel op, dus dit is een veiligheidsmeting en niet alleen een efficiëntiemeting.',
    useIt: 'Een dalende waarde met stijgende manteltemperatuur is de combinatie die telt.',
  },
  'kpi:slope': {
    title: 'Temperatuurtrend',
    what: 'Hoe snel de temperatuur stijgt of daalt, in graden per dag.',
    steel: 'Vuurvaste slijtage gaat langzaam, dus een aanhoudende opwaartse helling van zelfs een fractie graad per dag is betekenisvol.',
    useIt: 'Het teken telt meer dan de grootte. Een blijvend positieve helling in één sector verdient aandacht.',
  },
  'kpi:sensor': {
    title: 'Sensordekking',
    what: 'Hoeveel thermische sensoren nu gezonde data rapporteren.',
    steel: 'Voorspellingen zijn maar zo goed als hun invoer. Een sector met dode sensoren is feitelijk onbewaakt.',
    useIt: 'Controleer dit met het scherm voor het apparatenpark wanneer het aantal daalt.',
  },
  'furnace-health/thermal-explorer:kpi:peak': {
    title: 'Piektemperatuur van de mantel',
    what: 'De hoogste temperatuur gemeten op de ovenmantel in de geselecteerde periode.',
    steel:
      'De mantel moet veel koeler blijven dan het gesmolten binnenste. Een stijgende piek betekent dat warmte een pad door de vuurvaste bekleding vindt.',
    useIt: 'Gebruik de warmtekaart om te vinden welke sector de piek veroorzaakte.',
  },
  'kpi:open': {
    title: 'Open werkorders',
    what: 'Onderhoudstaken die zijn aangemaakt maar nog niet voltooid.',
    steel: 'Staalfabrieken draaien continu, dus onderhoud concurreert met productie om tijd. De achterstand is de zichtbare kostenpost van uitstel.',
    useIt: 'Sorteer de werkordertabel op prioriteit om te zien wat naar het volgende venster moet worden gehaald.',
  },
  'kpi:urgent': {
    title: 'Urgente werkorders',
    what: 'Taken gemarkeerd als nodig voor de volgende geplande stop.',
    steel: 'Dit zijn de taken die bepalen of de volgende stop gepland of geforceerd is.',
    useIt: 'Alles hier moet worden vergeleken met de lengte van het onderhoudsvenster.',
  },
  'kpi:completed': {
    title: 'Voltooide werkorders',
    what: 'Taken die in de huidige periode zijn afgesloten.',
    steel: 'De voltooiingsgraad tegenover de achterstand laat zien of de onderhoudscapaciteit past bij de behoeften van de fabriek.',
    useIt: 'Lees dit samen met het open aantal. Beide dalend is goed, alleen voltooid dalend niet.',
  },
  'kpi:window': {
    title: 'Onderhoudsvenster',
    what: 'De lengte van de volgende geplande productiestop die beschikbaar is voor reparaties.',
    steel:
      'Een deel van een oven opnieuw bekleden kan dagen duren en het vat moet eerst afkoelen. Het werk in het venster passen is het centrale probleem van de planner.',
    useIt: 'Vergelijk dit met de totale duur van de urgente werkorders.',
  },

  // ------------------------------------------------------------------ energy
  'kpi:price': {
    title: 'Spotprijs elektriciteit',
    what: 'Wat een megawattuur elektriciteit nu kost op de groothandelsmarkt.',
    steel:
      'Europese stroomprijzen veranderen elk uur en kunnen binnen een dag veelvoudig variëren. Een fabriek die flexibele belasting naar goedkope uren kan verplaatsen, verlaagt de rekening zonder minder te produceren.',
    useIt: 'Zet dit naast de geplande belasting in de prijs- en belastingsgrafiek.',
  },
  'kpi:savings': {
    title: 'Geprojecteerde besparingen',
    what: 'Geld dat de voorgestelde planning zou besparen vergeleken met hetzelfde werk tegen een vlak tarief.',
    steel: 'De besparing komt puur uit timing. Dezelfde tonnen worden geproduceerd, alleen in goedkopere uren.',
    useIt: 'Dit is een voorstel. Het wordt pas echt wanneer een operator de planning goedkeurt.',
  },
  'kpi:shiftable': {
    title: 'Verschuifbare belasting',
    what: 'Hoeveel van de elektriciteitsvraag van de fabriek naar een ander uur kan worden verplaatst.',
    steel:
      'Een hoogoven kan niet worden gepauzeerd, maar herverhittingsovens, walserijen en zuurstoffabrieken hebben enige flexibiliteit. Alleen dat flexibele deel kan goedkope stroom volgen.',
    useIt: 'Dit zet het plafond op wat elke optimalisatie kan bereiken.',
  },
  'kpi:baseline': {
    title: 'Basisscenario',
    what: 'Wat kosten en emissies zouden zijn zonder enige lastverschuiving.',
    steel: 'Elke geclaimde verbetering heeft iets nodig om tegen te meten. Dit is die referentie.',
    useIt: 'Vergelijk dit met het geoptimaliseerde scenario om het voordeel te lezen.',
  },
  'kpi:optimized': {
    title: 'Geoptimaliseerd scenario',
    what: 'Kosten en emissies onder de planning die de optimalisator voorstelt.',
    steel: 'De optimalisator respecteert echte fabrieksbeperkingen zoals minimale draaitijden, op- en afregelsnelheden en netaansluitlimieten, niet alleen de prijs.',
    useIt: 'Controleer de tegel met beperkingsovertredingen voordat u het cijfer vertrouwt.',
  },
  'kpi:estimate': {
    title: 'Scenarioschatting',
    what: 'Het resultaat van de wat-als-instellingen die nu op dit scherm zijn geselecteerd.',
    steel: 'Laat een planner een idee testen voordat de fabriek eraan wordt vastgelegd.',
    useIt: 'Verander de schuifregelaars en kijk hoe dit cijfer reageert.',
  },
  'kpi:violations': {
    title: 'Beperkingsovertredingen',
    what: 'Hoeveel fabrieksregels het huidige scenario zou breken.',
    steel:
      'Beperkingen leggen fysieke werkelijkheid vast: een oven die boven een temperatuur moet blijven, een walserij die niet steeds kan starten en stoppen. Een goedkope planning die ze breekt, is geen planning.',
    useIt: 'Dit moet nul zijn voordat een scenario voor goedkeuring kan worden voorgesteld.',
  },
  'energy-optimization/load-shift-simulator:kpi:peak': {
    title: 'Piekvraag',
    what: 'De hoogste elektriciteitsafname die het scenario zou bereiken.',
    steel:
      'Netaansluitingen worden deels afgerekend op de hoogste bereikte piek, dus de piek afvlakken bespaart geld zelfs als het totale verbruik gelijk blijft.',
    useIt: 'Let erop tijdens het verschuiven van belasting. Werk verplaatsen kan per ongeluk een nieuwe, hogere piek maken.',
  },
  'kpi:server': {
    title: 'Solverstatus',
    what: 'Of de optimalisatiemotor een geldig antwoord vond, en hoe goed dat is.',
    steel: 'Duidelijk zeggen of de optimalisatie werkelijk is opgelost, onderscheidt een beslissingsondersteunend hulpmiddel van een black box.',
    useIt: 'Een onhaalbaar resultaat betekent dat niet alle beperkingen tegelijk kunnen worden gehaald. Versoepel er één en voer opnieuw uit.',
  },

  // ----------------------------------------------------------------- quality
  'kpi:firstpass': {
    title: 'First-pass percentage',
    what: 'Aandeel batches dat zonder nabewerking aan de specificatie voldeed.',
    steel: 'Nabewerking betekent opnieuw smelten, wat energie twee keer gebruikt en de order vertraagt. Het first-pass percentage is waar kwaliteit en kosten samenkomen.',
    useIt: 'Een daling hier zou te herleiden moeten zijn tot een oorzaak in de Pareto-grafiek.',
  },
  'kpi:defect': {
    title: 'Defectpercentage',
    what: 'Aandeel van de productie met een geregistreerd defect.',
    steel: 'Typische defecten zijn oppervlaktescheuren, slakinsluitingen of een chemische samenstelling die buiten het klantbereik is gedreven.',
    useIt: 'Gebruik de Pareto-grafiek om te vinden welke paar defecttypen domineren.',
  },
  'kpi:ncr': {
    title: 'Non-conformiteitsrapporten',
    what: 'Formele records die worden aangemaakt wanneer een batch niet aan de specificatie voldoet.',
    steel: 'Klanten in automotive en bouw auditen deze records, dus ze zijn zowel een nalevingsplicht als een kwaliteitssignaal.',
    useIt: 'Open de tabel om te zien welke productkwaliteiten zijn geraakt.',
  },
  'kpi:cpk': {
    title: 'Procesbekwaamheid (Cpk)',
    what: 'Eén getal dat zegt hoe ruim het proces binnen de tolerantie van de klant past.',
    steel:
      'Boven 1,33 wordt meestal als bekwaam gezien; onder 1,0 worden defecten eerder als normaal verwacht dan als toeval.',
    useIt: 'Lees dit met de regelkaart. Cpk vat samen wat de grafiek in detail toont.',
  },
  'kpi:ooc': {
    title: 'Punten buiten controle',
    what: 'Metingen die buiten de statistische grenzen op de regelkaart vielen.',
    steel:
      'Buiten controle betekent niet buiten specificatie. Het betekent dat het proces veranderde, wat een reden is om te onderzoeken voordat de klant het merkt.',
    useIt: 'Elk punt zou een toegewezen oorzaak erbij moeten hebben vastgelegd.',
  },
  'kpi:total': {
    title: 'Totaal aantal metingen',
    what: 'Hoeveel metingen de statistieken op dit scherm dragen.',
    steel: 'Statistische regels hebben genoeg data nodig om betekenisvol te zijn. Een bekwaamheidscijfer uit een handvol monsters is niet betrouwbaar.',
    useIt: 'Vergroot het tijdsbereik als dit aantal laag is.',
  },
  'kpi:top': {
    title: 'Grootste bijdrage',
    what: 'De ene categorie die verantwoordelijk is voor het grootste deel van het probleem.',
    steel: 'Verbeterprogramma\u2019s slagen door één dominante oorzaak tegelijk te herstellen, niet alles tegelijk.',
    useIt: 'Dit is de eerste staaf in de Pareto-grafiek.',
  },

  // -------------------------------------------------------- sustainability
  'kpi:allowance': {
    title: 'Emissierechten',
    what: 'Rechten in bezit, elk goed voor één ton CO2.',
    steel:
      'Onder het EU-emissiehandelssysteem moet een fabriek één recht inleveren per uitgestoten ton. Sommige worden gratis toegekend, de rest moet worden gekocht.',
    useIt: 'Vergelijk met het plafond en met de werkelijke emissies om het gat te zien.',
  },
  'kpi:cap': {
    title: 'Emissieplafond',
    what: 'De gratis toewijzing die de fabriek ontvangt voor het nalevingsjaar.',
    steel: 'Het plafond krimpt elk jaar bewust, en dat is het mechanisme dat de sector tot decarbonisatie dwingt.',
    useIt: 'Emissies boven het plafond moeten worden gedekt met gekochte rechten.',
  },
  'kpi:used': {
    title: 'Gebruikte rechten',
    what: 'Hoeveel van de toewijzing dit jaar tot nu toe is verbruikt.',
    steel: 'Verbruik is niet gelijkmatig over het jaar. Een koude winter of een lange campagne verschuift het.',
    useIt: 'Vergelijk het gebruikte percentage met het verstreken percentage van het jaar.',
  },
  'kpi:overage': {
    title: 'Geprojecteerd tekort',
    what: 'Rechten die de fabriek naar verwachting aan het einde van het jaar tekortkomt.',
    steel: 'Een tekort moet op de markt worden gekocht tegen de koolstofprijs van dat moment, dus het is een direct financieel risico.',
    useIt: 'Vermenigvuldig met de koolstofprijs om de kosten te zien, weergegeven in de blootstellingstegel.',
  },
  'kpi:exposure': {
    title: 'Blootstelling aan koolstofkosten',
    what: 'De geldwaarde van het geprojecteerde tekort aan emissierechten.',
    steel: 'Dit vertaalt een milieucijfer naar een regel die de financieel directeur begrijpt, en dat is wat decarbonisatie gefinancierd krijgt.',
    useIt: 'Het beweegt mee met zowel de fabrieksemissies als de marktprijs voor koolstof.',
  },
  'kpi:intensity': {
    title: 'Emissie-intensiteit',
    what: 'CO2 uitgestoten per ton geproduceerd staal.',
    steel:
      'Intensiteit is de eerlijke manier om fabrieken en jaren te vergelijken, omdat totale emissies al dalen door minder te produceren. Intensiteit daalt alleen als het proces verbetert.',
    useIt: 'Gebruik dit in plaats van totale tonnen wanneer u voortgang beoordeelt.',
  },
  'kpi:target': {
    title: 'Doel',
    what: 'De waarde die de fabriek heeft toegezegd te halen, getoond naast waar zij werkelijk staat.',
    steel: 'Doelen in deze demo zijn pilotafspraken, geen gemeten resultaten. De gemeten waarde wordt altijd ernaast getoond.',
    useIt: 'Het gat tussen de twee is wat het verbeterprogramma moet sluiten.',
  },
  'kpi:records': {
    title: 'Auditrecords',
    what: 'Hoeveel gebeurtenissen zijn geschreven naar het manipulatiebestendige auditlogboek.',
    steel: 'Toezichthouders en klanten vragen allebei hoe een gerapporteerd cijfer is gemaakt. Elke berekening hier laat een record achter dat dat beantwoordt.',
    useIt: 'Open de tabel om afzonderlijke regels te bekijken.',
  },
  'kpi:immutable': {
    title: 'Ketenintegriteit',
    what: 'Of het auditlogboek van begin tot eind verifieert.',
    steel:
      'Elke regel draagt een cryptografische vingerafdruk van de vorige. Een oud record aanpassen breekt daardoor elke vingerafdruk erna en is direct zichtbaar.',
    useIt: 'Alles behalve geverifieerd betekent dat u niet op het logboek moet vertrouwen.',
  },
  'kpi:models': {
    title: 'Geregistreerde modellen',
    what: 'Hoeveel voorspellingsmodellen zijn geregistreerd met een vastgelegde versie.',
    steel: 'Als een voorspelling een beslissing beïnvloedde, moet u precies weten welke versie van welk model die maakte.',
    useIt: 'De modelversie verschijnt naast elke voorspelling in de audittabel.',
  },
  'kpi:domains': {
    title: 'Gedekte domeinen',
    what: 'Hoeveel gebieden van de fabriek in het auditspoor zijn vertegenwoordigd.',
    steel: 'Gedeeltelijke dekking is een nalevingsgat. Het doel is dat elk beslissingsrelevant gebied naar hetzelfde log schrijft.',
    useIt: 'Filter de audittabel op domein om één gebied te bekijken.',
  },

  // --------------------------------------------------------------- knowledge
  'kpi:sessions': {
    title: 'Vastlegginsessies',
    what: 'Interviews die met ervaren operators zijn opgenomen en omgezet in conceptprocedures.',
    steel:
      'Veel kennis in een staalfabriek zit in de hoofden van mensen die de oven dertig jaar hebben bediend. Die vastleggen voordat zij met pensioen gaan is een echt industrieel probleem.',
    useIt: 'Open een sessie om het transcript naast het concept te zien dat eruit kwam.',
  },
  'kpi:coverage': {
    title: 'Proceduredekking',
    what: 'Aandeel kritieke taken dat nu een geschreven, goedgekeurde procedure heeft.',
    steel: 'Gaten in de dekking zijn plekken waar de fabriek afhankelijk is van de beschikbaarheid van één persoon.',
    useIt: 'Gebruik dit om te bepalen welke interviews u hierna uitvoert.',
  },
  'kpi:approved': {
    title: 'Goedgekeurde procedures',
    what: 'Concepten die een gekwalificeerd mens heeft beoordeeld en goedgekeurd.',
    steel: 'Een procedure die door een machine is geschreven en nooit is gecontroleerd, is een risico. Goedkeuring is de controle die de output bruikbaar maakt.',
    useIt: 'Alleen goedgekeurde procedures worden door de assistent als antwoorden teruggegeven.',
  },
  'kpi:review': {
    title: 'Wacht op beoordeling',
    what: 'Concepten die wachten op acceptatie, correctie of afwijzing door een mens.',
    steel: 'Deze wachtrij is de mens-in-de-lus-poort. Niets gaat eromheen.',
    useIt: 'Een groeiende wachtrij betekent dat beoordelingscapaciteit, niet vastleggingscapaciteit, de bottleneck is.',
  },

  // -------------------------------------------------------------- operations
  'kpi:oee': {
    title: 'Overall equipment effectiveness (OEE)',
    what: 'Eén getal dat combineert hoeveel van de tijd apparatuur draaide, hoe snel zij draaide en hoeveel output goed was.',
    steel: 'De standaard scorekaart voor productie. Zij voorkomt dat een fabriek succes claimt op beschikbaarheid terwijl stilletjes product wordt afgekeurd.',
    useIt: 'Als dit daalt, controleer dan welk van de drie onderdelen de oorzaak was.',
  },
  'kpi:throughput': {
    title: 'Doorvoer',
    what: 'Ton staal geproduceerd in de periode.',
    steel: 'De output van de fabriek en de noemer van bijna elke andere maat op dit portaal.',
    useIt: 'Lees intensiteitsmaten altijd ertegen af. Lage output verfraait totale emissies.',
  },
  'kpi:ontime': {
    title: 'Levering op tijd',
    what: 'Aandeel klantorders dat op de beloofde datum is verzonden.',
    steel: 'Staal gaat naar geplande productielijnen verderop, dus een late levering stopt de fabriek van iemand anders.',
    useIt: 'Late leveringen zijn vaak terug te voeren op ongeplande stops of nabewerking.',
  },
  'kpi:alerts': {
    title: 'Actieve waarschuwingen',
    what: 'Omstandigheden die nu zijn gemarkeerd als aandacht nodig.',
    steel: 'Alarmmoeheid is een echt veiligheidsrisico, dus dit platform mikt op weinig, betekenisvolle waarschuwingen in plaats van veel.',
    useIt: 'Klik door om het onderliggende signaal voor elke waarschuwing te zien.',
  },

  // ---------------------------------------------------------- platform ops
  'kpi:util': {
    title: 'Capaciteitsbenutting',
    what: 'Hoeveel van de gereserveerde analytische rekencapaciteit in gebruik is.',
    steel: 'Het platform draait bewust op kleine capaciteit die per uur wordt betaald, zodat een demonstratieomgeving niet kost als een productieomgeving.',
    useIt: 'Aanhoudend hoge benutting is het signaal om op te schalen voordat taken gaan wachten.',
  },
  'kpi:utilization': {
    title: 'Capaciteitsbenutting',
    what: 'Hoeveel van de gereserveerde analytische rekencapaciteit in gebruik is.',
    steel: 'Analytische capaciteit wordt per uur gefactureerd, druk of niet, dus ongebruikte capaciteit is pure verspilling.',
    useIt: 'Gebruik dit met de kostentegel om te beoordelen of de huidige grootte klopt.',
  },
  'kpi:spend': {
    title: 'Platformuitgaven',
    what: 'Wat het analyseplatform heeft gekost over de getoonde periode.',
    steel: 'Een beslissingsondersteunend systeem moet minder kosten dan de verliezen die het voorkomt. De kosten open tonen hoort bij dat argument.',
    useIt: 'Vergelijk met de besparingen die op de energieschermen worden gemeld.',
  },
  'kpi:cost': {
    title: 'Kosten',
    what: 'Het geldbedrag voor het item dat op deze tegel wordt getoond.',
    steel: 'Elke technische keuze op dit platform heeft een prijs, en die is bewust zichtbaar in plaats van verborgen.',
    useIt: 'Open de kostentabel voor de uitsplitsing per dienst.',
  },
  'kpi:rate': {
    title: 'Verwerkingssnelheid',
    what: 'Hoeveel records de pijplijn per tijdseenheid verwerkt.',
    steel: 'Sensordata komt continu binnen. Als de pijplijn langzamer verwerkt dan data binnenkomt, lopen dashboards stilletjes achter.',
    useIt: 'Lees dit samen met dataversheid. Een gezonde snelheid maar oude data betekent dat er stroomopwaarts iets is gestopt.',
  },
  'kpi:fresh': {
    title: 'Dataversheid',
    what: 'Hoe lang geleden het nieuwste datapunt binnenkwam.',
    steel: 'Een controlekamerscherm dat temperaturen van gisteren toont, is erger dan geen scherm, omdat het actueel lijkt.',
    useIt: 'Als dit groeit, behandel elk ander cijfer op het portaal als verdacht totdat het herstelt.',
  },
}
