"""Dutch answers served for the Copilot's per-persona predefined questions.

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
    "persona-plant-manager-q1": """**Er is geen enkele lijn-KPI per dag in deze demo-dataset.** De dichtstbijzijnde live-proxy is **LUX-RHF-01**, de herverwarmingslijn die tijdens het schaarstevenster het verst van plan afwijkt.

- De sitedoorvoer is **128.4 t/h** tegen een doel van **130 t/h**, met OEE **84.1%** tegen 85%
- Tussen **17:00 en 20:00** zakt het herverwarmingsprofiel naar ongeveer **114-122 t/h**
- Dat venster valt samen met de avondpiek van **€280/MWh**, dus de dip is bewuste lastverschuiving en geen ongeplande stop
- Stroomafwaartse kwaliteit blijft aandacht vragen omdat **COIL-LUX-260725-017** een haspeltemperatuur-bias van **+11.4 °C** draagt

Als u de ene lijn wilt die operationeel het verst achterligt, triageer dan eerst het venster van de herverwarmingsoven. Het gevolg is commercieel in plaats van catastrofaal: u ruilt een korte doorvoerdip in voor goedkopere energie en lagere Scope 2-blootstelling.""",
    "persona-plant-manager-q2": """**De dataset bevat geen opbrengstgrootboek met ploeglabel voor de nachtploeg.** Het dichtstbijzijnde bewijs wijst op lokale kwaliteitsdrift, niet op een fabriekbrede metallurgische uitslag.

- De huidige fail-charge is **COIL-LUX-260725-017** op **LUX-HSM-01**, met een haspeltemperatuur-bias van **+11.4 °C**
- Rekgrens is **452.4 MPa** tegen een specificatie van **380-520 MPa**, dus het staal zit nog binnen de band, maar het labresultaat is **REVIEW**
- SPC zet subgroep **20** op **11.4**, boven de **8.5** bovenste controlegrens
- Over juli 2026 zijn er **86 defecten**, en haspeltemperatuurdrift is goed voor **34 (39.5%)**, vóór randscheur 21 en oppervlakteschaalsvorming 14

Begin de ochtend met beheersing van de haspeltemperatuur op de warmwalsstraat, vrijgavediscipline op de DP780 coil en bevestiging dat de drift toewijsbaar was in plaats van systemisch. Dat is de oorzaak met de hoogste kans waarop u als eerste kunt handelen.""",
    "persona-plant-manager-q3": """**Begin met de haard, daarna de dispatch, daarna de DP780 kwaliteitsdrift.** Dat is vanochtend de schoonste triagevolgorde.

- **1. Oven** - **ALERT-HEARTH-SECTOR-07-260725** is de enige critical alert: risico **0.8995**, **P50 19.65 dagen**, bekleding **363 mm** tegen een minimum van **300 mm**
- **2. Energie** - **REC-DEMO-LUX-240725** wacht nog op goedkeuring en is **€2,688.70** of **7.25%** waard, met piekvraag omlaag van **56.0 MW** naar **51.58 MW**
- **3. Kwaliteit** - **COIL-LUX-260725-017** draagt een haspeltemperatuur-bias van **+11.4 °C** en de SPC-overschrijding van subgroep 20
- De bordstatus is **16 open alerts**: **1 critical, 8 warning, 7 info, 2 acknowledged**

Die volgorde beschermt eerst veiligheid en beschikbaarheid, legt daarna vandaag de grootste beheersbare kosten- en koolstofhefboom vast en pakt vervolgens het meest zichtbare klantgerichte kwaliteitsrisico aan.""",
    "persona-plant-manager-q4": """**84.1%** op dit moment, tegen een doel van **85%**.

- Doorvoer is **128.4 t/h** versus **130 t/h**
- Levering op tijd is **96.4%** versus 97%
- Energie-intensiteit is **€312/t** versus **€300/t**
- De zichtbare prestatieremming zit geconcentreerd in het schaarstevenster **17:00-20:00**, waar de herverwarmingsoutput op ongeveer **114-122 t/h** draait

Dus de fabriek zit dicht bij de OEE-doelstelling, maar haalt die niet. De belangrijke lezing is dat het tekort bewust wordt ingekocht om **€280/MWh** elektriciteit te vermijden, niet omdat de lijn instabiel draait. Het operationeel gevolg is dat u de energie-afruil expliciet houdt in plaats van deze als verborgen doorvoerverlies te behandelen.""",
    # -- furnace-operator ----------------------------------------------------
    "persona-furnace-operator-q1": """**Het haardprofiel van BF-01 is asymmetrisch, niet overal gelijkmatig heet.** Het aandachtspunt is **SECTOR-07**.

- **SECTOR-07** stijgt met **3.4 °C/h** vanaf ongeveer **652 °C**
- De andere sectoren bewegen slechts rond **0.4 °C/h**, dus het probleem is divergentie, niet een verschuiving van de hele haard
- Lokale warmtestroom is **118 kW/m²**
- Koeling ziet er nog nominaal uit op **198 m³/h** met een water-**ΔT van 9.4 °C**
- De schatting van de vuurvaste bekleding daalt van **372 mm** naar **363 mm** over 24 uur

Die combinatie is waarom het model **heat_flux_6h_slope** op **29%**, **sector_to_ring_temp_delta** op **24%** en **cooling_efficiency_residual** op **18%** weegt. Het gevolg is dat u dit moet behandelen als een reëel lokaal slijtsignaal, niet als een onschuldige opwarming van de hele oven.""",
    "persona-furnace-operator-q2": """**De demo bevat geen sensor met de tag T12-North.** Het dichtstbijzijnde live-bewijs is **TC-114** die drift, plus de mantel op **SECTOR-07** die wegloopt van zijn buren.

- **TC-114** drift met **1.8 °C/h**
- **SECTOR-07** stijgt met **3.4 °C/h** vanaf **652 °C**, terwijl naburige sectoren rond **0.4 °C/h** zitten
- Warmtestroom is al **118 kW/m²**
- Koelwater staat nog steeds op **198 m³/h** met **ΔT 9.4 °C**, dus een simpele verklaring via waterverlies past niet bij het patroon

Dus de best onderbouwde verklaring is niet 'één slechte noordsensor' maar een echte lokale thermische verandering die ook zichtbaar is in de fysica-geïnformeerde score. Het operationeel gevolg is dat u TC-114 verifieert tegen aangrenzende thermokoppels, maar blijft handelen alsof het haardsignaal echt is totdat die controle het tegendeel aantoont.""",
    "persona-furnace-operator-q3": """**Er is geen live tabel met aftapparameters op dit platform.** Het dichtstbijzijnde geborgde bewijs is **PROC-DEMO-0002**, plus het feit dat de abnormaliteit van vandaag in thermisch haardgedrag zit en niet in een chemievenster van een afgetapte smelt.

- **PROC-DEMO-0002** is de goedgekeurde procedure: status **APPROVED**, versie **3**
- **PROC-DEMO-0001** staat nog steeds op **IN_REVIEW**, dus die kan controles informeren maar mag niet als operationele autoriteit worden behandeld
- De huidige context is thermisch: warmtestroom **118 kW/m²**, koeling **198 m³/h**, **ΔT 9.4 °C**, en sector 07 stijgt met **3.4 °C/h**
- De procesketen loopt nog steeds van hoogoven naar staalproductie naar gietmachine; niets in het bewijs zegt dat u de volgende gieting op eigen inzicht moet aanpassen

Verzin dus geen aftapaanpassing op basis van dit scherm. Het gevolg is procedureel: voer eerst de goedgekeurde keurings- en bevestigingsstappen uit en wijzig de gietpraktijk pas als een geborgde BOF- of gietmachine-instructie dat expliciet voorschrijft.""",
    "persona-furnace-operator-q4": """**Het platform kwantificeert geen op zichzelf staande cokesratio-naar-slijtage-curve.** Wat het wel laat zien, is dat het slijtsignaal van vandaag wordt gedomineerd door thermische spanning.

- De bovenste modeldrijfveer is **heat_flux_6h_slope op 29%**
- Daarna **sector_to_ring_temp_delta op 24%**
- Vervolgens **cooling_efficiency_residual op 18%**
- De live thermische toestand daarachter is **118 kW/m²** warmtestroom, **198 m³/h** koelstroom en water-**ΔT 9.4 °C**
- De schatting staat al op **363 mm** bekledingsdikte versus een veilig minimum van **300 mm**

Dus het eerlijke antwoord is dat cokesratio als covariaat kan meetellen, maar dat de huidige score niet wordt gedreven door een bewezen cokesratio-elasticiteit. Het operationeel gevolg is dat u stuurt op wat nu direct is aangetoond - warmtelast, sectoronbalans en koeleffectiviteit - in plaats van een onbewezen verklaring op alleen cokes te volgen.""",
    # -- maintenance-engineer ------------------------------------------------
    "persona-maintenance-engineer-q1": """**LUX-BF-01 / HEARTH-SECTOR-07** is deze week duidelijk het grootste risico.

- Risicoscore **0.8995** met **P50 19.65 dagen**, **P10 18.69**, **P90 20.61**
- Geschatte dikte **363 mm** tegen een minimum van **300 mm**
- Degradatie loopt op ongeveer **3.0 mm/day**
- Het volgende benoemde asset in de dataset, **LUX-RHF-01**, zit slechts rond **34%** risico met ongeveer **120 days** resterend
- Werkorder **WO-DEMO-LUX-1042** bestaat al voor een geplande keuring

Er is geen goede tweede binnen dezelfde urgentieband. Het gevolg is dat u het keurings- en herbekledingsvenster eerst rond BF-01 vastzet; alles daarbuiten is watchlist-werk en geen interventie voor deze week.""",
    "persona-maintenance-engineer-q2": """**Omdat het live thermische beeld steiler is dan de historische meldingsepisodes.** Het model ziet een sneller lokaal degradatiesignaal, niet slechts een herhaling van het oude gemiddelde pad.

- De schatting van de vuurvaste bekleding beweegt van **372 mm** naar **363 mm** over 24 uur
- **SECTOR-07** stijgt met **3.4 °C/h** terwijl naburige sectoren rond **0.4 °C/h** zitten
- De score blijft verankerd in dezelfde drijfveerstapel: **29%** warmtestroomhelling, **24%** sector-tot-ring-delta, **18%** koelefficiëntie-residu
- Koeling blijft nominaal op **198 m³/h** en **ΔT 9.4 °C**, wat de sectordivergentie moeilijker maakt om als instrumentatieruis weg te zetten

Historisch bewijzen de meldingsepisodes van juli dat het systeem een geplande herbekleding kan dragen bij **21.0 dagen** waarschuwing. De daling van vandaag naar **P50 19.65 dagen** betekent dat de huidige slijtsignatuur al binnen die comfortmarge zit. Het operationeel gevolg is dat u de planning en keuringscadans comprimeert, niet wacht tot de historie het wegmiddelt.""",
    "persona-maintenance-engineer-q3": """**Plan nu de keuringsreeks voor BF-01 en houd het herbekledingsvenster binnen dagen 18-24.** Dat is het geborgde plan dat door het huidige bewijs wordt ondersteund.

- **WO-DEMO-LUX-1042** is het live onderhoudsobject
- Keuringsdagen **1-4**: bevestig thermokoppels, koeling-inlaat- en uitlaattemperaturen en lokale historie
- Echografie en diktebevestiging dagen **5-8**
- Gepland herbekledingsvenster **dagen 18-24**
- Ankercijfers zijn risico **0.8995**, **P50 19.65 dagen** en **363 mm** bekleding versus **300 mm** minimum

Gebruik **PROC-DEMO-0002** als goedgekeurde operationele procedure; **PROC-DEMO-0001** staat nog in review en moet adviserend blijven. Het operationeel gevolg is dat u nog tijd hebt om dit een geplande stop te laten zijn, maar alleen als de keuringsreeks onmiddellijk start.""",
    "persona-maintenance-engineer-q4": """**P50 is 19.65 dagen; P90 is 20.61 dagen.** Het zijn geen twee verschillende toekomsten, maar twee verschillende betrouwbaarheidsniveaus op dezelfde voorspelde verdeling van resterende levensduur.

- **P10 18.69 dagen** - een conservatieve ondergrens
- **P50 19.65 dagen** - de mediaanschatting, de waarde die de meeste mensen voor dagelijkse planning gebruiken
- **P90 20.61 dagen** - een optimistische bovengrens met meer resterende levensduur dan de mediaan
- De spreiding is krap: slechts **0.96 days** van P50 naar P90

Tegen een programmadoel van **21 dagen** vroegtijdige waarschuwing vertellen alle drie de getallen hetzelfde verhaal: u zit feitelijk al in het actievenster. Het operationeel gevolg is dat u plant met P50, een stress-test doet met P10 en P90 alleen gebruikt om opwaarts potentieel te begrijpen - niet om wachten te rechtvaardigen.""",
    # -- energy-manager ------------------------------------------------------
    "persona-energy-manager-q1": """**02:00-05:00** is het volgende koolstofarme venster in de demo, geholpen door het **12 MWh** wind-PPA-blok.

- Het dure, vuilere venster is **17:00-20:00**, met prijzen tot **€280/MWh**
- Het dispatchvoorstel verplaatst flexibele herverwarming weg van die schaarsteperiode
- Eén zichtbare verplaatsing is **REHEAT-BATCH-06** van tijdslot **75** om **18:45** naar tijdslot **67** om **16:45**
- De impact op dagniveau is **€37,109.10** basisscenario naar **€34,420.40** geoptimaliseerd, een besparing van **€2,688.70** of **7.25%**

Dus het volgende schone venster is niet alleen goedkopere elektriciteit; het is het deel van de dag waarin het schema last kan opnemen zonder de koolstofpremie van de avondpiek te betalen. Het operationeel gevolg is dat u flexibele verhitting en smelten naar voren of later trekt, en het niet binnen de band van 17:00-20:00 laat staan.""",
    "persona-energy-manager-q2": """**Omdat tonnage daalde terwijl de vaste last dat niet deed.** De piek in energie-intensiteit van de vorige ploeg wordt het best verklaard door de bewuste herverwarmings-lastverschuiving door het schaarstevenster.

- Energie-intensiteit is **€312/t** tegen een doel van **€300/t**
- Doorvoer is **128.4 t/h** tegen **130 t/h**, maar in het venster **17:00-20:00** daalt die naar ongeveer **114-122 t/h**
- Dat is precies waar de spotprijs piekt op **€280/MWh**
- De dispatch houdt het totale tonnage ongewijzigd op **960 t**, dus het schema koopt kosten- en koolstofverlichting met een korte snelheidsdip

Met andere woorden, de piek is een rekenkundig effect van lagere momentane output tegenover een grotendeels vaste fabriekslast, en geen bewijs dat de fabriek plots intrinsiek inefficiënt werd. Het operationeel gevolg is dat u €/t samen met het dispatchdoel beoordeelt, niet geïsoleerd.""",
    "persona-energy-manager-q3": """**REC-DEMO-LUX-240725** is de grootste zichtbare besparing in de dataset, en de sleutelverplaatsing is de herverwarmingscharge die het tijdslot van 18:45 verlaat.

- Basisscenario **€37,109.10** naar geoptimaliseerd **€34,420.40** - een besparing van **€2,688.70** of **7.25%**
- Piekvraag daalt van **56.0 MW** naar **51.58 MW**
- **REHEAT-BATCH-06** verplaatst van tijdslot **75** om **18:45** en **€280/MWh** naar tijdslot **67** om **16:45** en **€97.24/MWh**
- Die ene verplaatsing verlaagt de chargekosten van **€3,920.00** naar **€1,361.36**
- In juli 2026 werden **100 of 116** aanbevelingen geaccepteerd, adoptie **0.862** tegen een doel van 0.70

Dus de kansen met de hoogste waarde zijn de flexibele thermische lasten die nog steeds het schaarstevenster raken. Het operationeel gevolg is dat u de dispatch snel goedkeurt en blijft zoeken naar herverwarmings- of smeltverplaatsingen in het avondvenster met hetzelfde patroon.""",
    "persona-energy-manager-q4": """**Het platform bevat op deze kaart geen EAF-specifieke daluren-what-if.** Het dichtstbijzijnde gemeten bewijs is de dispatch die al op flexibele thermische last is gemodelleerd.

- Die dispatch verlaagt CO₂ met **3.29%** bij ongewijzigd tonnage
- De optimalisatiecase voor het volledige plan op het duurzaamheidsoverzicht is **8.7%**
- Netkoolstof is gemiddeld ongeveer **244 gCO₂/kWh**, dus het verplaatsen van last naar schonere uren verlaagt Scope 2 zonder de staaloutput te wijzigen
- Diezelfde dispatch verlaagt ook de piekvraag van **56.0 MW** naar **51.58 MW**

Dus ik zou geen afzonderlijk cijfer voor EAF-smelten noemen dat de dataset niet bewijst. Wat het platform wel bewijst, is het mechanisme: verplaatsing naar daluren verlaagt emissies uit ingekochte elektriciteit direct. Het operationeel gevolg is dat u lastverschuiving behandelt als een echte Scope 2-hefboom, ook wanneer doorvoer en tonnage vlak blijven.""",
    # -- quality-engineer ----------------------------------------------------
    "persona-quality-engineer-q1": """**COIL-LUX-260725-017** is de enige huidige **FAIL** op het live Luxemburgse bord, en is degene die u als eerste moet pakken.

- Kwaliteit **NS-AUTO-DP780**
- Risicoscore **0.429**
- Haspeltemperatuur-bias **+11.4 °C**, de grootste zichtbare afwijking
- Gemeten rekgrens **452.4 MPa** tegen een specificatie van **380-520 MPa**
- Labstatus **REVIEW**, en de kwaliteitsalert blijft acknowledged maar open

Het platform toont op dit scherm geen aparte multi-coil-fail-lijst voor alleen oppervlak, dus dit is het dichtstbijzijnde waarheidsgetrouwe antwoord op een kwaliteitscontrolefout. Het operationeel gevolg is dat u deze coil vóór vrijgave in quarantaine zet of beoordeelt en de drift vervolgens terugvolgt via herverwarming en haspelen in plaats van uit te gaan van een algemeen labprobleem.""",
    "persona-quality-engineer-q2": """**Er is geen asset met de naam Line 3 in het demomodel.** Het dichtstbijzijnde echte lijnbewijs is **LUX-HSM-01**, en de drift wordt aangevoerd door haspeltemperatuur en niet door een brede wijziging in productmix.

- Juli 2026 registreert **86 defecten** in scope
- **34 defecten (39.5%)** zijn haspeltemperatuurdrift, vóór randscheur **21**, oppervlakteschaalsvorming **14**, diktevariatie **9**, coating **5** en overige **3**
- Het huidige speciaal-oorzaak-punt is subgroep **20** op **11.4**, boven de **8.5** UCL
- De getroffen coil is **COIL-LUX-260725-017** met **+11.4 °C** bias op **LUX-HSM-01**

Dus de trend leest u beter niet als 'Line 3 wordt slechter'; hij leest beter als één dominante foutmodus op de warmwalsroute. Het operationeel gevolg is dat u eerst de haspeltemperatuurregeling stabiliseert, omdat zowel de live-overschrijding als de maandelijkse defectmix daarheen wijzen.""",
    "persona-quality-engineer-q3": """**Het platform scoort middenlijnsegregatie niet als eigen KPI.** Het dichtstbijzijnde echte bewijs zit in de gietmachine-ingangen en de genealogie achter de getroffen coil.

- De live gietmachinevariabelen die beschikbaar zijn voor dit type triage zijn **superheat**, **casting_speed** en **secondary_cooling_flow** op **LUX-CC-01**
- De genealogie is volledig: **LOT-FE-017 → H-LUX-260725-0040 → LADLE-017 → SLAB-017 → REHEAT-017 → COIL-LUX-260725-017 → SMP-017 → SHIP-DEMO-017**
- De gemeten rekgrens van de coil is **452.4 MPa**, nog steeds binnen de band van **380-520 MPa**, met labstatus **REVIEW**

Dus ik zou het trio van de gietmachine gebruiken als correlatieset en de genealogie openhouden via herverwarming en haspelen. Het operationeel gevolg is dat u segregatieachtig risico onderzoekt als een routeprobleem dat zowel thermische praktijk op de gietmachine als stroomafwaartse herverwarming omvat, en niet als een op zichzelf staand labgetal dat uit het niets verschijnt.""",
    "persona-quality-engineer-q4": """**De SPC op dit scherm is niet rechtstreeks voor dikte; hij is voor haspeltemperatuur-bias.** Wat hij u vertelt, is nog steeds operationeel belangrijk.

- Gemiddelde **1.9**, sigma **2.2**, bovenste controlegrens **8.5**, onderste controlegrens **-4.7**
- Subgroep **20** leest **11.4**, dus hij is aan de hoge kant buiten controle
- Procescapaciteit is **Cpk 1.18** tegen een doel van **1.33**
- Dezelfde waarde **11.4** komt overeen met de haspel-bias op **COIL-LUX-260725-017**

Dus SPC vertelt u dat er een verse speciale oorzaak in de thermische handling zit, niet dat het hele procescentrum geleidelijk is weggedreven. Het operationeel gevolg is dat u eerst de toewijsbare oorzaak van de haspeltemperatuur onderzoekt; pas daarna moet u op basis van diezelfde productierun iets afleiden over dikteprestaties.""",
    # -- sustainability-officer ---------------------------------------------
    "persona-sustainability-officer-q1": """**Grotendeels wel, maar het kwartaal is niet langer comfortabel.** Het verbruik van emissierechten staat al op **71%**, en de emissierechten-marge is gedaald naar **6.2%**.

- Huidige prijs van emissierechten is **€86/t**
- De blootstellingsprognose is ongeveer **€248,000** op het huidige operationele punt
- De huidige fixture-intensiteit is **1.42 tCO₂e/t** tegen een doel van **1.35**
- De live grootboekalert hiervoor is de open **ALERT-ETS-ALLOWANCE-Q3**
- Afgesloten juli 2026 ziet er nog sterk uit op **1.019 tCO₂e/t** tegen een doel van **1.638** en een basislijn van **2.10**

Dus het programma ligt op koers in de historische scorecard, maar de buffer van het huidige kwartaal is dun. Het operationeel gevolg is dat u lastverschuiving en andere kortetermijnhefbomen nu blijft gebruiken, omdat een paar zwakke operationele dagen de resterende marge van 6.2% snel zouden opbranden.""",
    "persona-sustainability-officer-q2": """**Het platform bevat geen CBAM-specifieke blootstellingskolom.** De dichtstbijzijnde bewezen proxy is ETS-blootstelling plus de huidige Scope 1-intensiteit.

- De Scope 1-last van vandaag is **1,368 t CO₂e/day** voor **960 t** staal, of ongeveer **1,425 kg/t**
- Een rechte **10%** productiestijging bij ongewijzigde intensiteit zou ruwweg **136.8 t CO₂e/day** toevoegen
- Het verbruik van emissierechten staat al op **71%**, met een blootstellingsprognose van **€248,000** en een marge van **6.2%**
- De huidige operationele intensiteit staat op **1.42 tCO₂e/t** tegen een doel van **1.35**

Dus ik zou geen CBAM-factuurnummer claimen dat de dataset niet bevat. Wat het bewijs wel zegt, is dat een tonnagestijging van 10% de koolstofgeprijsde blootstelling materieel zou verhogen tenzij de intensiteit tegelijk verbetert. Het operationeel gevolg is dat u elke outputverhoging koppelt aan een efficiëntie- of dispatchactie, en tonnage niet laat stijgen op een ongewijzigd emissieprofiel.""",
    "persona-sustainability-officer-q3": """**1.42 tCO₂e/t** op de huidige operationele fixture.

- Dat is het live-dagcijfer, niet het maandgemiddelde van de afgesloten boeken
- Het ligt boven het doel van **1.35** voor de huidige operationele modus
- Voor de laatste afgesloten maand, juli 2026, stond de fabriek op **1.019 tCO₂e/t**
- Dat resultaat van juli versloeg het doel van **1.638** en de basislijn van **2.10** ruim
- De Scope-verdeling voor juli is **355,336 t** Scope 1 en **147,868 t** Scope 2

Dus uw huidige intensiteit is slechter dan de maandelijkse goudafsluiting, ook al ligt de programmatrend nog steeds vóór op het doel. Het operationeel gevolg is dat u de waarde 1.42 leest als een live-correctiesignaal - vooral rond thermische last en timing van elektriciteit - en niet als reden om aan het maandultimo-grootboek te twijfelen.""",
    "persona-sustainability-officer-q4": """**Ten opzichte van de benchmark ligt het programma voor op de maand en achter op de live dag.** Beide dingen zijn tegelijk waar.

- Huidige fixture: **1.42 tCO₂e/t** tegen een doel van **1.35**, dus ongeveer **0.07 tCO₂e/t** te hoog
- Afgesloten juli 2026: **1.019 tCO₂e/t** tegen een doel van **1.638** en een basislijn van **2.10**
- Huidige kwartaalcontext: verbruik van emissierechten **71%**, marge **6.2%**, verwachte blootstelling **€248,000** bij **€86/t**
- Dispatch blijft de snelste hefboom en verlaagt CO₂ met **3.29%** op het aangetoonde schema

Dus vergeleken met de benchmark wint het systeem in het historische grootboek, maar staat het onder druk in het huidige operationele venster. Het operationeel gevolg is dat u beide getallen samen blijft presenteren: de maandscore bewijst dat het programma werkt, terwijl het live-cijfer u vertelt dat vandaag nog actieve interventie nodig is.""",
    # -- knowledge-engineer --------------------------------------------------
    "persona-knowledge-engineer-q1": """**De fixture-dataset slaat geen opzoekfrequentie per woordenlijstterm op.** Het dichtstbijzijnde echte bewijs is vraag en dekking per kennisdomein.

- Hoogoven-dekking **82%**
- Kwaliteitslaboratorium **77%**
- Warmwalsstraat **71%**
- Herverwarmingsoven **64%**
- Energie en nutsvoorzieningen **58%**
- Procedurestatussen zijn verdeeld over **PROC-DEMO-0001 IN_REVIEW v2**, **PROC-DEMO-0002 APPROVED v3** en **PROC-DEMO-0003 DRAFT v1**

Dus ik kan niet waarheidsgetrouw de meest opgezochte woordenlijstterm uit deze dataset noemen. Wat ik wel kan zeggen, is dat de domeinen met de laagste dekking de waarschijnlijkste drukpunten voor opzoeken zijn, vooral energie en herverwarming. Het operationeel gevolg is dat u daar eerst vastlegging en goedkeuring verbetert, omdat onbewezen vragen zich daar het waarschijnlijkst ophopen.""",
    "persona-knowledge-engineer-q2": """**Het citeert bronnen die zowel relevant als governance-technisch geborgd zijn, niet zomaar welke opgehaalde tekst dan ook.** In dit platform is de bewijsketen bewust auditeerbaar.

- Het beslissingsgrootboek toont **AUD-0001** tot **AUD-0005**, en alle vijf hebben **complete_audit_flag true**
- Procedures zijn niet gelijk: **PROC-DEMO-0002** is **APPROVED v3**, terwijl **PROC-DEMO-0001** **IN_REVIEW v2** is en **PROC-DEMO-0003** **DRAFT v1**
- Voor vooraf gedefinieerde personavragen gebruikt de Copilot vaste Fabric-kaarten, zodat de geciteerde datasets deterministisch zijn en niet geïmproviseerd

Dus het systeem geeft de voorkeur aan goedgekeurde kennis en volledige auditketens boven louter beschikbare tekst. Het operationeel gevolg is dat een behulpzaam ogende niet-goedgekeurde bron toch buiten het uiteindelijke antwoord moet blijven als die niet aan dezelfde governancestandaard kan voldoen als het goedgekeurde of geauditeerde bewijs.""",
    "persona-knowledge-engineer-q3": """**De funderingsarchitectuur is gelaagd en bewust smal.** Het dichtstbijzijnde echte bewijs is de combinatie van geborgde procedures, Fabric-feiten en het ontologiepad dat assets via de procesroute met elkaar verbindt.

- Geborgde tekstlaag: **PROC-DEMO-0002 APPROVED v3**, met **PROC-DEMO-0001 IN_REVIEW v2** en **PROC-DEMO-0003 DRAFT v1** nog buiten hetzelfde vertrouwensniveau
- Analytische laag: Fabric-goudfeiten voor KPI-historie en KQL-hot views voor live status
- Structurele laag: de ontologie kan paden volgen zoals **LUX-BF-01** vooruit door de staalproductieketen naar **LUX-HSM-01**
- Beslissingslaag: **AUD-0001..AUD-0005**, allemaal met **complete_audit_flag true**

Dus het platform fundeert antwoorden op een klein aantal expliciete ophaalroutes in plaats van op vrije synthese. Het operationeel gevolg is voorspelbaarheid: u kunt inspecteren welke datalaag, procedurestatus of grafiekpad het antwoord ondersteunde, in plaats van een black-boxsamenvatting te moeten vertrouwen.""",
    "persona-knowledge-engineer-q4": """**Het platform toont in Fabric geen aparte tabel met 'prompt-injection score'.** Het dichtstbijzijnde operationele bewijs is dat het al fundering op alleen goedgekeurde bronnen afdwingt, plus volledige auditregistraties en menselijke review vóór actie.

- Alle vijf auditrijen **AUD-0001** tot **AUD-0005** zijn volledig
- Alleen **PROC-DEMO-0002** is goedgekeurd voor direct operationeel gebruik; **PROC-DEMO-0001** en **PROC-DEMO-0003** blijven onder die lat
- Aanbevelingen zoals **REC-DEMO-LUX-240725** blijven wachten op menselijke goedkeuring in plaats van automatisch te worden vastgelegd

Dus de echte guardrails die u uit de data kunt bewijzen, zijn governancegrenzen, traceerbaarheid en human-in-the-loop-besturing. Het operationeel gevolg is belangrijk: zelfs als niet-vertrouwde tekst zou worden opgehaald, mist die nog steeds een direct pad om een planning goed te keuren, een regelactie te wijzigen of het auditspoor te wissen.""",
    # -- ot-systems-engineer -------------------------------------------------
    "persona-ot-systems-engineer-q1": """**Geen daarvan is op dit moment materieel vertraagd of ontbreekt.** Het live landschap is gezond volgens de maatstaven die het platform werkelijk bevat.

- **17 apparaten** en **91 signalen** zijn online
- Signaalversheid ligt onder **5 s** voor de snelle live-feeds
- End-to-end versheid is ongeveer **12 s**
- Actieve incidenten zijn **0**
- De alarmdrempel voor quarantaine is **2% per 15 minutes**, en hier is geen bewijs dat die drempel is overschreden

Het ene punt om te onthouden is dat niet elk signaal op dezelfde cadans hoort te verversen: **hearth_refractory_estimate** is bewust een signaal van **900,000 ms**, geen vertraagde feed van 5 seconden. Het operationeel gevolg is dat u nu geen feedtriage nodig hebt; u moet de gezonde keten behouden terwijl u de procesalerts apart afhandelt.""",
    "persona-ot-systems-engineer-q2": """**5,000 ms** voor de snelle haardsignalen, met een algemene platformversheid van ongeveer **12 s** end-to-end.

- **hearth_shell_temperature** publiceert elke **5,000 ms**
- **local_heat_flux** publiceert elke **5,000 ms**
- **hearth_refractory_estimate** is bewust langzamer op **900,000 ms**
- Het landschap is overall nog steeds gezond: **17 apparaten**, **91 signalen**, **0 incidenten**
- **TC-114** die met **1.8 °C/h** drift is een thermisch signaalprobleem, geen bewijs van netwerklatentie

Dus het netwerk van ovensensoren is niet de bottleneck. Het operationeel gevolg is dat u latency in het datapad scheidt van procesgedrag: de 5-secondenfeeds komen op tijd aan, dus de abnormale haardtrend moet als fabrieksconditie worden behandeld en niet als transportartefact.""",
    "persona-ot-systems-engineer-q3": """**Het platform biedt geen wizard in het product voor provisioning van PLC-tags.** Het dichtstbijzijnde gezaghebbende object is het telemetrie-eventcontract dat de gateway moet publiceren.

- De envelop draagt **source_id**, **asset_id**, **plant_id**, **sequence**, **schema_name** en **schema_version**
- De naam van het telemetrieschema is **novasteel.telemetry.v1**
- Een goede source id ziet eruit als **LUX-BF-01-TC-H07-03**, zodat de asset- en signaalidentiteit expliciet blijven door de gateway heen
- Snelle tags moeten op de juiste cadans aansluiten, zoals **5,000 ms** voor haardmanteltemperatuur, terwijl langzamere schattingen op **900,000 ms** kunnen draaien
- Slecht gevormde payloads horen in quarantaine te landen in plaats van ongemerkt in silver te glippen

Dus het configureren van een nieuwe PLC-tag betekent hier dat u die netjes in de gepubliceerde envelop en het signaalregister inpast, niet dat u een verborgen analysetabel bewerkt. Het operationeel gevolg is dat contractconformiteit net zo belangrijk is als de tag zelf, omdat de verkeerde vorm bewust wordt geweigerd.""",
    "persona-ot-systems-engineer-q4": """**Het draadprotocol wordt niet in Fabric opgeslagen.** Wat het platform wel bewijst, is het gateway-gemedieerde patroon daarboven.

- Het live landschap toont **17 apparaten** en **91 signalen** met **0 incidenten**
- Events komen binnen als geversioneerde enveloppen met source ids zoals **LUX-BF-01-TC-H07-03**
- Gezondheid wordt gemeten via gateway-verbindingsstatus, versheid en wachtrijgedrag, niet via een protocolkolom
- End-to-end versheid is ongeveer **12 s**, en de snelle thermische signalen publiceren nog steeds elke **5,000 ms**

Dus ik zou niet doen alsof de analyselaag u kan vertellen of de thermische array Modbus, Profinet of iets anders is. Het dichtstbijzijnde waarheidsgetrouwe antwoord is dat het protocol geabstraheerd is achter het gatewaypatroon van de fabriek, en dat het bewijs hier is dat de brug gezond genoeg is om oventelemetrie op tijd af te leveren. Het operationeel gevolg is dat u voor protocolspecifieke details in het OT-register moet kijken, niet in de Fabric-feiten.""",
}
