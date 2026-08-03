"""Dutch answers served for the Copilot's predefined questions.

Translated from ``fabric_answers_en``: numbers, identifiers, table names and
model versions are byte-identical to the English pack; only the prose differs.

Formatting note: the Copilot panel renders paragraphs, ``**bold**`` and
``_italic_`` only. Do not use tables, headings or code spans.
"""

from __future__ import annotations

from typing import Final

ANSWERS: Final[dict[str, str]] = {
    # -- command-center ----------------------------------------------------
    "command-center-q1": """**ALERT-HEARTH-SECTOR-07-260725** is de eerste om aan te pakken: het is de enige CRITICAL alert die open staat, en de enige waarachter een herbekleding schuilt.

- Asset **LUX-BF-01**, component **HEARTH-SECTOR-07**, site NS-DEMO-LUX-01
- Resterende levensduur **P50 19.65 dagen**, risicoscore **0.90**, modelvertrouwen 0.78
- Gemeld om **17:58**, nog steeds OPEN

Zestien alerts staan open over de vier sites: **1 critical, 8 warning, 7 info, 2 acknowledged**. Alles overige is een warning of lager - de avondprijspiek tot €280/MWh, de DP780 haspeltemperatuurdrift op COIL-LUX-260725-017, en de Q3 ETS-marge op 6.2%.

Werkorder **WO-DEMO-LUX-1042** is al als concept aangemaakt voor de haard, dus de openstaande beslissing is het inspectievenster, niet de diagnose.""",
    "command-center-q2": """Vier volgende aanbevolen acties staan in de wachtrij, één per domein.

- **Oven** - plan de BF-01 haardkeuring. Risico 0.90, RUL P50 19.65 dagen, werkorder WO-DEMO-LUX-1042 aangemaakt om 18:00.
- **Energie** - keur de lastverschuiving van 17:00-20:00 goed. De tegel toont een gemodelleerde besparingsbandwijdte van circa €4.2k; het toegezegde dispatchvoorstel REC-DEMO-LUX-240725 komt uit op **€2,688.70 (7.25%)** met piekbelasting gedaald van 56.0 naar 51.58 MW.
- **Kwaliteit** - beoordeel de NS-AUTO-DP780-drift op COIL-LUX-260725-017: haspeltemperatuur-bias **+11.4 °C**, risico 0.429, status FAIL.
- **ETS** - de Q3 emissierechten-marge is gedaald naar **6.2%**, met 71% van de emissierechten gebruikt tegen €86/t.

De hoogste impact die vandaag goedgekeurd kan worden is het dispatchvoorstel. De hoogste schade die voorkomen kan worden is de haardstoring, die in de use case gewaardeerd wordt op €8M per ongeplande gebeurtenis.""",
    "command-center-q3": """Ploeg A (06:00-14:00, A. Weber) draagt over aan Ploeg B om **13:45**. Sinds de vorige ploegoverdracht:

- **Geëscaleerd** - de haardmelding ging CRITICAL om 17:58, risico 0.90, RUL P50 19.65 dagen
- **Nieuw** - avondschaarstemeldingswaarschuwing om 15:12 (€280/MWh, 18:30-19:00) en de Q3 ETS-margewaarschuwing om 08:45
- **Bevestigd maar nog open** - DP780 haspeltemperatuurdrift (04:00) en thermokoppel TC-114-drift (21:10)
- **Aangemaakt** - werkorder WO-DEMO-LUX-1042 om 18:00; dispatchvoorstel REC-DEMO-LUX-240725 blijft PENDING_APPROVAL
- **Beslissingen vastgelegd** - 5 auditregistraties, AUD-0001 tot AUD-0005, over oven, energie, kwaliteit, kennis en capaciteit

Er werd niets afgesloten tijdens de ploeg, dus het aantal openstaande meldingen is ongewijzigd op **16 alerts**.""",
    "command-center-q4": """**REC-DEMO-LUX-240725**, het energie-dispatchvoorstel, is de aanbeveling met de hoogste goedkeurbare impact.

- Kosten €37,109.10 basisscenario naar **€34,420.40** geoptimaliseerd - een besparing van **€2,688.70 (7.25%)** op de dag
- Piekbelasting 56.0 MW naar **51.58 MW**, daling van 7.89%
- CO₂ gedaald met **3.29%** bij ongewijzigd tonnage (960 t)
- **0 harde beperkingsschendingen**; status PENDING_APPROVAL, model energy-dispatch-deterministic:2.1.0

Ter referentie: in juli 2026 accepteerde de vloot **100 van 116** aanbevelingen - adoptie 0.862 tegen een doel van 0.70 - voor **11,431 t** verwachte CO₂-vermijding en nul beperkingsschendingen.

De haardkeuring heeft nog meer waarde, maar het is geen aanbeveling om goed te keuren: het beschermt het €8M ongeplande-storing-scenario via een onderhoudsvenster.""",
    # -- operations --------------------------------------------------------
    "operations-q1": """Iets onder het doel. De doorvoer is **128.4 t/h** tegen een doel van **130 t/h** - 1.6 t/h onder, maar wel **+3.2%** ten opzichte van de vorige periode.

- OEE **84.1%** tegen 85%
- Levering op tijd **96.4%** tegen 97%
- Energie-intensiteit **€312/t** tegen €300/t, verbeterd met 4.1%

Het doorvoerprofiel daalt met ongeveer **6 t/h tussen 17:00 en 20:00**. Die daling is bewust: het is herverwarmingsbelasting die buiten het €280/MWh avondschaarstevenster wordt verschoven. Buiten die drie uur draait de lijn op of boven het doel.""",
    "operations-q2": """**LUX-RHF-01**, de herverwarmingsoven, tijdens het venster van 17:00-20:00.

- De doorvoer daalt van circa 130 t/h naar **114-122 t/h** over die drie uur
- REHEAT-BATCH-06 (NS-AUTO-HSLA420, 120 t) werd verplaatst van 18:45 naar **16:45** om het €280/MWh-tijdslot te vermijden
- Stroomafwaarts draagt LUX-HSM-01 de DP780 haspeltemperatuurdrift op COIL-LUX-260725-017

Op de andere sites: BE-HSM-01 walsstand F4 draait **5.8% te hoog op walskracht**, en ES-RHF-01 brandstofzone 02 is **4% rijk op lucht/brandstof**, goed voor circa 180 kWh/h aan vermijdbaar verlies.

De lijngenalogie is LUX-BF-01 naar LUX-BOF-01 naar LUX-CC-01 naar LUX-RHF-01 naar LUX-HSM-01, dus de herverwarmingsstop is wat de walserij ziet als verloren uren - geen walserijfout.""",
    "operations-q3": """**Ploegoverdracht - Ploeg A (06:00-14:00, A. Weber) naar Ploeg B (14:00-22:00, M. Dupont). Overdracht 13:45; Ploeg C neemt over om 22:00.**

Productie: doorvoer **128.4 t/h** tegen 130, OEE **84.1%** tegen 85%, op tijd **96.4%** tegen 97%, energie-intensiteit **€312/t** tegen 300.

Open incidenten - 16 alerts: 1 critical, 8 warning, 7 info, 2 acknowledged.
- CRITICAL ALERT-HEARTH-SECTOR-07-260725 - LUX-BF-01, RUL P50 19.65 dagen, risico 0.90
- WARNING ALERT-ENERGY-SCARCITY-1830 - €280/MWh tussen 18:30 en 19:00
- WARNING ALERT-QUALITY-DRIFT-DP780 - COIL-LUX-260725-017, bevestigd om 04:00
- WARNING ALERT-ETS-ALLOWANCE-Q3 - emissierechten-marge 6.2%

Openstaande punten en beslissingen:
- WO-DEMO-LUX-1042, geplande keuring op HEARTH-SECTOR-07, aangemaakt om 18:00
- REC-DEMO-LUX-240725 dispatchvoorstel nog steeds PENDING_APPROVAL - €2,688.70, 7.25%
- 5 beslissingsregistraties AUD-0001 tot AUD-0005, alle met volledige traceerbaarheid""",
    "operations-q4": """De haardvoorspelling op **LUX-BF-01** verdient prioriteit.

- ALERT-HEARTH-SECTOR-07-260725, CRITICAL, open sinds 17:58
- RUL **P50 19.65 dagen** (P10 18.69 / P90 20.61), risico **0.90**
- Vuurvaste bekleding op **363 mm** tegen een veilig minimum van 300 mm, verdunning circa **3.0 mm/dag**
- Er is een herbekleding-venster nodig binnen **18-24 dagen**, wat een productieplanbeslissing is en geen onderhoudsbeslissing

Op de tweede plaats staat de Q3 ETS-marge op **6.2%** - een commerciële blootstelling op €86/t en geen operationele. Al het overige op het bord valt binnen de normale ploegtriage.""",
    # -- furnace-health ----------------------------------------------------
    "furnace-health-q1": """De thermische signatuur is het patroon dat vijf haardsectoren vormen wanneer ze samen worden gevolgd in plaats van één voor één.

- SECTOR-05, -06, -08 en -09 drijven af met **0.4 °C/h** vanuit 640-664 °C
- **SECTOR-07 stijgt met 3.4 °C/h** vanaf 652 °C en overschrijdt de **700 °C** anomaliedrempel rond uur 14; cellen op 720 °C of hoger worden als critical gemarkeerd
- Koeling ziet er onopvallend uit - delta T **9.4 °C** bij **198 m³/h** - wat precies de sectordivergentie betekenisvol maakt in plaats van een koelfout
- Warmtestroom **118 kW/m²**, koelwater-warmteproxy **214.7 kW**, schijnbare thermische weerstand **8.73**
- De vuurvaste-bekleding-schatting van de sector daalt van **372.0 mm naar 363 mm** over het venster van 24 uur

Model **lining-rul-piml/1.3.0-demo** vertaalt dat naar resterende levensduur, met weging heat_flux_6h_slope 29%, sector_to_ring_temp_delta 24% en cooling_efficiency_residual 18%.""",
    "furnace-health-q2": """**HIGH - risicoscore 0.8995 (90%)** op component HEARTH-SECTOR-07.

- Resterende levensduur **P50 19.65 dagen**, P10 18.69, P90 20.61 - een nauw interval
- Dikte vuurvaste bekleding **363 mm** tegen een geschat minimum van **300 mm**, veroudering circa 3.0 mm/dag
- Model lining-rul-piml/1.3.0-demo, gescoord om 18:45 vandaag
- De tweede eenheid, **LUX-RHF-01**, staat op 34% risico met circa 120 dagen resterend - WATCH, geen actie

Het programmadoel (KPI-FUR-01) is minimaal **21 dagen** vroegtijdige waarschuwing. In de geschiedenis van juli 2026 vuurde elke meldingsepisode precies op **21.0 dagen** - BE-EAF-01 op 2026-06-19 voor een storingsdatum van 2026-07-10, LUX-RHF-01 op 2026-06-09 voor 2026-06-30 - en unplanned_outage_flag was **false op elke rij**.""",
    "furnace-health-q3": """Drie drijfveren dragen 71% van de score.

- **heat_flux_6h_slope - 29%.** Lokale warmtestroom op 118 kW/m² met een stijgende helling over zes uur: warmte bereikt de mantel sneller dan een intacte vuurvaste bekleding toestaat.
- **sector_to_ring_temp_delta - 24%.** SECTOR-07 stijgt met 3.4 °C/h terwijl de naburige sectoren afwijken met 0.4 °C/h. De divergentie, niet de absolute temperatuur, is het signaal.
- **cooling_efficiency_residual - 18%.** Koel-delta T van 9.4 °C bij 198 m³/h verwijdert minder warmte dan de stroming impliceert, zodat de schijnbare thermische weerstand is gedaald naar 8.73.

De resterende 29% is verspreid over langzamere kenmerken. De dikte leest nu **363 mm** tegen een minimum van 300 mm, en bij circa 3.0 mm/dag is dat wat de P50 fixeert op **19.65 dagen**.""",
    "furnace-health-q4": """**WO-DEMO-LUX-1042 - geplande keuring, HEARTH-SECTOR-07, LUX-BF-01.**

Motivering: het fysica-geïnformeerde bekledingsmodel (lining-rul-piml/1.3.0-demo) scoort sector 07 op **risico 0.8995** met **RUL P50 19.65 dagen** (P10 18.69 / P90 20.61). De geschatte dikte is **363 mm** tegen een veilig minimum van **300 mm** en daalt circa **3.0 mm/dag**. De drijfveren zijn een stijgende warmtestroomhelling over zes uur (29%), een sector-tot-ring temperatuurdelta van 3.4 °C/h tegen 0.4 °C/h op naburige sectoren (24%) en een koelefficiëntie-residu (18%). De koelstroom is nominaal op 198 m³/h met delta T 9.4 °C, dus een koelfout verklaart het signaal niet.

Scope: verifieer de mantelthermokoppels met naburige sectoren, registreer de koeling inlaat- en uitlaatdelta T met recente stroomgeschiedenis, en bevestig de dikteschatting voordat het herbekleding-venster opent. **PROC-DEMO-0002** (koelcircuitkeuring en echografie-escalatie, goedgekeurd v3) is van toepassing; **PROC-DEMO-0001** (verificatie van haardsektor-overtemperatuur) is nog in beoordeling.

Planning: keuring dag 1-4, echografie dag 5-8, herbekleding-venster **dag 18-24**. Handelen binnen dat venster is wat dit een geplande gebeurtenis houdt - in de geschiedenis van juli 2026 eindigde elke meldingsepisode in een geplande herbekleding met unplanned_outage_flag false.""",
    # -- energy-optimization -----------------------------------------------
    "energy-optimization-q1": """**REC-DEMO-LUX-240725** - verplaats flexibele herverwarmingslast buiten het avondschaarstevenster.

- Basisscenario **€37,109.10** naar geoptimaliseerd **€34,420.40**, een besparing van **€2,688.70 (7.25%)**
- Piekbelasting **56.0 MW naar 51.58 MW**, daling van 7.89%; verschuifbare belasting 18 MW
- De rendabele verplaatsing: REHEAT-BATCH-06 uit tijdslot 75 (18:45, **€280.00/MWh**, €3,920.00) naar tijdslot 67 (16:45, €97.24/MWh, **€1,361.36**)
- Tonnage ongewijzigd op **960 t** over 8 charges van 120 t / 14 MWh op LUX-RHF-01
- **0 harde beperkingsschendingen**; status PENDING_APPROVAL, model energy-dispatch-deterministic:2.1.0

REHEAT-BATCH-03 blijft vast op 09:45 omdat het als urgent is gemarkeerd. Twee charges worden 15-30 minuten naar voren gehaald, en charges 00 en 07 schuiven naar goedkopere nachtslots.""",
    "energy-optimization-q2": """Omdat één tijdslot meer kost dan het grootste deel van de rest van de dag bij elkaar.

- De day-ahead prijscurve piekt op **€280.00/MWh om 18:45**, tegen 54.85-€112.64/MWh overal elders
- Het herverwarmen van één charge van 120 t / 14 MWh in dat tijdslot kost **€3,920.00**; dezelfde charge om 16:45 (€97.24/MWh) kost **€1,361.36** - een €2,558.64 verschil voor één charge
- Schaarste loopt van **17:00-20:00**, wat ook precies is waar het operationele doorvoerprofiel zijn dip van 6 t/h vertoont
- Een windenergie-PPA-overschot van **12 MWh** is voorspeld voor 02:00-05:00, en dat is waarom charge 07 naar 23:30 en charge 00 naar 02:15 verschuift

De totale kosten van flexibele charges dalen van €12,369.70 naar €9,681.00. De vaste fabrieksbelasting van €24,739.40 is identiek geprijsd in beide schema's, zodat de volledige besparing van **€2,688.70** uit de acht herverwarmingscharges komt.""",
    "energy-optimization-q3": """Alle vijf beperkingen rapporteren SATISFIED, met **0 harde schendingen**.

- **equal_planned_tonnage** - 960.00 t gepland, 960.00 t ingepland. De optimalisator mag staal verplaatsen, nooit verwijderen.
- **urgent_batch_fixed** - REHEAT-BATCH-03 (NS-AUTO-HSLA420, urgent) blijft in tijdslot 39 op 09:45, niet verschoven.
- **minimum_soak_time** - 60 minuten doorwarmtijd bewaard op elke charge.
- **maximum_hold_time** - geen charge gehouden voorbij de limiet van 120 minuten; de grootste verplaatsing is charge 06 op -120 minuten.
- **equipment_capacity** - maximaal 2 gelijktijdige charges op LUX-RHF-01.

Dat maakt het resultaat goedkeurbaar: de besparing van **€2,688.70** wordt volledig gerealiseerd binnen de beperkingenset, en de aanbeveling is geversioneerd (v1) en auditeerbaar als **AUD-0002**.""",
    "energy-optimization-q4": """**Daling van 3.29%** op dit dispatchvoorstel - bereikt door belasting naar schonere tijdsloten te verplaatsen, niet door minder te produceren.

- De netwerk-CO₂-intensiteit gemiddeld circa **244 gCO₂/kWh** over de 96 kwartiertijdsloten, schommelend ruwweg tussen 140 en 310
- Tonnage is ongewijzigd op **960 t**, dus de reductie is pure koolstofarbitrage
- Piekbelasting daalt ook van **56.0 naar 51.58 MW**, wat precies is waar koolstof tijdens schaarsteure-uren gewoonlijk zit
- De gemodelleerde volledige-plan dispatchreductie op het duurzaamheidsoverzicht is **8.7%**

Op vlootniveau in juli 2026 dragen de **100 geaccepteerde** aanbevelingen (van 116, adoptie 0.862 tegen een doel van 0.70) **11,431 t** verwachte CO₂-vermijding.""",
    # -- quality -----------------------------------------------------------
    "quality-q1": """**COIL-LUX-260725-017**, kwaliteit NS-AUTO-DP780 - de enige charge momenteel op FAIL.

- Risicoscore **0.429**, kenmerk YIELD_STRENGTH
- Haspeltemperatuur-bias **+11.4 °C**, de grootste op het bord; de op één na hoogste is +3.0 °C
- Gemeten rekgrens **452.4 MPa** tegen een specificatie van 380-520 MPa - binnen specificatie, maar het laboratoriumresultaat is in REVIEW
- Bronsmelt H-LUX-260725-0040, walserij LUX-HSM-01
- ALERT-QUALITY-DRIFT-DP780 werd bevestigd om 04:00 en staat nog steeds open

Van de 20 charges op het bord is dit degene die een automotieve klant zou zien. De drift werd gemarkeerd vóór het eerste buiten-specificatie laboratoriumresultaat, wat het doel van het signaal is.""",
    "quality-q2": """Één punt is buiten control, en het is het meest recente.

- Gemiddelde **1.9**, sigma **2.2**, dus UCL **8.5** en LCL **-4.7**
- Subgroep 20 leest **11.4** - boven de bovenste controlegrens, en dezelfde **+11.4 °C** haspeltemperatuur-bias gedragen door COIL-LUX-260725-017
- Subgroepen 1-19 blijven binnen de grenzen, met een maximum van 5.8. Er is geen loop, trend of grensomarmend patroon daarvóór
- Procescapaciteit **Cpk 1.18** tegen een doel van **1.33** - capabel, maar niet ruim

Over 30 dagen zijn er **86 defecten**, en haspeltemperatuurdrift is verantwoordelijk voor **34 ervan (39.5%)**, gevolgd door randscheur (21), oppervlakteschaalsvorming (14), diktevariatie (9), bekledingsporositeit (5) en overige (3). Één speciaal-oorzaak-punt op de dominante defectfamilie wijst op een toewijsbare oorzaak, niet op het hercentreren van het proces.""",
    "quality-q3": """De keten achter COIL-LUX-260725-017 is van begin tot eind intact, wat het mogelijk maakt de afwijking te plaatsen.

- Grondstofpartij LOT-FE-017 naar smelt **H-LUX-260725-0040** naar gietpanbehandeling LADLE-017 naar plak SLAB-017
- Herverwarming bij **LUX-RHF-01** (REHEAT-017) naar coil COIL-LUX-260725-017 naar monster SMP-017 naar test YIELD_STRENGTH **452.4 MPa** (REVIEW) naar verzending SHIP-DEMO-017
- Koolstofequivalent 0.420 aan het begin van de reeks, stijgend met 0.002 per charge

De stap die bewoog is de herverwarming: die oven hield charges buiten het schaarstevenster van 17:00-20:00, en de haspeltemperatuur-bias kwam uit op **+11.4 °C**. De afwijking is daarom verbonden aan de herverwarmings- en haspelstappen, niet aan de smelt - niets stroomopwaarts van de gietpan toont een overeenkomend signaal.""",
    "quality-q4": """Haspeltemperatuur **-8 °C** met walskracht **-3%** - de begrensde what-if die dit scherm al uitvoert.

- Voorspelde eerste-passopbrengst verschuift van circa **88% naar circa 95%**, tegen scenariogrenzen van onder 0.90 ervoor en minimaal 0.93 erna
- Model **quality-yield-gbm/2.1.0-demo**; de run is vastgelegd als audit **AUD-0003**
- Het blijft binnen specificatie: rekgrens 452.4 MPa zit in het midden van het venster van 380-520 MPa, dus het verwijderen van de +11.4 °C-bias bedreigt de onderkant niet
- Op het bord vandaag is de hoogwaardige opbrengst 94.8% tegen een doel van 95% en de eerste-passopbrengst 97.1% tegen 97%

Afgezet tegen de programmadoelstelling (KPI) was de hoogwaardige eerste-passopbrengst van juli 2026 **0.9494** tegen het doel van **0.972** - de enige uitkomst die nog tekortschiet, met circa 2.3 punten. Verliezen die maand waren 4,498 t afgewaardeerd, 8,996 t nabewerkt en 1,499 t uitgesloopt over 464 defecten.""",
    # -- sustainability-compliance -----------------------------------------
    "sustainability-compliance-q1": """**71% van de emissierechten gebruikt**, met de Q3-marge gedaald naar **6.2%**.

- Emissierechtenprijs **€86.00/t**
- Verwachte periodeblootstelling **€248,000** bij de huidige emissie-intensiteit
- Scope 1 loopt op **1,368 t CO₂e/dag** voor 960 t staal; Scope 2 volgt het elektriciteitsnet, gemiddeld circa 244 gCO₂/kWh over de 96 intervallen
- CO₂ per ton staal **1.42 t/t** tegen een doel van **1.35**
- ALERT-ETS-ALLOWANCE-Q3 staat open in het grootboek

Voor de laatste maand met gesloten boeken, juli 2026: CO₂-intensiteit **1.019 tCO₂e/t** tegen een doel van 1.638 en een basislijn van 2.10, dus KPI-CO₂-01 is gehaald - met Scope 1 **355,336 t**, Scope 2 **147,868 t** en totale ETS-blootstelling van **€3,974,153**.""",
    "sustainability-compliance-q2": """**In maand 5**, bij het huidige verloop.

- Verbruik staat op **71%** en de projectie voegt circa **3.1 punten per maand** toe
- Maand 4 komt uit op 83.4% - nog onder de richtlijndrempel van **85%**
- Maand 5 komt uit op **86.5%**, dat is het overschrijdingspunt
- De cap van 100% wordt pas bereikt rond maand 10, dus de richtlijnovertreding komt ongeveer vijf maanden eerder
- De Q3-marge is al gedaald naar **6.2%**, wat ALERT-ETS-ALLOWANCE-Q3 bijhoudt

Het accepteren van het huidige dispatchvoorstel verschuift de lijn: **-3.29%** CO₂ op dat schema, en een gemodelleerde reductie van **8.7%** als dispatchoptimalisatie over het hele plan wordt uitgevoerd.""",
    "sustainability-compliance-q3": """Beide staan in hetzelfde append-only grootboek, maar beantwoorden verschillende vragen.

- **Scope 1 - direct.** Verbrandings- en procesgerelateerde emissies op locatie: **1,368 t CO₂e** voor 960 t staal vandaag, effectief 1,425 kg per ton. Het beweegt wanneer het proces verandert, en het maakt niet uit wat het elektriciteitsnet doet.
- **Scope 2 - indirect, ingekochte elektriciteit.** Berekend per kwartier: verbruik in het interval maal de netwerk-CO₂-intensiteit van datzelfde interval - gemiddeld circa **244 gCO₂/kWh**, variërend ruwweg van 40 tot 480 gedurende de dag. Het beweegt wanneer belasting in de tijd wordt verschoven, zelfs bij identiek tonnage.

Dat is waarom het dispatchvoorstel CO₂ reduceert met **3.29%** zonder minder staal te produceren: het raakt alleen Scope 2. Het grootboek bevat **96 onveranderlijke intervalrijen**, en de ETS-blootstelling wordt afgeleid uit hun som tegen €86/t.

In juli 2026 was de verdeling Scope 1 **355,336 t** en Scope 2 **147,868 t**.""",
    "sustainability-compliance-q4": """Keur het dispatchvoorstel goed - het is de enige hefboom die vandaag werkt.

- **REC-DEMO-LUX-240725** - CO₂ **-3.29%** onmiddellijk, bij ongewijzigd tonnage (960 t), 0 harde beperkingsschendingen, nog PENDING_APPROVAL
- Het uitvoeren van dispatchoptimalisatie over het hele plan is gemodelleerd op **8.7%**
- Volgende snelste: ES-RHF-01 brandstofzone 02 is **4% rijk op lucht/brandstof**, goed voor circa 180 kWh/h aan vermijdbaar verlies
- Langzaamste maar grootste: de Scope 1-procesroute zelf, die geen planwijziging bereikt

Bij **€86/t** en met een marge van 6.2% is het dispatchvoorstel datgene wat de richtlijndrempeloverschrijding niet eerder dan maand 5 laat komen. In juli 2026 droegen de 100 geaccepteerde aanbevelingen **11,431 t** verwachte CO₂-vermijding.""",
    # -- knowledge-hub -----------------------------------------------------
    "knowledge-hub-q1": """**PROC-DEMO-0002 - koelcircuitkeuring en echografie-escalatie.** Status APPROVED, versie 3, vastgelegd in sessie SESS-DEMO-015 en geciteerd naar transcript:SESS-DEMO-015#seg-2. Het is de enige goedgekeurde procedure in de bibliotheek, en degene die van toepassing is op de openstaande haardmelding.

Dichtstbijzijnde, maar nog niet bruikbaar: **PROC-DEMO-0001 - verificatie van haardsektor-overtemperatuur**, versie 2, IN_REVIEW, geciteerd naar transcript:SESS-DEMO-014#seg-4 en #seg-7. Het stelt dat naburige mantelthermokoppels moeten worden vergeleken voordat actie wordt ondernomen, dat koeling inlaat- en uitlaatdelta T met recente stroomgeschiedenis moet worden gelezen in plaats van alleen de huidige stroming, en dat alarmen nooit mogen worden omzeild of bedieningselementen worden gewijzigd op basis van interviewbegeleiding.

Gefundeerde antwoorden worden uitsluitend ontleend aan goedgekeurde procedures, dus PROC-DEMO-0001 kan worden gelezen maar wordt niet als antwoord geciteerd totdat een expert het heeft goedgekeurd.""",
    "knowledge-hub-q2": """**Energie en nutsvoorzieningen is de lacune - 58% dekking**, de laagste van de vijf domeinen.

- Hoogoven **82%**
- Kwaliteitslaboratorium **77%**
- Warmwalsstraat **71%**
- Herverwarmingsoven **64%**
- Energie en nutsvoorzieningen **58%**

Drie vastgelegde procedures hebben de 5-daagse review-SLA overschreden (ALERT-KNOWLEDGE-REVIEW-QUEUE), en slechts één van de drie procedures in de bibliotheek is goedgekeurd - dus bruikbare dekking is lager dan vastgelegde dekking in elk domein.

De lacune is het meest voelbaar waar de uittredingen zijn: de haardexpertise achter PROC-DEMO-0001 is vastgelegd maar niet goedgekeurd, terwijl het energiedomein - het domein dat de €2,688.70/dag dispatchbeslissing draagt - het minst vastgelegd heeft om mee te beginnen.""",
    "knowledge-hub-q3": """Twee van de drie procedures zijn nog niet bruikbaar.

- **PROC-DEMO-0001 - verificatie van haardsektor-overtemperatuur.** IN_REVIEW, versie 2, sessie SESS-DEMO-014, twee geciteerde transcriptsegmenten (#seg-4, #seg-7). Direct relevant voor de openstaande LUX-BF-01-melding.
- **PROC-DEMO-0003 - doorwarmtijdherstel van herverwarmingsoven-zone.** DRAFT, versie 1, sessie SESS-DEMO-016, één geciteerd segment (#seg-1).
- Al goedgekeurd: **PROC-DEMO-0002**, versie 3, koelcircuitkeuring en echografie-escalatie.

**ALERT-KNOWLEDGE-REVIEW-QUEUE** markeert drie vastgelegde procedures die de 5-daagse review-SLA hebben overschreden. Goedkeuring is bewust een menselijke stap: de goedkeuring van PROC-DEMO-0002 is vastgelegd als audit **AUD-0004** met actor ke-demo om 10:15, zodat de keten van operatortranscript naar gepubliceerde procedure auditeerbaar blijft.""",
    "knowledge-hub-q4": """Interviewgids, gefundeerd op PROC-DEMO-0001 en de huidige LUX-BF-01-signatuur. Onderwerp **OP-DEMO-014**, senior hoogoven-operator; vastlegging is toestemmingsgebonden en het transcript wordt bewaard onder dat toestemmingsbereik.

- Wanneer een haardsector opwarmt maar de koelstroom normaal leest, wat controleert u als eerste, en in welke volgorde?
- Met welke naburige mantelthermokoppels vergelijkt u, en hoe groot een delta zet u aan tot actie? SECTOR-07 stijgt momenteel met 3.4 °C/h tegen 0.4 °C/h op de naburige sectoren.
- Hoe onderscheidt u vuurvaste-bekleding-degradatie van een driftende sensor? PROC-DEMO-0001 noemt persistentie over aftappingen en langzamere na-aftap-koeling - wat gebruikt u verder?
- Wat vertellen koeling inlaat- en uitlaatdelta T plus recente stroomgeschiedenis dat de huidige stroming alleen niet doet? Vandaag leest het 9.4 °C bij 198 m³/h.
- Bij een geschatte dikte van 363 mm tegen een minimum van 300 mm, wat zou u ertoe brengen het herbekleding-venster naar voren te halen?
- Wat is er eerder op deze oven misgegaan dat een nieuwe operator niet zou verwachten?

Veiligheidsgrens om vast te leggen: alarmen nooit omzeilen of oven- of koelregelingen wijzigen op basis van interviewbegeleiding.""",
    # -- executive-overview ------------------------------------------------
    "executive-overview-q1": """Drie van de vier doelresultaten zijn gehaald, één schiet tekort. Cijfers zijn de juli 2026-afsluiting op de goudtabellen.

- **Energie-intensiteit (KPI-ENE-01)** - **10.63 GJ/t** tegen een doel van 16.77, vanuit een basislijn van 19.5. **Gehaald**, met energiekosten van circa €46.5M tegen een basislijn van €54.1M.
- **CO₂-intensiteit (KPI-CO₂-01)** - **1.019 tCO₂e/t** tegen een doel van 1.638, vanuit een basislijn van 2.10. **Gehaald**.
- **Vroegtijdige bekledings-waarschuwing (KPI-FUR-01)** - elke meldingsepisode vuurde precies op **21.0 dagen**, het gestelde minimum, met unplanned_outage_flag false op elke rij. **Gehaald**.
- **Hoogwaardige eerste-passopbrengst (KPI-QUA-01)** - **0.9494** tegen een doel van 0.972, vanuit een basislijn van 0.90. **Niet gehaald**, circa 2.3 punten tekort.
- Ondersteunend: dispatchadoptie **0.862** (100 van 116 geaccepteerd) tegen een minimum van 0.70. **Gehaald**.

De voortgangsbalken op dit scherm lezen 92, 88, 96 en 100 van 100 voor energie, CO₂, opbrengst en waarschuwingstijd. Kwaliteit is de eerlijke lacune, en het is waar het kennisvastleggingswerk als volgende op wijst.""",
    "executive-overview-q2": """**Saarbrucken (DE)** op prestatie, **Moselle (LU)** op risico.

- Moselle (LU) - energie -14.2%, CO₂ -22.4%, opbrengst +8.1%, **3 openstaande alerts** waaronder de enige critical
- Saarbrucken (DE) - energie **-11.8%**, CO₂ **-18.6%**, opbrengst **+6.4%**, 2 openstaande alerts: laagste op alle drie de maatstaven
- Luik (BE) - energie -13.1%, CO₂ -20.2%, opbrengst +7.2%, 1 openstaande alert
- Asturië (ES) - energie -12.5%, CO₂ -19.4%, opbrengst +7.9%, 2 openstaande alerts

Saarbrucken is de enige site die op alle drie de assen onder het programmadoel zit, en de openstaande punten zijn kostgerelateerd: gietspiegel-oscillatie boven de 4.5 mm-band, en een schrootlaadmix van 3.1% boven het minimalekost-recept.

Moselle leidt op alle assen maar draagt de LUX-BF-01 haardvoorspelling - risico 0.90, 19.65 dagen - wat de €8M-vraag van deze week is.""",
    "executive-overview-q3": """Vier toegezegde resultaten, gemeten op een synthetische pilotdataset, uitgedrukt als doelstellingen waar ze doelstellingen zijn.

- **Doelstellingen** - energie per ton -14%, CO₂ per ton -22%, hoogwaardige opbrengst +8%, minimaal 21 dagen bekledings-waarschuwing.
- **Gemeten in de pilotdata** - energie-intensiteit 10.63 GJ/t en CO₂-intensiteit 1.019 tCO₂e/t in juli 2026; elke bekledingsmelding afgegeven op precies 21.0 dagen zonder ongeplande uitval; hoogwaardige eerste-passopbrengst 0.9494, nog tekortschietend ten opzichte van het doel van 0.972.
- **Gemeten op één dispatchvoorstel vandaag** - €2,688.70 bespaard (7.25%), piekbelasting -7.89%, CO₂ -3.29%, nul beperkingsschendingen.
- **Gemodelleerd, niet gerealiseerd** - één storing voorkomen, gewaardeerd in de use case op €8M per ongeplande haardstoring.

Governance heeft hetzelfde gewicht als de cijfers: vijf beslissingsregistraties over vijf domeinen, drie ervan modelgekoppeld, 100% onveranderlijkheid, en elke aanbeveling vereist een menselijke beslissing voordat deze van kracht wordt.""",
    "executive-overview-q4": """De scheiding is helder, en de tegels zeggen dit in hun tooltips.

**Doelstellingen, geen metingen:** energie per ton -14%, CO₂ per ton -22%, hoogwaardige opbrengst +8%, minimaal 21 dagen vroegtijdige waarschuwing. Dit zijn de vlootbrede use-case-toezeggingen.

**Gemeten in deze demo:**
- Dispatch - **€2,688.70 (7.25%)** bespaard, piek 56.0 naar 51.58 MW, CO₂ **-3.29%**, 0 harde schendingen
- Oven - risico 0.8995 met **P50 19.65 dagen** waarschuwing op LUX-BF-01, onder het doel van 21 dagen voor deze enkele live episode
- Kwaliteit what-if - voorspelde eerste-passopbrengst circa 88% naar circa 95%, model quality-yield-gbm/2.1.0-demo
- Juli 2026 goudafsluiting - 10.63 GJ/t, 1.019 tCO₂e/t, 21.0-daagse waarschuwing bij elke episode, 0.9494 hoogwaardige eerste-passopbrengst

**Gemodelleerd:** de €8M vermeden-storing-waarde en het aantal van één voorkomen storing.

Het ene cijfer dat nooit als bereikt mag worden gepresenteerd is het CO₂-doel: het vlootdoel is -22%, terwijl deze demo met één site -3.29% meet op één dispatchvoorstel.""",
    # -- platform-ops ------------------------------------------------------
    "platform-ops-q1": """**Running** - capaciteit **cap-novasteel-demo-sc**, SKU **F2**, regio Sweden Central, omgeving demo.

- Hervat vanochtend: Paused naar Resuming om 07:27, Resuming naar ReadinessCheck om 07:28, ReadinessCheck naar Running om 07:30 - allemaal door demo-platform-ops met reden "rehearsal"
- Levenscyclusbeleid: nachtelijke pauzecontrole om **01:00 Europe/Luxembourg**
- SKU is schakelbaar tussen F2, F4 en F8; de toestandswijziging is vastgelegd als audit **AUD-0005**
- Werkruimte NovaSteelV3-Demo draagt het lakehouse lh_novasteelv3_core, de KQL-database kql-ns-operations en de ontologie onto_novasteelv3

Dit is een niet-productie capaciteit, en de levenscyclus is bewust beperkt tot starten, pauzeren en SKU-wijziging - elk geauditeerd.""",
    "platform-ops-q2": """**Geen mislukt.** Vier van de vijf meest recente runs zijn geslaagd en één is nog bezig.

- RUN-4821 bronze-to-silver - SUCCEEDED, 17:45, **214 s**
- RUN-4820 silver-to-gold - SUCCEEDED, 17:30, **176 s**
- RUN-4819 semantic-refresh - **RUNNING**, gestart 18:40, 62 s tot nu toe
- RUN-4818 contract-assertions - SUCCEEDED, 17:10, 41 s
- RUN-4817 quarantine-negative-tests - SUCCEEDED, 16:55, 33 s

Beide bewakerstaken zijn geslaagd: contractbeweringen op de gebeurtenisenveloppen, en de negatieve tests die bewijzen dat slechte payloads in quarantaine terechtkomen in plaats van in silver. End-to-end versheid is **12 s**. Het enige openstaande punt is de semantische verversing.""",
    "platform-ops-q3": """Stabiel, en klein - dit is een F2 met een demo-werkbelasting.

- Kosten per uur **€2.80**, schommelend circa €0.40 aan beide zijden over het venster van 06:00-18:00
- Benutting gemiddeld circa **38%**, met een soepel profiel tussen ruwweg 26% en 50%
- Uitgaven tot op heden zijn de som van de 13 uurpunten op de trend
- Telemetrieverversing **12 s**

De vorm is belangrijker dan het totaal: de benutting piekt naast de silver-to-gold en semantic-refresh-runs, en dat is waarom de nachtelijke pauzecontrole om 01:00 niets kost aan doorvoer. Op een F2 is de capaciteit zelf de bodem van de rekening, dus pauzeren tussen demo's is de enige echte hefboom.""",
    "platform-ops-q4": """**Nog niet - RUN-4819 (semantic-refresh) draait nog steeds**, 62 s onderweg, gestart om 18:40.

- De andere vier runs zijn voltooid: bronze-to-silver, silver-to-gold, contract-assertions en quarantine-negative-tests zijn allemaal SUCCEEDED tussen 16:55 en 17:45
- Pauzeren tijdens een semantisch-model-verversing laat het model onververd, zodat dashboards bij hervatting het vorige goud-momentopname serveren
- Capaciteit **cap-novasteel-demo-sc** is F2, Running sinds 07:30, omgeving demo
- Het levenscyclusbeleid voert zijn pauzecontrole al uit om **01:00 Europe/Luxembourg**, op welk moment deze run allang klaar is

Wacht tot RUN-4819 SUCCEEDED meldt, pauzeer dan. De overgang wordt zoals de anderen vastgelegd, met actor en reden.""",
    # -- device-operations -------------------------------------------------
    "device-operations-q1": """**Geen.** Alle **17 apparaten** rapporteren en er zijn **0 actieve incidenten** ingespoten.

- Vloot: 6 in Luxemburg (LUX-BF-01, LUX-BOF-01, LUX-CC-01, LUX-RHF-01, LUX-HSM-01, LUX-UTIL-01), 4 in Duitsland, 4 in België, 3 in Spanje
- **91 sensorsignalen** online over de vloot
- Uptime varieert van **99.10% tot 99.95%** per apparaat
- Simulator: scenario **demo-full**, seed 240726, tick 720, circa 6 verstreken uren op 5 s per tick

Het enige apparaat met een openstaande alert is **LUX-BF-01** - de haardvoorspelling - en dat is een procesconditie, geen apparaatfout: de thermokoppels, warmtestroom- en koelingssignalen publiceren allemaal op schema. Gezondheid op dit scherm wordt gemeten aan de hand van signaalversheid en alarmtellingen, dus een gezonde gateway kan achter een critical procesmelding zitten.""",
    "device-operations-q2": """Het meet de gezondheid van gateways, niet de processgezondheid. Drie ingangen:

- **Uptime** - het aandeel van het venster waarin het apparaat überhaupt heeft gepubliceerd. De vloot zit tussen **99.10% en 99.95%**.
- **Signaalversheid** - elk signaal heeft een verwachte emissieperiode en veroudert zodra die wordt overschreden. Perioden lopen van **1 s** (arc_current op DE-EAF-01) en 5 s (hearth_shell_temperature, local_heat_flux) tot **900 s** (hearth_refractory_estimate, spot_price, grid_carbon_intensity). Eén signaal is gebeurtenis-gedreven zonder vaste periode: hot_metal_temperature, alleen afgegeven bij een aftap.
- **Alarmtelling** - actieve apparaatsalarmen in het venster, gewogen naar ernst.

Een apparaat is gezond wanneer alle drie stand houden, gedegradeerd wanneer versheid of alarmen afnemen, en defect wanneer het stopt met publiceren. Bij tick 720 zonder ingespoten incident zijn alle **17 apparaten en 91 signalen** gezond - wat verklaart waarom de LUX-BF-01-procesmelding naast een schone apparaatscore staat.""",
    "device-operations-q3": """**Geen zijn momenteel verouderd** - alle **91 signalen** zitten binnen hun verwachte periode bij tick 720.

Veroudering wordt per signaal beoordeeld, en de perioden verschillen sterk:
- **1-5 s** - arc_current (DE-EAF-01), hearth_shell_temperature en local_heat_flux (LUX-BF-01), zinc_bath_temperature (BE-GAL-01)
- **10 s** - bath_temperature op LUX-BOF-01 en DE-EAF-01
- **60 s** - production_rate
- **900 s** - hearth_refractory_estimate, spot_price, grid_carbon_intensity
- **Gebeurtenis-gedreven** - hot_metal_temperature, alleen afgegeven bij een aftap

Het is van belang omdat een model slechts zo actueel is als zijn langzaamste invoer. De bekledingsscore is afhankelijk van hearth_refractory_estimate en local_heat_flux: als de 900 s vuurvaste-bekleding-schatting veroudert, stopt de **RUL P50 van 19.65 dagen** met bewegen terwijl de oven blijft verdunnen met circa 3.0 mm/dag. Het dispatchvoorstel heeft dezelfde blootstelling via spot_price en grid_carbon_intensity, beide ook op 900 s.""",
    "device-operations-q4": """Twee manieren, afhankelijk van hoe lang u het wilt laten lopen.

**Enkelvoudig incident - degrading-furnace.** Ernst hoog, standaardduur **30 minuten**, doel **LUX-BF-01**, stuurt local_heat_flux, hearth_refractory_estimate en hearth_shell_temperature aan. Selecteer het in het incidentenpaneel op dit scherm, bevestig het apparaat en de duur, en injecteer.

**Volledig scenario - lining-degradation-21d.** Herstart de simulator op dat scenario in plaats van demo-full om het volledige degradatieverloop te doorlopen in plaats van een uitstap van 30 minuten.

- Huidige toestand: scenario **demo-full**, seed **240726**, tick 720, circa 6 verstreken uren, 5 s ticks, **0 actieve incidenten**
- Andere beschikbare scenario's: healthy-baseline, energy-price-spike, quality-drift, edge-outage-recovery
- Andere incidenten: cooling-water-loss (critical, 15 min), sensor-drift (60 min), sensor-dropout (10 min), energy-price-spike (45 min, LUX-UTIL-01), quality-drift (45 min, LUX-CC-01 en LUX-HSM-01), edge-outage-recovery (20 min)

Verwacht het effect op Ovengezondheid binnen een paar ticks: risicoscore boven 0.80 en RUL P50 tussen **19 en 23 dagen**, dat is de band waarbinnen het scenario is begrensd.""",
    # -- dashboards --------------------------------------------------------
    "dashboards-q1": """**Ochtendploegoverdracht** - Fabrieksmanager, circa **6 minuten**, getagd als dagelijks en triage.

Het loopt Command Center door, dan Operations, dan de openstaande alerts - wat de volgorde is die een ploegoverdracht eigenlijk nodig heeft: wat is critical, wat heeft de lijn gedaan, wat staat er nog open.

Wat het nu zou tonen: **16 openstaande alerts** (1 critical, 8 warning, 7 info, 2 acknowledged), doorvoer **128.4 t/h** tegen 130, OEE **84.1%**, en één werkorder - WO-DEMO-LUX-1042 - aangemaakt voor de haardvoorspelling.

Als de ploegoverdracht specifiek over de oven gaat, gebruik dan **Furnace risk investigation** (circa 8 minuten); dat is de meer diepgaande van de twee.""",
    "dashboards-q2": """**Compliance evidence pack** - Duurzaamheidsfunctionaris en Auditor, circa **7 minuten**, getagd als compliance, audit en eu-ai-act.

Het assembleert het bewijsspoor in plaats van de meetwaarden:
- **5 beslissingsregistraties**, AUD-0001 tot AUD-0005, behorend tot alle **5 domeinen**: oven, energie, kwaliteit, kennis en capaciteit
- **3 ervan modelgekoppeld** - lining-rul-piml/1.3.0-demo, energy-dispatch-milp/1.2.0-demo en quality-yield-gbm/2.1.0-demo
- **100% onveranderlijkheid**, met correlatie-id run-demo-full-240725 dat de oven-, energie- en kwaliteitsbeslissingen koppelt aan één run
- Het emissiegrootboek erachter: 96 append-only intervalrijen, Scope 1 en Scope 2 gescheiden, ETS geprijsd op €86/t
- Menselijke beslissingspunten: elke aanbeveling draagt een actor en een tijdstempel, waarop het EU AI Act-traceerbaarheidsargument rust

Dat is het pakket: wat er is besloten, door welke modelversie, op welke gegevens, en goedgekeurd door wie.""",
    "dashboards-q3": """Zes verzamelingen, elk een vaste route door bestaande schermen.

- **Ochtendploegoverdracht** - Fabrieksmanager, circa 6 min, dagelijks en triage. Wat is critical, wat heeft de lijn gedaan, wat staat er nog open.
- **Furnace risk investigation** - Onderhouds- en Betrouwbaarheidsingenieur, circa 8 min, betrouwbaarheid en grondoorzaak. Is het bekledings-risico reëel, wat veroorzaakt het, wanneer moet er gehandeld worden.
- **Energie- en kostenreview** - Energiemanager, circa 7 min, energie en kosten. Wat kost het schema, wat bespaart het alternatief, wat beperkt het.
- **Kwaliteitsontsnappingsreview** - Kwaliteitsingenieur, circa 6 min, kwaliteit en grondoorzaak. Welke charge, welke stap, welke aanpassing.
- **Compliance evidence pack** - Duurzaamheidsfunctionaris en Auditor, circa 7 min, compliance, audit en eu-ai-act. Wat er besloten is, door welk model, goedgekeurd door wie.
- **Platform health and spend** - Platform Ops, circa 5 min, platform en kosten. Is de pipeline gezond, wat kost het.

Elke verzameling bevat drie of vier geordende schermen en voegt geen eigen gegevens toe - de cijfers blijven eigendom van de schermen waarnaar wordt gelinkt.""",
    "dashboards-q4": """**Furnace risk investigation** - Onderhouds- en Betrouwbaarheidsingenieur, circa **8 minuten**, getagd als betrouwbaarheid en grondoorzaak. Het doorloopt de bekledings-prognose, dan de thermische verkenner, dan de onderhoudsgids - de volgorde waarin het bewijs zich opbouwt.

Wat het nu zou tonen:
- Bekledings-prognose - LUX-BF-01 / HEARTH-SECTOR-07 op risico **0.8995**, RUL **P50 19.65 dagen** (P10 18.69 / P90 20.61)
- Thermische verkenner - SECTOR-07 stijgend met **3.4 °C/h** tegen 0.4 °C/h op de naburige sectoren, kruist de 700 °C anomaliedrempel
- Onderhoudsgids - **WO-DEMO-LUX-1042** open op de sector, herbekleding-venster op dag 18-24

Voor de bredere ploegoverdracht gebruik Ochtendploegoverdracht (circa 6 min); voor de auditomlijsting in plaats van de techniek draagt Compliance evidence pack het beslissingsspoor achter dezelfde oproep.""",
}
