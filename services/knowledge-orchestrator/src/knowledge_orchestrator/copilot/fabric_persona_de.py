"""German answers served for the Copilot's per-persona predefined questions.

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
    "persona-plant-manager-q1": """**Es gibt in diesem Demo-Paket keine einzelne tagesbezogene KPI auf Linienebene.** Der nächstliegende Live-Proxy ist **LUX-RHF-01**, die Wärmofenlinie, die im Knappheitsfenster am weitesten vom Plan abweicht.

- Der Standortdurchsatz liegt bei **128.4 t/h** gegenüber einem Ziel von **130 t/h**, bei einer OEE von **84.1%** gegenüber 85%
- Zwischen **17:00 und 20:00** fällt das Wärmofen-Profil auf etwa **114-122 t/h**
- Dieses Fenster fällt mit dem abendlichen Anstieg auf **€280/MWh** zusammen, sodass der Rückgang eine bewusste Lastverschiebung und kein ungeplanter Stillstand ist
- Nachgelagert muss die Qualität weiter beobachtet werden, weil **COIL-LUX-260725-017** eine **+11.4 °C** Haspeltemperatur-Abweichung trägt

Wenn Sie die betrieblich am weitesten zurückliegende einzelne Linie wissen wollen, priorisieren Sie zuerst das Zeitfenster des Wärmofens. Die Folge ist eher kommerziell als katastrophal: Sie tauschen einen kurzen Durchsatzrückgang gegen günstigere Energie und eine geringere Scope 2-Belastung.""",
    "persona-plant-manager-q2": """**Das Paket enthält kein schichtbezogenes Ausbeutebuch für die Nachtschicht.** Die nächstliegende Evidenz weist auf eine lokale Qualitätsdrift hin, nicht auf eine werkweite metallurgische Veränderung.

- Die aktuelle **FAIL**-Charge ist **COIL-LUX-260725-017** auf **LUX-HSM-01**, mit einer **+11.4 °C** Haspeltemperatur-Abweichung
- Die Streckgrenze liegt bei **452.4 MPa** gegenüber einer Spezifikation von **380-520 MPa**, der Stahl liegt also noch im Band, aber das Laborergebnis ist **REVIEW**
- SPC setzt Stichprobe **20** auf **11.4**, oberhalb der **8.5** oberen Regelgrenze
- Über Juli 2026 hinweg gibt es **86 Fehler**, und Haspeltemperaturdrift erklärt **34 (39.5%)**, vor Kantenriss 21 und Oberflächenzunder 14

Beginnen Sie den Morgen mit der Haspelregelung im Warmwalzwerk, Freigabedisziplin für das DP780-Coil und der Bestätigung, dass die Drift zuordenbar und nicht systemisch war. Das ist die wahrscheinlichste Ursache, auf die Sie zuerst einwirken können.""",
    "persona-plant-manager-q3": """**Beginnen Sie mit dem Herd, dann mit dem Fahrplan, dann mit der DP780-Qualitätsdrift.** Das ist heute Morgen die sauberste Triage-Reihenfolge.

- **1. Herd** - **ALERT-HEARTH-SECTOR-07-260725** ist der einzige kritische Alert: Risiko **0.8995**, **P50 19.65 Tage**, Zustellung **363 mm** gegenüber einem Minimum von **300 mm**
- **2. Energie** - **REC-DEMO-LUX-240725** wartet noch auf Freigabe und hat einen Wert von **€2,688.70** oder **7.25%**, bei einer Spitzenlastsenkung von **56.0 MW** auf **51.58 MW**
- **3. Qualität** - **COIL-LUX-260725-017** trägt eine **+11.4 °C** Haspeltemperatur-Abweichung und die SPC-Verletzung in Stichprobe 20
- Board-Status sind **16 offene Alerts**: **1 kritisch, 8 Warnung, 7 Info, 2 bestätigt**

Diese Reihenfolge schützt zuerst Sicherheit und Verfügbarkeit, erfasst danach den heute größten steuerbaren Kosten- und CO₂-Hebel und kümmert sich anschließend um das sichtbarste qualitätsseitige Kundenrisiko.""",
    "persona-plant-manager-q4": """**84.1%** im Moment, gegenüber einem Ziel von **85%**.

- Der Durchsatz liegt bei **128.4 t/h** gegenüber **130 t/h**
- Die Lieferpünktlichkeit liegt bei **96.4%** gegenüber 97%
- Die Energieintensität liegt bei **€312/t** gegenüber **€300/t**
- Die sichtbare Leistungsbelastung konzentriert sich auf das Knappheitsfenster **17:00-20:00**, in dem der Wärmofendurchsatz bei ungefähr **114-122 t/h** liegt

Das Werk liegt also nahe am OEE-Ziel, aber nicht darauf. Wichtig ist, dass das Defizit bewusst in Kauf genommen wird, um Strom zu **€280/MWh** zu vermeiden, nicht weil die Linie instabil läuft. Die operative Folge ist, den Energie-Trade-off explizit zu halten, statt ihn als versteckten Durchsatzverlust zu behandeln.""",    # -- furnace-operator ----------------------------------------------------
    "persona-furnace-operator-q1": """**Das BF-01-Herdprofil ist asymmetrisch, nicht gleichmäßig heiß.** Beobachtet werden muss **SECTOR-07**.

- **SECTOR-07** steigt mit **3.4 °C/h** von etwa **652 °C**
- Die anderen Sektoren bewegen sich nur um **0.4 °C/h**, also ist das Problem die Divergenz und keine Verschiebung des ganzen Herds
- Der lokale Wärmestrom liegt bei **118 kW/m²**
- Die Kühlung wirkt mit **198 m³/h** und einem Wasser-**ΔT von 9.4 °C** weiterhin nominal
- Die Feuerfest-Schätzung fällt über 24 Stunden von **372 mm** auf **363 mm**

Diese Kombination erklärt, warum das Modell **heat_flux_6h_slope** mit **29%**, **sector_to_ring_temp_delta** mit **24%** und **cooling_efficiency_residual** mit **18%** gewichtet. Die operative Folge ist, dies als reales lokalisiertes Verschleißsignal und nicht als harmlose Aufwärmung des ganzen Ofens zu behandeln.""",
    "persona-furnace-operator-q2": """**Das Demo enthält keinen Sensor mit dem Tag T12-North.** Der nächstliegende Live-Hinweis ist **TC-114** mit Drift und die Schale auf **SECTOR-07**, die ihren Nachbarn davonläuft.

- **TC-114** driftet mit **1.8 °C/h**
- **SECTOR-07** steigt mit **3.4 °C/h** von **652 °C**, während benachbarte Sektoren bei etwa **0.4 °C/h** liegen
- Der Wärmestrom liegt bereits bei **118 kW/m²**
- Das Kühlwasser liegt weiterhin bei **198 m³/h** mit **ΔT 9.4 °C**, sodass eine einfache Erklärung über Wasserverlust nicht zum Muster passt

Die bestgestützte Erklärung ist also nicht „ein schlechter Nord-Sensor“, sondern eine echte lokale thermische Veränderung, die auch im physikinformierten Score sichtbar ist. Die operative Folge ist, TC-114 gegen benachbarte Thermoelemente zu verifizieren, aber weiter so zu handeln, als sei das Herdsignal real, bis diese Prüfung es entkräftet.""",
    "persona-furnace-operator-q3": """**Es gibt in dieser Plattform keine Live-Tabelle für Abstichparameter.** Die nächstliegende governte Evidenz ist **PROC-DEMO-0002**, plus die Tatsache, dass die heutige Auffälligkeit im thermischen Verhalten des Herds und nicht in einem Chemiefenster einer abgestochenen Schmelze liegt.

- **PROC-DEMO-0002** ist die freigegebene Arbeitsanweisung: Status **APPROVED**, Version **3**
- **PROC-DEMO-0001** ist noch **IN_REVIEW**, kann also Prüfungen unterstützen, sollte aber nicht als betriebliche Autorität behandelt werden
- Der aktuelle Kontext ist thermisch: Wärmestrom **118 kW/m²**, Kühlung **198 m³/h**, **ΔT 9.4 °C**, und Sektor 07 steigt mit **3.4 °C/h**
- Die Prozesskette läuft weiterhin Hochofen zu Stahlwerk zu Strangguss; nichts in den Evidenzen rechtfertigt ein Freihandfahren des nächsten Gusses

Erfinden Sie also auf Basis dieses Bildschirms keine Abstichanpassung. Die Folge ist prozedural: Führen Sie zuerst die freigegebenen Inspektions- und Bestätigungsschritte aus und ändern Sie die Gießpraxis nur, wenn eine governte BOF- oder Strangguss-Anweisung dies ausdrücklich vorgibt.""",
    "persona-furnace-operator-q4": """**Die Plattform quantifiziert keine eigenständige Koksraten-Verschleiß-Kurve.** Was sie zeigt, ist, dass das heutige Verschleißsignal von thermischer Belastung dominiert wird.

- Der größte Modelltreiber ist **heat_flux_6h_slope at 29%**
- Danach kommt **sector_to_ring_temp_delta at 24%**
- Dann **cooling_efficiency_residual at 18%**
- Der Live-Thermalzustand dahinter ist ein Wärmestrom von **118 kW/m²**, ein Kühldurchfluss von **198 m³/h** und ein Wasser-**ΔT von 9.4 °C**
- Die Schätzung liegt bereits bei **363 mm** Zustellungsdicke gegenüber einem sicheren Minimum von **300 mm**

Die ehrliche Antwort ist also, dass die Koksrate als Kovariate relevant sein mag, der aktuelle Score aber nicht von einer nachgewiesenen Koksraten-Elastizität getrieben wird. Die operative Folge ist, das zu steuern, was jetzt direkt belegt ist - Wärmelast, Sektorungleichgewicht und Kühlwirksamkeit - statt einer nicht belegten Koks-only-Erklärung nachzujagen.""",    # -- maintenance-engineer ------------------------------------------------
    "persona-maintenance-engineer-q1": """**LUX-BF-01 / HEARTH-SECTOR-07** ist diese Woche klar das Spitzenrisiko.

- Risikowert **0.8995** mit **P50 19.65 Tage**, **P10 18.69**, **P90 20.61**
- Geschätzte Dicke **363 mm** gegenüber einem Minimum von **300 mm**
- Die Degradierung läuft bei rund **3.0 mm/day**
- Die nächste namentlich genannte Anlage im Paket, **LUX-RHF-01**, liegt nur bei rund **34%** Risiko und etwa **120 Tagen** Restlaufzeit
- Arbeitsauftrag **WO-DEMO-LUX-1042** existiert bereits für eine geplante Inspektion

Es gibt keinen nahen Zweiten im selben Dringlichkeitsband. Die Folge ist, das Inspektions- und Neuzustellungsfenster zuerst um BF-01 herum festzuziehen; alles andere ist Watchlist-Arbeit, keine Intervention dieser Woche.""",
    "persona-maintenance-engineer-q2": """**Weil das Live-Thermalbild steiler ist als die historischen Alert-Episoden.** Das Modell sieht ein schnelleres lokales Degradierungssignal und spielt nicht nur den alten Durchschnittspfad erneut ab.

- Die Feuerfest-Schätzung bewegt sich über 24 Stunden von **372 mm** auf **363 mm**
- **SECTOR-07** steigt mit **3.4 °C/h**, während benachbarte Sektoren bei etwa **0.4 °C/h** liegen
- Der Score ist weiterhin in demselben Treiber-Stack verankert: **29%** Wärmestrom-Anstieg, **24%** Sektor-zu-Ring-Delta, **18%** Kühlungseffizienz-Residuum
- Die Kühlung bleibt nominal bei **198 m³/h** und **ΔT 9.4 °C**, was die Sektordivergenz schwerer als Instrumentenrauschen abtun lässt

Historisch zeigen die Alert-Episoden im Juli, dass das System eine geplante Neuzustellung mit **21.0 Tagen** Vorwarnung halten kann. Der heutige Rückgang auf **P50 19.65 Tage** bedeutet, dass die aktuelle Verschleißsignatur bereits innerhalb dieser Komfortmarge liegt. Die Folge ist, Planung und Inspektionskadenz zu verdichten, nicht abzuwarten, bis die Historie es wegmittelt.""",
    "persona-maintenance-engineer-q3": """**Planen Sie jetzt die BF-01-Inspektionsfolge ein und halten Sie das Neuzustellungsfenster innerhalb der Tage 18-24.** Das ist der governte Plan, den die aktuelle Evidenz trägt.

- **WO-DEMO-LUX-1042** ist das Live-Instandhaltungsobjekt
- Inspektionstage **1-4**: Thermoelemente, Kühlein- und -auslauftemperaturen und lokale Historie bestätigen
- Ultraschall und Dickenbestätigung an den Tagen **5-8**
- Geplantes Neuzustellungsfenster **Tage 18-24**
- Ankerwerte sind Risiko **0.8995**, **P50 19.65 Tage** und **363 mm** Zustellung gegenüber **300 mm** Minimum

Verwenden Sie **PROC-DEMO-0002** als freigegebene Betriebsanweisung; **PROC-DEMO-0001** ist noch in Prüfung und sollte beratend bleiben. Die Folge ist, dass Sie noch Zeit haben, dies zu einem geplanten Stopp zu machen - aber nur, wenn die Inspektionsfolge sofort beginnt.""",
    "persona-maintenance-engineer-q4": """**P50 ist 19.65 Tage; P90 ist 20.61 Tage.** Das sind nicht zwei verschiedene Zukünfte, sondern zwei verschiedene Konfidenzpunkte derselben prognostizierten Restnutzungsdauer-Verteilung.

- **P10 18.69 Tage** - eine konservative Untergrenze
- **P50 19.65 Tage** - die Median-Schätzung, also der Wert, den die meisten für die tägliche Planung verwenden
- **P90 20.61 Tage** - eine optimistische Obergrenze mit mehr Restlaufzeit als der Median
- Die Spreizung ist eng: nur **0.96 Tage** von P50 bis P90

Gegenüber einem Programmziel von **21 Tagen** Vorwarnzeit erzählen alle drei Zahlen dieselbe Geschichte: Sie befinden sich praktisch bereits im Handlungsfenster. Die operative Folge ist, mit P50 zu planen, mit P10 den Stresstest zu machen und P90 nur zum Verständnis des Potenzials nach oben zu nutzen - nicht als Rechtfertigung zum Warten.""",    # -- energy-manager ------------------------------------------------------
    "persona-energy-manager-q1": """**02:00-05:00** ist das nächste CO₂-arme Fenster, das im Demo geführt wird, gestützt durch den **12 MWh**-Wind-PPA-Block.

- Das teure, schmutzigere Fenster ist **17:00-20:00**, mit Preisen bis zu **€280/MWh**
- Die Fahrplan-Empfehlung verschiebt flexible Wärmofen-Last aus dieser Knappheitsperiode heraus
- Ein sichtbarer Schritt ist **REHEAT-BATCH-06** von Slot **75** um **18:45** auf Slot **67** um **16:45**
- Die Tageswirkung liegt bei **€37,109.10** Baseline zu **€34,420.40** optimiert, also einer Einsparung von **€2,688.70** oder **7.25%**

Das nächste saubere Fenster ist also nicht nur günstigerer Strom; es ist der Teil des Tages, in dem der Fahrplan Last aufnehmen kann, ohne die CO₂-Prämie der Abendspitze zu bezahlen. Die Folge ist, flexible Erwärmung und Schmelzen vorzuziehen oder später zu fahren, statt sie im Band 17:00-20:00 stehen zu lassen.""",
    "persona-energy-manager-q2": """**Weil die Tonnage sank, die feste Last aber nicht.** Der Anstieg der Energieintensität in der letzten Schicht lässt sich am besten durch die bewusste Wärmofen-Lastverschiebung durch das Knappheitsfenster erklären.

- Die Energieintensität liegt bei **€312/t** gegenüber einem Ziel von **€300/t**
- Der Durchsatz liegt bei **128.4 t/h** gegenüber **130 t/h**, fällt aber im Fenster **17:00-20:00** auf etwa **114-122 t/h**
- Genau dort erreicht der Spotpreis **€280/MWh**
- Der Fahrplan hält die Gesamttonnage bei **960 t** unverändert, sodass der Plan Kosten- und CO₂-Entlastung mit einem kurzzeitigen Durchsatzrückgang erkauft

Mit anderen Worten: Der Anstieg ist ein arithmetischer Effekt aus geringerem momentanen Ausstoß gegenüber einer weitgehend festen Anlagenlast, nicht der Beleg, dass die Anlage plötzlich intrinsisch ineffizient wurde. Die operative Folge ist, €/t zusammen mit dem Fahrplanziel und nicht isoliert zu bewerten.""",
    "persona-energy-manager-q3": """**REC-DEMO-LUX-240725** ist die größte sichtbare Einsparung im Paket, und der Schlüsselschritt ist die Wärmofencharge, die den Slot 18:45 verlässt.

- Baseline **€37,109.10** zu optimiert **€34,420.40** - eine Einsparung von **€2,688.70** oder **7.25%**
- Die Spitzenlast sinkt von **56.0 MW** auf **51.58 MW**
- **REHEAT-BATCH-06** wechselt von Slot **75** um **18:45** und **€280/MWh** zu Slot **67** um **16:45** und **€97.24/MWh**
- Dieser einzelne Schritt senkt die Chargenkosten von **€3,920.00** auf **€1,361.36**
- Im Juli 2026 wurden **100 of 116** Empfehlungen angenommen, Annahmequote **0.862** gegenüber einem Ziel von 0.70

Die wertvollsten Chancen sind also die flexiblen thermischen Lasten, die das Knappheitsband noch berühren. Die Folge ist, den Fahrplan schnell freizugeben und weiter nach Wärmofen- oder Schmelzverschiebungen aus dem Abendfenster mit demselben Muster zu suchen.""",
    "persona-energy-manager-q4": """**Die Plattform führt auf dieser Kachel kein EAF-spezifisches Off-Peak-What-if.** Die nächstliegende gemessene Evidenz ist der bereits auf flexible thermische Last modellierte Fahrplan.

- Dieser Fahrplan reduziert CO₂ um **3.29%** bei unveränderter Tonnage
- Der Optimierungsfall für den Gesamtplan in der Nachhaltigkeitszusammenfassung liegt bei **8.7%**
- Die Netz-CO₂-Intensität mittelt sich auf etwa **244 gCO₂/kWh**, sodass das Verschieben von Last in sauberere Stunden Scope 2 senkt, ohne den Stahlausstoß zu ändern
- Derselbe Fahrplan senkt auch die Spitzenlast von **56.0 MW** auf **51.58 MW**

Ich würde also keine separate EAF-Schmelzen-Zahl nennen, die das Paket nicht belegt. Was die Plattform belegt, ist der Mechanismus: Off-Peak-Verschiebung reduziert Emissionen aus zugekauftem Strom direkt. Die operative Folge ist, Lastverschiebung als realen Scope-2-Hebel zu behandeln, selbst wenn Durchsatz und Tonnage unverändert bleiben.""",    # -- quality-engineer ----------------------------------------------------
    "persona-quality-engineer-q1": """**COIL-LUX-260725-017** ist der einzige aktuelle **FAIL** auf dem Live-Board Luxemburg und derjenige, den Sie zuerst ziehen sollten.

- Güte **NS-AUTO-DP780**
- Risikowert **0.429**
- Haspeltemperatur-Abweichung **+11.4 °C**, die größte sichtbare Abweichung
- Gemessene Streckgrenze **452.4 MPa** gegenüber einer Spezifikation von **380-520 MPa**
- Laborstatus **REVIEW**, und der Qualitätsalert bleibt bestätigt, aber offen

Die Plattform zeigt auf diesem Bildschirm keine separate Multi-Coil-FAIL-Liste nur für Oberflächenfehler, deshalb ist dies die nächstliegende wahrheitsgemäße Antwort auf eine Qualitätsprüfungs-FAIL-Meldung. Die operative Folge ist, dieses Coil vor der Freigabe in Quarantäne zu stellen oder zu prüfen und die Drift dann über Wärmofen und Haspeln zurückzuverfolgen, statt ein allgemeines Laborproblem zu unterstellen.""",
    "persona-quality-engineer-q2": """**Es gibt im Demo-Modell keine Anlage mit dem Namen Line 3.** Die nächstliegende reale Linienevidenz ist **LUX-HSM-01**, und die Drift wird von der Haspeltemperatur und nicht von einer breiten Veränderung des Produktmixes getrieben.

- Juli 2026 verzeichnet **86 Fehler** im Umfang
- **34 defects (39.5%)** sind Haspeltemperaturdrift, vor Kantenriss **21**, Oberflächenzunder **14**, Dickenschwankung **9**, Beschichtung **5** und Sonstiges **3**
- Der aktuelle Sonderpunkt ist Stichprobe **20** mit **11.4**, oberhalb der **8.5** UCL
- Das betroffene Coil ist **COIL-LUX-260725-017** mit **+11.4 °C** Abweichung auf **LUX-HSM-01**

Der Trend lässt sich also nicht am besten als „Line 3 wird schlechter“ lesen; treffender ist eine dominante Fehlerart auf der Warmbandroute. Die operative Folge ist, zuerst die Haspelregelung zu stabilisieren, weil sowohl die Live-Verletzung als auch der monatliche Fehlermix dorthin zeigen.""",
    "persona-quality-engineer-q3": """**Die Plattform bewertet Mittellinienseigerung nicht als eigene KPI.** Die nächstliegende reale Evidenz liegt auf den Strangguss-Eingängen und der Genealogie hinter dem betroffenen Coil.

- Die verfügbaren Live-Stranggussvariablen für diese Art der Triage sind **superheat**, **casting_speed** und **secondary_cooling_flow** auf **LUX-CC-01**
- Die Genealogie ist vollständig: **LOT-FE-017 → H-LUX-260725-0040 → LADLE-017 → SLAB-017 → REHEAT-017 → COIL-LUX-260725-017 → SMP-017 → SHIP-DEMO-017**
- Die gemessene Streckgrenze des Coils liegt bei **452.4 MPa**, weiterhin innerhalb des **380-520 MPa**-Bandes, bei Laborstatus **REVIEW**

Ich würde also das Strangguss-Trio als Korrelationsmenge verwenden und die Genealogie durch Wärmofen und Haspeln offenhalten. Die operative Folge ist, segregationsähnliches Risiko als Routenproblem zu untersuchen, das Strangguss-Thermik und nachgelagertes Wiedererwärmen umfasst, und nicht als isolierte Laborzahl, die aus dem Nichts erscheint.""",
    "persona-quality-engineer-q4": """**Das SPC auf diesem Bildschirm ist nicht direkt für Dicke; es gilt der Haspeltemperatur-Abweichung.** Was es sagt, ist dennoch betrieblich wichtig.

- Mittelwert **1.9**, Sigma **2.2**, obere Regelgrenze **8.5**, untere Regelgrenze **-4.7**
- Stichprobe **20** liest **11.4**, also oberhalb der Kontrolle auf der hohen Seite
- Die Prozesskennzahl liegt bei **Cpk 1.18** gegenüber einem Ziel von **1.33**
- Derselbe Wert **11.4** entspricht der Haspeltemperatur-Abweichung auf **COIL-LUX-260725-017**

SPC sagt also, dass es eine frische zuordenbare Ursache in der thermischen Handhabung gibt, nicht dass das gesamte Prozesszentrum schrittweise abgedriftet ist. Die operative Folge ist, zuerst die zuordenbare Haspeltemperatur-Ursache zu untersuchen; erst danach sollten Sie aus demselben Produktionslauf etwas über die Dickenleistung ableiten.""",    # -- sustainability-officer ---------------------------------------------
    "persona-sustainability-officer-q1": """**Größtenteils ja, aber das Quartal ist nicht mehr komfortabel.** Der Zertifikatsverbrauch liegt bereits bei **71%**, und der Puffer ist auf **6.2%** gesunken.

- Der aktuelle Zertifikatspreis liegt bei **€86/t**
- Das Exposure-Forecast liegt am aktuellen Betriebspunkt bei etwa **€248,000**
- Die aktuelle Fixture-Intensität liegt bei **1.42 tCO₂e/t** gegenüber einem Ziel von **1.35**
- Der Live-Ledger-Alert dazu ist der offene **ALERT-ETS-ALLOWANCE-Q3**
- Der Abschluss für Juli 2026 sieht mit **1.019 tCO₂e/t** gegenüber einem Ziel von **1.638** und einer Baseline von **2.10** weiter stark aus

Das Programm liegt im historischen Scorecard also auf Kurs, aber der Puffer für das laufende Quartal ist dünn. Die operative Folge ist, Lastverschiebung und andere kurzfristige Hebel jetzt weiter zu nutzen, weil einige schwache Betriebstage den verbleibenden Puffer von 6.2% schnell aufbrauchen würden.""",
    "persona-sustainability-officer-q2": """**Die Plattform führt keine CBAM-spezifische Exposure-Spalte.** Der nächstliegende belegte Proxy ist ETS-Exposure plus die aktuelle Scope-1-Intensität.

- Die heutige Scope-1-Last liegt bei **1,368 t CO₂e/day** für **960 t** Stahl, also bei etwa **1,425 kg/t**
- Eine direkte Produktionssteigerung von **10%** bei unveränderter Intensität würde ungefähr **136.8 t CO₂e/day** hinzufügen
- Der Zertifikatsverbrauch liegt bereits bei **71%**, bei einem Exposure-Forecast von **€248,000** und einem Puffer von **6.2%**
- Die aktuelle Betriebsintensität liegt bei **1.42 tCO₂e/t** gegenüber einem Ziel von **1.35**

Ich würde also keine CBAM-Rechnungszahl behaupten, die das Datenpaket nicht enthält. Was die Evidenz sagt, ist, dass eine Tonnagesteigerung von 10% die CO₂-bepreiste Belastung materiell erhöhen würde, sofern sich die Intensität nicht gleichzeitig verbessert. Die operative Folge ist, jede Ausstoßsteigerung mit Effizienz- oder Fahrplanmaßnahmen zu koppeln, statt die Tonnage bei unverändertem Emissionsprofil steigen zu lassen.""",
    "persona-sustainability-officer-q3": """**1.42 tCO₂e/t** auf der aktuellen Betriebs-Fixture.

- Das ist die Live-Tageszahl, nicht der monatliche Durchschnitt bei geschlossenen Büchern
- Sie liegt über dem Ziel von **1.35** für den aktuellen Betriebsmodus
- Für den letzten abgeschlossenen Monat, Juli 2026, lag das Werk bei **1.019 tCO₂e/t**
- Dieses Juli-Ergebnis lag deutlich besser als das Ziel von **1.638** und die Baseline von **2.10**
- Die Scope-Aufteilung für Juli beträgt **355,336 t** Scope 1 und **147,868 t** Scope 2

Ihre aktuelle Intensität ist also schlechter als der monatliche Gold-Abschluss, obwohl der Programmtrend weiterhin vor Ziel liegt. Die operative Folge ist, den Wert 1.42 als Live-Korrektursignal zu lesen - insbesondere rund um thermische Last und Stromzeitpunkt - und nicht als Anlass, am Monatsend-Hauptbuch zu zweifeln.""",
    "persona-sustainability-officer-q4": """**Gegenüber dem Benchmark liegt das Programm im Monat vorn und am Live-Tag hinten.** Beides ist gleichzeitig wahr.

- Aktuelle Fixture: **1.42 tCO₂e/t** gegenüber einem Ziel von **1.35**, also etwa **0.07 tCO₂e/t** zu hoch
- Juli 2026 bei geschlossenen Büchern: **1.019 tCO₂e/t** gegenüber einem Ziel von **1.638** und einer Baseline von **2.10**
- Aktueller Quartalskontext: Zertifikatsverbrauch **71%**, Puffer **6.2%**, prognostiziertes Exposure **€248,000** bei **€86/t**
- Der Fahrplan bleibt der schnellste Hebel und senkt CO₂ im demonstrierten Zeitplan um **3.29%**

Gegenüber dem Benchmark gewinnt das System also im historischen Hauptbuch, steht aber im aktuellen Betriebsfenster unter Druck. Die operative Folge ist, beide Zahlen weiterhin gemeinsam zu zeigen: Der Monatswert beweist, dass das Programm funktioniert, während die Live-Zahl sagt, dass der heutige Betrieb noch aktive Eingriffe braucht.""",    # -- knowledge-engineer --------------------------------------------------
    "persona-knowledge-engineer-q1": """**Das Fixture-Paket speichert keine Glossarabrufhäufigkeit pro Begriff.** Die nächstliegende reale Evidenz ist Nachfrage und Abdeckung nach Wissensdomäne.

- Hochofenabdeckung **82%**
- Qualitätslabor **77%**
- Warmwalzwerk **71%**
- Wärmofen **64%**
- Energie und Versorgung **58%**
- Die Zustände der Arbeitsanweisungen verteilen sich auf **PROC-DEMO-0001 IN_REVIEW v2**, **PROC-DEMO-0002 APPROVED v3** und **PROC-DEMO-0003 DRAFT v1**

Ich kann also aus diesem Paket nicht wahrheitsgemäß den meistabgerufenen Glossarbegriff nennen. Was ich sagen kann, ist, dass die Domänen mit der geringsten Abdeckung die wahrscheinlichsten Nachfragespitzen für Nachschlagen sind, besonders Energie und Wärmofen. Die operative Folge ist, dort zuerst Erfassung und Freigabe zu verbessern, weil sich dort am ehesten nicht unterstützte Fragen ansammeln werden.""",
    "persona-knowledge-engineer-q2": """**Es zitiert die Quellen, die sowohl relevant als auch governbar sind, nicht einfach den beliebigen Text, der abgerufen wurde.** In dieser Plattform ist die Evidenzkette bewusst auditierbar.

- Das Entscheidungsprotokoll zeigt **AUD-0001** bis **AUD-0005**, und alle fünf haben **complete_audit_flag true**
- Arbeitsanweisungen sind nicht gleich: **PROC-DEMO-0002** ist **APPROVED v3**, während **PROC-DEMO-0001** **IN_REVIEW v2** und **PROC-DEMO-0003** **DRAFT v1** ist
- Für vordefinierte Persona-Fragen verwendet der Copilot feste Fabric-Karten, sodass die zitierten Datasets deterministisch und nicht improvisiert sind

Das System bevorzugt also freigegebenes Wissen und vollständige Audit-Ketten vor bloß verfügbarem Text. Die operative Folge ist, dass eine hilfreich aussehende, aber nicht freigegebene Quelle trotzdem aus der finalen Antwort herausbleiben sollte, wenn sie nicht denselben Governance-Standard wie die freigegebene oder auditierte Evidenz erfüllt.""",
    "persona-knowledge-engineer-q3": """**Die Grounding-Architektur ist geschichtet und bewusst eng gehalten.** Die nächstliegende reale Evidenz ist die Kombination aus governter Arbeitsanweisung, Fabric-Fakten und dem Ontologiepfad, der Anlagen entlang der Prozessroute verbindet.

- Governte Textebene: **PROC-DEMO-0002 APPROVED v3**, während **PROC-DEMO-0001 IN_REVIEW v2** und **PROC-DEMO-0003 DRAFT v1** noch außerhalb desselben Vertrauensniveaus liegen
- Analytische Ebene: Fabric-Gold-Fakten für KPI-Historie und KQL-Hot-Views für Live-Zustand
- Strukturelle Ebene: Die Ontologie kann Pfade wie **LUX-BF-01** vorwärts durch die Stahlherstellungskette bis **LUX-HSM-01** verfolgen
- Entscheidungsebene: **AUD-0001..AUD-0005**, alle mit **complete_audit_flag true**

Die Plattform groundet Antworten also auf einer kleinen Anzahl expliziter Abrufpfade statt auf freier Synthese. Die operative Folge ist Vorhersagbarkeit: Sie können prüfen, welche Datenschicht, welcher Prüfungsstatus oder welcher Graphpfad die Antwort getragen hat, statt einer Black-Box-Zusammenfassung zu vertrauen.""",
    "persona-knowledge-engineer-q4": """**Die Plattform zeigt in Fabric keine dedizierte Tabelle für einen „prompt-injection score“.** Die nächstliegende operative Evidenz ist, dass sie bereits freigegebenes-only Grounding, vollständige Audit-Datensätze und menschliche Prüfung vor Aktionen erzwingt.

- Alle fünf Audit-Zeilen **AUD-0001** bis **AUD-0005** sind vollständig
- Nur **PROC-DEMO-0002** ist für den direkten Betriebseinsatz freigegeben; **PROC-DEMO-0001** und **PROC-DEMO-0003** bleiben unter dieser Schwelle
- Empfehlungen wie **REC-DEMO-LUX-240725** warten auf menschliche Freigabe, statt automatisch festgeschrieben zu werden

Die realen Schutzmaßnahmen, die Sie aus den Daten belegen können, sind also Governance-Grenzen, Rückverfolgbarkeit und Human-in-the-Loop-Steuerung. Die operative Folge ist wichtig: Selbst wenn nicht vertrauenswürdiger Text abgerufen würde, fehlt ihm immer noch der direkte Pfad, einen Fahrplan freizugeben, eine Regelaktion zu ändern oder das Audit-Protokoll zu löschen.""",    # -- ot-systems-engineer -------------------------------------------------
    "persona-ot-systems-engineer-q1": """**Keine sind derzeit materiell verspätet oder fehlen.** Der Live-Bestand ist nach den tatsächlich von der Plattform geführten Maßzahlen gesund.

- **17 Geräte** und **91 Signale** sind online
- Die Signal-Aktualität liegt bei den schnellen Live-Feeds unter **5 s**
- Die End-to-End-Aktualität liegt bei etwa **12 s**
- Aktive Vorfälle sind **0**
- Der Alert-Schwellenwert für Quarantäne liegt bei **2% per 15 minutes**, und es gibt hier keinen Hinweis darauf, dass diese Schwelle verletzt wurde

Man muss nur bedenken, dass nicht jedes Signal mit derselben Kadenz aktualisiert werden soll: **hearth_refractory_estimate** ist per Design ein **900,000 ms**-Signal und kein verspäteter 5-Sekunden-Feed. Die operative Folge ist, dass Sie derzeit keine Feed-Triage brauchen; Sie müssen den gesunden Pfad erhalten, während Sie die Prozessalerts separat bearbeiten.""",
    "persona-ot-systems-engineer-q2": """**5,000 ms** für die schnellen Herdsignale, bei einer Gesamt-Aktualität der Plattform von etwa **12 s** end to end.

- **hearth_shell_temperature** veröffentlicht alle **5,000 ms**
- **local_heat_flux** veröffentlicht alle **5,000 ms**
- **hearth_refractory_estimate** ist bewusst langsamer mit **900,000 ms**
- Der Bestand ist insgesamt weiterhin gesund: **17 Geräte**, **91 Signale**, **0 Vorfälle**
- **TC-114** mit einer Drift von **1.8 °C/h** ist ein thermisches Signalproblem und kein Beleg für Netzwerklatenz

Das Sensornetz des Ofens ist also nicht der Engpass. Die operative Folge ist, Datenpfad-Latenz von Prozessverhalten zu trennen: Die 5-Sekunden-Feeds kommen pünktlich an, deshalb sollte der anomale Herdtrend als Anlagenzustand und nicht als Transportartefakt behandelt werden.""",
    "persona-ot-systems-engineer-q3": """**Die Plattform bietet keinen In-Product-PLC-Tag-Provisioning-Wizard.** Das nächstliegende autoritative Objekt ist der Telemetrie-Event-Contract, den das Gateway veröffentlichen muss.

- Das Envelope trägt **source_id**, **asset_id**, **plant_id**, **sequence**, **schema_name** und **schema_version**
- Der Name des Telemetrie-Schemas ist **novasteel.telemetry.v1**
- Eine gute source id sieht aus wie **LUX-BF-01-TC-H07-03**, damit Anlagen- und Signalidentität durch das Gateway explizit bleiben
- Schnelle Tags sollten auf die richtige Kadenz abgestimmt sein, etwa **5,000 ms** für hearth shell temperature, während langsamere Schätzungen mit **900,000 ms** laufen können
- Schlecht geformte Payloads sollen in der Quarantäne landen, statt unbemerkt in Silver zu rutschen

Das Konfigurieren eines neuen PLC-Tag bedeutet hier also, ihn sauber in das veröffentlichte Envelope und Signal-Register abzubilden, nicht eine versteckte Analytiktabelle zu bearbeiten. Die operative Folge ist, dass Contract-Konformität genauso wichtig ist wie der Tag selbst, weil die falsche Form absichtlich zurückgewiesen wird.""",
    "persona-ot-systems-engineer-q4": """**Das Drahtprotokoll wird nicht in Fabric gespeichert.** Was die Plattform belegt, ist das Gateway-vermittelte Muster darüber.

- Der Live-Bestand zeigt **17 Geräte** und **91 Signale** bei **0 Vorfällen**
- Events kommen als versionierte Envelopes mit source ids wie **LUX-BF-01-TC-H07-03** an
- Der Zustand wird über Gateway-Verbindungsstatus, Aktualität und Queue-Verhalten gemessen, nicht über eine Protokollspalte
- Die End-to-End-Aktualität liegt bei etwa **12 s**, und die schnellen thermischen Signale werden weiterhin alle **5,000 ms** veröffentlicht

Ich würde also nicht vortäuschen, dass die Analytikschicht Ihnen sagen kann, ob das Thermofeld Modbus, Profinet oder etwas anderes ist. Die nächstliegende wahrheitsgemäße Antwort ist, dass das Protokoll hinter dem Gateway-Muster der Anlage abstrahiert wird und die Evidenz hier zeigt, dass die Brücke gesund genug ist, um die Ofentelemetrie pünktlich zu liefern. Die operative Folge ist, im OT-Register und nicht in den Fabric-Fakten nach Protokolldetails zu suchen.""",
}