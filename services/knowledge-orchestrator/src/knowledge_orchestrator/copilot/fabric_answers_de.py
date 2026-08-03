"""German answers served for the Copilot's predefined questions.

Translated from ``fabric_answers_en``: numbers, identifiers, table names and
model versions are byte-identical to the English pack; only the prose differs.

Formatting note: the Copilot panel renders paragraphs, ``**bold**`` and
``_italic_`` only. Do not use tables, headings or code spans.
"""

from __future__ import annotations

from typing import Final

ANSWERS: Final[dict[str, str]] = {
    # -- command-center ----------------------------------------------------
    "command-center-q1": """**ALERT-HEARTH-SECTOR-07-260725** hat höchste Priorität: Es ist der einzige offene CRITICAL-Alert und der einzige mit einer anstehenden Neuzustellung.

- Anlage **LUX-BF-01**, Komponente **HEARTH-SECTOR-07**, Standort NS-DEMO-LUX-01
- Restnutzungsdauer **P50 19.65 Tage**, Risikowert **0.90**, Modellkonfidenz 0.78
- Gemeldet um **17:58**, noch OPEN

Sechzehn Alerts sind über alle vier Standorte verteilt offen: **1 kritisch, 8 Warnung, 7 Info, 2 bestätigt**. Alles andere ist eine Warnung oder niedriger - der Abendpreisanstieg auf €280/MWh, der DP780-Haspeldrift auf COIL-LUX-260725-017 und der Q3-ETS-Puffer bei 6.2%.

Arbeitsauftrag **WO-DEMO-LUX-1042** ist bereits für den Herd angelegt; die anstehende Entscheidung betrifft das Inspektionsfenster, nicht die Diagnose.""",
    "command-center-q2": """Vier empfohlene Maßnahmen sind in der Warteschlange, eine je Bereich.

- **Herd** - Inspektion des BF-01-Herds einplanen. Risikowert 0.90, Restnutzungsdauer P50 19.65 Tage, Arbeitsauftrag WO-DEMO-LUX-1042 angelegt um 18:00.
- **Energie** - Lastverschiebung 17:00-20:00 freigeben. Die Kachel zeigt ein modelliertes Einsparband von rund €4.2k; der bestätigte Fahrplan REC-DEMO-LUX-240725 ergibt **€2,688.70 (7.25%)** Einsparung bei einem Spitzenlastabfall von 56.0 auf 51.58 MW.
- **Qualität** - Den NS-AUTO-DP780-Drift auf COIL-LUX-260725-017 prüfen: Haspeltemperatur-Abweichung **+11.4 °C**, Risikowert 0.429, Status FAIL.
- **ETS** - Q3-Zertifikat-Puffer auf **6.2%** gesunken, bei 71% verbrauchten Zertifikaten zu €86/t.

Die heute freigebbare Maßnahme mit dem höchsten Nutzenpotenzial ist der Fahrplan. Der größte vermeidbare Schaden ist der Herdausfall, den das Anwendungsszenario mit €8M pro ungeplantem Ereignis bewertet.""",
    "command-center-q3": """Schicht A (06:00-14:00, A. Weber) übergibt an Schicht B um **13:45**. Seit der letzten Schichtübergabe:

- **Eskaliert** - der Herdalert wurde um 17:58 CRITICAL, Risikowert 0.90, Restnutzungsdauer P50 19.65 Tage
- **Neu** - Abend-Knappheitswarnung um 15:12 (€280/MWh, 18:30-19:00) und Q3-ETS-Puffer-Warnung um 08:45
- **Bestätigt, aber noch offen** - DP780-Haspeldrift (04:00) und Thermoelement TC-114-Drift (21:10)
- **Angelegt** - Arbeitsauftrag WO-DEMO-LUX-1042 um 18:00; Fahrplan REC-DEMO-LUX-240725 noch PENDING_APPROVAL
- **Entscheidungen erfasst** - 5 Auditeinträge, AUD-0001 bis AUD-0005, in den Bereichen Herd, Energie, Qualität, Wissensmanagement und Kapazität

Während der Schicht wurde nichts geschlossen, sodass die offene Anzahl unverändert bei **16 Alerts** liegt.""",
    "command-center-q4": """**REC-DEMO-LUX-240725**, der Energie-Fahrplan, ist die Empfehlung mit dem höchsten freigebbaren Nutzenpotenzial.

- Kosten €37,109.10 Baseline zu **€34,420.40** optimiert - eine Einsparung von **€2,688.70 (7.25%)** für den Tag
- Spitzenlast 56.0 MW auf **51.58 MW**, minus 7.89%
- CO₂ um **3.29%** gesunken bei unverändertem Durchsatz (960 t)
- **0 Hard-Constraint-Verletzungen**; Status PENDING_APPROVAL, Modell energy-dispatch-deterministic:2.1.0

Im Vergleich: Die Flotte nahm im Juli 2026 **100 von 116** Empfehlungen an - Annahmequote 0.862 gegen ein Ziel von 0.70 - mit **11,431 t** erwartetem CO₂-Einsparpotenzial und null Constraint-Verletzungen.

Die Herdinspektion hat noch höheres Nutzenpotenzial, ist aber keine freizugebende Empfehlung: Sie sichert den €8M-Fall für ungeplante Ausfälle durch ein geplantes Wartungsfenster.""",
    # -- operations --------------------------------------------------------
    "operations-q1": """Knapp unter Ziel. Der Durchsatz liegt bei **128.4 t/h** gegenüber einem Zielwert von **130 t/h** - 1.6 t/h darunter, jedoch **+3.2%** gegenüber der Vorperiode.

- OEE **84.1%** gegen 85%
- Lieferpünktlichkeit **96.4%** gegen 97%
- Energieintensität **€312/t** gegen €300/t, verbessert um 4.1%

Das Durchsatzprofil sinkt zwischen **17:00 und 20:00** um rund **6 t/h**. Dieser Einbruch ist beabsichtigt: Es handelt sich um Wärmofen-Lasten, die aus dem €280/MWh-Abend-Knappheitsfenster verschoben werden. Außerhalb dieser drei Stunden läuft die Linie am oder über dem Zielwert.""",
    "operations-q2": """**LUX-RHF-01**, der Wärmofen, im Zeitfenster 17:00-20:00.

- Der Durchsatz fällt in diesen drei Stunden von rund 130 t/h auf **114-122 t/h**
- REHEAT-BATCH-06 (NS-AUTO-HSLA420, 120 t) wurde von 18:45 auf **16:45** vorgezogen, um das €280/MWh-Zeitfenster zu meiden
- Nachgelagert zeigt LUX-HSM-01 den DP780-Haspeldrift auf COIL-LUX-260725-017

An den anderen Standorten: BE-HSM-01 Gerüst F4 läuft **5.8% zu hoch auf Walzkraft**, und ES-RHF-01 Brennerzone 02 ist **4% fett im Luft/Gas-Verhältnis**, was rund 180 kWh/h vermeidbare Verluste bedeutet.

Die Anlagenkette ist LUX-BF-01 - LUX-BOF-01 - LUX-CC-01 - LUX-RHF-01 - LUX-HSM-01, sodass die Wärmofen-Haltezeit das ist, was das Walzwerk als verlorene Stunden registriert - kein Walzwerkfehler.""",
    "operations-q3": """**Schichtübergabe - Schicht A (06:00-14:00, A. Weber) an Schicht B (14:00-22:00, M. Dupont). Übergabe 13:45; Schicht C übernimmt um 22:00.**

Produktion: Durchsatz **128.4 t/h** gegen 130, OEE **84.1%** gegen 85%, Pünktlichkeit **96.4%** gegen 97%, Energieintensität **€312/t** gegen 300.

Offene Vorfälle - 16 Alerts: 1 kritisch, 8 Warnung, 7 Info, 2 bestätigt.
- CRITICAL ALERT-HEARTH-SECTOR-07-260725 - LUX-BF-01, Restnutzungsdauer P50 19.65 Tage, Risikowert 0.90
- WARNING ALERT-ENERGY-SCARCITY-1830 - €280/MWh zwischen 18:30 und 19:00
- WARNING ALERT-QUALITY-DRIFT-DP780 - COIL-LUX-260725-017, bestätigt um 04:00
- WARNING ALERT-ETS-ALLOWANCE-Q3 - Zertifikat-Puffer 6.2%

Offene Punkte und Entscheidungen:
- WO-DEMO-LUX-1042, geplante Inspektion an HEARTH-SECTOR-07, angelegt 18:00
- Fahrplan REC-DEMO-LUX-240725 noch PENDING_APPROVAL - €2,688.70, 7.25%
- 5 Entscheidungsprotokoll-Einträge AUD-0001 bis AUD-0005, alle mit vollständiger Rückverfolgbarkeit""",
    "operations-q4": """Die Herdprognose auf **LUX-BF-01** hat höchste Priorität.

- ALERT-HEARTH-SECTOR-07-260725, CRITICAL, offen seit 17:58
- Restnutzungsdauer **P50 19.65 Tage** (P10 18.69 / P90 20.61), Risikowert **0.90**
- Feuerfeste Zustellung bei **363 mm** gegenüber einem sicheren Minimum von 300 mm, Ausdünnung ca. **3.0 mm/Tag**
- Ein Neuzustellungsfenster innerhalb von **18-24 Tagen** ist erforderlich - eher eine Produktionsplanung als eine Wartungsentscheidung

Zweite Priorität ist der Q3-ETS-Puffer bei **6.2%** - ein kommerzielles Kostenrisiko bei €86/t, kein operatives. Alles andere auf dem Board liegt im normalen Schichttriage-Bereich.""",
    # -- furnace-health ----------------------------------------------------
    "furnace-health-q1": """Das thermische Muster ergibt sich aus dem gemeinsamen Verlauf der fünf Herdsektoren - nicht aus der Einzelbetrachtung.

- SECTOR-05, -06, -08 und -09 driften bei **0.4 °C/h** von 640-664 °C
- **SECTOR-07 steigt mit 3.4 °C/h** von 652 °C und überschreitet den **700 °C**-Anomaliegrenzwert nach ca. 14 Stunden; Zellen bei 720 °C oder darüber werden als kritisch markiert
- Die Kühlung zeigt keine Auffälligkeiten - Delta T **9.4 °C** bei **198 m³/h** - was die Sektordivergenz bedeutsam macht und keinen Kühlfehler widerspiegelt
- Wärmestrom **118 kW/m²**, Kühlwasser-Wärme-Proxy **214.7 kW**, scheinbarer Wärmewiderstand **8.73**
- Die Feuerfest-Schätzung am Sektor fällt im 24-Stunden-Fenster von **372.0 mm auf 363 mm**

Modell **lining-rul-piml/1.3.0-demo** berechnet daraus die Restnutzungsdauer mit Gewichtungen heat_flux_6h_slope 29%, sector_to_ring_temp_delta 24% und cooling_efficiency_residual 18%.""",
    "furnace-health-q2": """**HIGH - Risikowert 0.8995 (90%)** für Komponente HEARTH-SECTOR-07.

- Restnutzungsdauer **P50 19.65 Tage**, P10 18.69, P90 20.61 - ein enger Bereich
- Zustellungsdicke **363 mm** gegenüber einem geschätzten Minimum von **300 mm**, Degradierung ca. 3.0 mm/Tag
- Modell lining-rul-piml/1.3.0-demo, bewertet um 18:45 heute
- Die zweite Anlage, **LUX-RHF-01**, liegt bei 34% Risikowert mit ca. 120 verbleibenden Tagen - WATCH, kein Handlungsbedarf

Das Programmziel (KPI-FUR-01) ist mindestens **21 Tage** Vorwarnzeit. In der Juli-2026-Historie hat jede Alert-Episode genau bei **21.0 Tagen** ausgelöst - BE-EAF-01 am 2026-06-19 für ein Ausfallsdatum 2026-07-10, LUX-RHF-01 am 2026-06-09 für 2026-06-30 - und unplanned_outage_flag war **false in jeder Zeile**.""",
    "furnace-health-q3": """Drei Treiber tragen 71% des Risikowerts.

- **heat_flux_6h_slope - 29%.** Lokaler Wärmestrom bei 118 kW/m² mit einem steigenden Sechs-Stunden-Anstieg: Die Wärme erreicht die Schale schneller als eine intakte Zustellung zulässt.
- **sector_to_ring_temp_delta - 24%.** SECTOR-07 steigt mit 3.4 °C/h, während Nachbarsektoren bei 0.4 °C/h driften. Die Divergenz - nicht die absolute Temperatur - ist das Signal.
- **cooling_efficiency_residual - 18%.** Kühl-Delta-T von 9.4 °C bei 198 m³/h entzieht weniger Wärme als der Durchfluss impliziert, sodass der scheinbare Wärmewiderstand auf 8.73 gesunken ist.

Die verbleibenden 29% verteilen sich auf langsamere Merkmale. Die aktuelle Dicke beträgt **363 mm** gegenüber einem Minimum von 300 mm; bei ca. 3.0 mm/Tag ergibt sich daraus der P50-Wert von **19.65 Tagen**.""",
    "furnace-health-q4": """**WO-DEMO-LUX-1042 - geplante Inspektion, HEARTH-SECTOR-07, LUX-BF-01.**

Begründung: Das physikbasierte Zustellungsmodell (lining-rul-piml/1.3.0-demo) bewertet Sektor 07 mit **Risikowert 0.8995** und **Restnutzungsdauer P50 19.65 Tage** (P10 18.69 / P90 20.61). Die geschätzte Dicke beträgt **363 mm** gegenüber einem Sicherheitsminimum von **300 mm** und fällt ca. **3.0 mm/Tag**. Die Treiber sind ein steigender Sechs-Stunden-Wärmestrom-Anstieg (29%), ein Sektor-zu-Ring-Temperaturdelta von 3.4 °C/h gegenüber 0.4 °C/h bei Nachbarsektoren (24%) und ein Kühlungseffizienz-Residuum (18%). Der Kühldurchfluss ist nominal bei 198 m³/h mit Delta T 9.4 °C, sodass ein Kühlfehler das Signal nicht erklärt.

Umfang: Schalen-Thermoelemente mit Nachbarsektoren abgleichen, Kühlein- und -auslauf-Delta T mit jüngster Durchflusshistorie aufzeichnen und die Dickenabschätzung vor Öffnung des Neuzustellungsfensters bestätigen. **PROC-DEMO-0002** (Kühlkreis-Inspektion und Ultraschall-Eskalation, freigegeben v3) gilt; **PROC-DEMO-0001** (Herdsektor-Übertemperatur-Verifikation) ist noch in Prüfung.

Zeitplan: Inspektion Tage 1-4, Ultraschall Tage 5-8, Neuzustellungsfenster **Tage 18-24**. Handeln innerhalb dieses Fensters ist entscheidend, damit das Ereignis geplant bleibt - in der Juli-2026-Historie endete jede Alert-Episode mit einer geplanten Neuzustellung bei unplanned_outage_flag false.""",
    # -- energy-optimization -----------------------------------------------
    "energy-optimization-q1": """**REC-DEMO-LUX-240725** - flexible Wärmofen-Lasten aus dem Abend-Knappheitsfenster verschieben.

- Baseline **€37,109.10** zu optimiert **€34,420.40**, eine Einsparung von **€2,688.70 (7.25%)**
- Spitzenlast **56.0 MW auf 51.58 MW**, minus 7.89%; verschiebbare Last 18 MW
- Die entscheidende Verschiebung: REHEAT-BATCH-06 aus Zeitfenster 75 (18:45, **€280.00/MWh**, €3,920.00) in Zeitfenster 67 (16:45, €97.24/MWh, **€1,361.36**)
- Durchsatz unverändert bei **960 t** über 8 Chargen à 120 t / 14 MWh auf LUX-RHF-01
- **0 Hard-Constraint-Verletzungen**; Status PENDING_APPROVAL, Modell energy-dispatch-deterministic:2.1.0

REHEAT-BATCH-03 bleibt um 09:45 fixiert, da er als dringend markiert ist. Zwei Chargen werden 15-30 Minuten vorgezogen, und Chargen 00 und 07 werden in günstigere Nachtzeitfenster verschoben.""",
    "energy-optimization-q2": """Weil ein einziges Zeitfenster mehr kostet als der Großteil des restlichen Tages zusammen.

- Die Day-Ahead-Kurve erreicht bei 18:45 ihr Maximum von **€280.00/MWh**, gegenüber 54.85-€112.64/MWh im übrigen Tagesverlauf
- Das Erwärmen einer einzelnen Charge von 120 t / 14 MWh in diesem Zeitfenster kostet **€3,920.00**; dieselbe Charge um 16:45 (€97.24/MWh) kostet **€1,361.36** - eine Differenz von €2,558.64 aus einer einzigen Charge
- Das Knappheitsfenster dauert von **17:00 bis 20:00** - genau dort, wo das Betriebsdurchsatzprofil seinen 6 t/h-Einbruch zeigt
- Ein Wind-PPA-Überschuss von **12 MWh** wird für 02:00-05:00 prognostiziert, weshalb Charge 07 auf 23:30 und Charge 00 auf 02:15 verschoben wird

Die Gesamtkosten der flexiblen Chargen sinken von €12,369.70 auf €9,681.00. Die feste Anlagenlast von €24,739.40 ist in beiden Fahrplänen identisch bewertet, sodass die gesamte **€2,688.70**-Einsparung aus den acht Wärmofen-Chargen stammt.""",
    "energy-optimization-q3": """Alle fünf Constraints melden SATISFIED, mit **0 Hard-Verletzungen**.

- **equal_planned_tonnage** - 960.00 t geplant, 960.00 t eingeplant. Der Optimierer darf Stahl verschieben, nicht entfernen.
- **urgent_batch_fixed** - REHEAT-BATCH-03 (NS-AUTO-HSLA420, dringend) bleibt in Zeitfenster 39 um 09:45, nicht verschoben.
- **minimum_soak_time** - 60 Minuten Durchwärmzeit bei jeder Charge eingehalten.
- **maximum_hold_time** - keine Charge über das 120-Minuten-Limit hinaus gehalten; die größte Verschiebung ist Charge 06 mit -120 Minuten.
- **equipment_capacity** - höchstens 2 gleichzeitige Chargen auf LUX-RHF-01.

Das macht das Ergebnis freigabefähig: Die **€2,688.70**-Einsparung wird vollständig innerhalb des Constraint-Sets erzielt, und die Empfehlung ist versioniert (v1) und auditierbar als **AUD-0002**.""",
    "energy-optimization-q4": """**Minus 3.29%** bei diesem Fahrplan - erreicht durch Verlagerung der Last in sauberere Zeitfenster, nicht durch geringere Produktion.

- Die Netz-CO₂-Intensität mittelt sich über die 96 Viertelstunden-Intervalle auf ca. **244 gCO₂/kWh**, mit Schwankungen von rund 140 bis 310
- Der Durchsatz bleibt bei **960 t**, sodass die Reduktion reines CO₂-Arbitrage ist
- Die Spitzenlast sinkt ebenfalls von **56.0 auf 51.58 MW**, wo der CO₂-Anteil der Knappheitsstunden üblicherweise liegt
- Die modellierte CO₂-Reduktion des vollständigen Plan-Fahrplans laut Nachhaltigkeitszusammenfassung beträgt **8.7%**

Auf Flottenebene im Juli 2026 tragen die **100 angenommenen** Empfehlungen (von 116, Annahmequote 0.862 gegen ein Ziel von 0.70) **11,431 t** erwartetes CO₂-Einsparpotenzial.""",
    # -- quality -----------------------------------------------------------
    "quality-q1": """**COIL-LUX-260725-017**, Güte NS-AUTO-DP780 - die einzige Charge mit aktuellem Status FAIL.

- Risikowert **0.429**, Merkmal YIELD_STRENGTH
- Haspeltemperatur-Abweichung **+11.4 °C**, die größte auf dem Board; der nächsthöhere Wert ist +3.0 °C
- Gemessene Streckgrenze **452.4 MPa** gegenüber einer Spezifikation von 380-520 MPa - innerhalb der Spezifikation, aber das Laborergebnis befindet sich in REVIEW
- Ausgangsschmelze H-LUX-260725-0040, Walzwerk LUX-HSM-01
- ALERT-QUALITY-DRIFT-DP780 wurde um 04:00 bestätigt und ist noch offen

Von den 20 Chargen auf dem Board ist dies die für einen Automobilkunden relevante. Der Drift wurde vor dem ersten außerspezifikationsgemäßen Laborergebnis gemeldet - das ist der Zweck des Signals.""",
    "quality-q2": """Ein Punkt liegt außerhalb der Regelgrenzen - und es ist der aktuellste.

- Mittelwert **1.9**, Sigma **2.2**, daher OGW **8.5** und UGW **-4.7**
- Stichprobe 20 liest **11.4** - über der oberen Regelgrenze und identisch mit der **+11.4 °C**-Haspeltemperatur-Abweichung bei COIL-LUX-260725-017
- Stichproben 1-19 bleiben innerhalb der Grenzen, mit einem Maximum von 5.8. Davor kein Lauf, kein Trend und kein Grenznähe-Muster
- Prozesskennzahl **Cpk 1.18** gegen ein Ziel von **1.33** - fähig, aber nicht komfortabel

Über 30 Tage gibt es **86 Fehler**, und Haspeltemperaturdrift verursacht **34 davon (39.5%)**, vor Kantenriss (21), Oberflächenzunder (14), Dickenschwankung (9), Beschichtungsporosität (5) und Sonstiges (3). Ein einzelner Sonderpunkt bei der dominanten Fehlerfamilie weist auf eine zuordenbare Ursache hin, nicht auf eine Prozessneuzentrierung.""",
    "quality-q3": """Die Prozesskette hinter COIL-LUX-260725-017 ist lückenlos, was die Zuordnung der Abweichung ermöglicht.

- Rohstoffcharge LOT-FE-017 zu Schmelze **H-LUX-260725-0040** zu Pfannenbehandlung LADLE-017 zu Bramme SLAB-017
- Erwärmen in **LUX-RHF-01** (REHEAT-017) zu Coil COIL-LUX-260725-017 zu Probe SMP-017 zu Prüfung YIELD_STRENGTH **452.4 MPa** (REVIEW) zu Lieferung SHIP-DEMO-017
- Kohlenstoffäquivalent 0.420 am Anfang der Kette, steigt um 0.002 pro Charge

Der veränderte Prozessschritt ist der Wärmofen: Dieser hielt Chargen aus dem 17:00-20:00-Knappheitsfenster zurück, und die Haspeltemperatur-Abweichung betrug **+11.4 °C**. Die Abweichung lässt sich daher dem Erwärm- und Haspelschritt zuordnen, nicht der Schmelze - nichts stromaufwärts der Pfanne zeigt ein passendes Signal.""",
    "quality-q4": """Haspeltemperatur **-8 °C** bei Walzkraft **-3%** - das ist das begrenzte What-if, das dieser Bildschirm bereits ausführt.

- Die vorhergesagte Erstdurchlaufausbeute steigt von ca. **88% auf ca. 95%**, bei Szenariogrenzen von unter 0.90 vorher und mindestens 0.93 danach
- Modell **quality-yield-gbm/2.1.0-demo**; der Lauf ist als Audit **AUD-0003** erfasst
- Es bleibt innerhalb der Spezifikation: Streckgrenze 452.4 MPa liegt in der Mitte des 380-520-MPa-Fensters, sodass das Entfernen der +11.4 °C-Abweichung die Untergrenze nicht gefährdet
- Auf dem Board heute: Hochgütenausbeute 94.8% gegen ein Ziel von 95% und Erstdurchlaufausbeute 97.1% gegen 97%

Gegenüber dem Programmziel lag die Hochgüten-Erstdurchlaufausbeute im Juli 2026 bei **0.9494** gegen das **0.972**-Ziel - das einzige noch nicht erreichte Ergebnis, rund 2.3 Punkte darunter. Die Verluste in diesem Monat betrugen 4,498 t abgestuft, 8,996 t nachgearbeitet und 1,499 t Ausschuss über 464 Fehler.""",
    # -- sustainability-compliance -----------------------------------------
    "sustainability-compliance-q1": """**71% der Zertifikate verbraucht**, Q3-Puffer auf **6.2%** gesunken.

- Zertifikatspreis **€86.00/t**
- Prognostiziertes Periodenrisiko **€248,000** bei aktueller Emissionsintensität
- Scope 1 liegt bei **1,368 t CO₂e/Tag** für 960 t Stahl; Scope 2 folgt dem Netz mit durchschnittlich ca. 244 gCO₂/kWh über die 96 Intervalle
- CO₂ pro Tonne Stahl **1.42 t/t** gegen ein Ziel von **1.35**
- ALERT-ETS-ALLOWANCE-Q3 ist im Hauptbuch offen

Für den letzten Monat mit geschlossenen Büchern, Juli 2026: CO₂-Intensität **1.019 tCO₂e/t** gegen ein Ziel von 1.638 und eine Baseline von 2.10, sodass KPI-CO₂-01 erfüllt ist - mit Scope 1 **355,336 t**, Scope 2 **147,868 t** und einem ETS-Gesamtrisiko von **€3,974,153**.""",
    "sustainability-compliance-q2": """**Im Monat 5**, auf dem aktuellen Kurs.

- Der Verbrauch steht bei **71%** und die Hochrechnung fügt ca. **3.1 Punkte pro Monat** hinzu
- Monat 4 endet bei 83.4% - noch unter dem **85%**-Richtwert
- Monat 5 endet bei **86.5%**, das ist die Überschreitung
- Die 100%-Grenze wird erst in ca. Monat 10 erreicht, sodass die Richtwert-Verletzung rund fünf Monate früher eintritt
- Der Q3-Puffer ist bereits auf **6.2%** gesunken, was ALERT-ETS-ALLOWANCE-Q3 verfolgt

Die Annahme des aktuellen Fahrplans verschiebt die Kurve: **-3.29%** CO₂ bei diesem Fahrplan, und eine modellierte **8.7%**-Reduktion, wenn die Fahrplanoptimierung über den Gesamtplan läuft.""",
    "sustainability-compliance-q3": """Beide befinden sich im selben unveränderlichen Hauptbuch, beantworten aber unterschiedliche Fragen.

- **Scope 1 - direkt.** Verbrennung und Prozessemissionen am Standort: **1,368 t CO₂e** für 960 t Stahl heute, effektiv 1,425 kg pro Tonne. Verändert sich, wenn sich der Prozess ändert - unabhängig vom Netz.
- **Scope 2 - indirekt, bezogener Strom.** Berechnet pro Viertelstunde: Verbrauch im Intervall multipliziert mit der Netz-CO₂-Intensität desselben Intervalls - ca. **244 gCO₂/kWh** im Mittel, mit Schwankungen von rund 40-480 über den Tag. Verändert sich, wenn Last zeitlich verschoben wird - selbst bei gleichem Durchsatz.

Deshalb reduziert die Fahrplan-Empfehlung CO₂ um **3.29%**, ohne weniger Stahl zu produzieren: Sie berührt nur Scope 2. Das Hauptbuch enthält **96 unveränderliche Intervallzeilen**, und das ETS-Kostenrisiko wird aus deren Summe bei €86/t abgeleitet.

Im Juli 2026 betrug die Aufteilung Scope 1 **355,336 t** und Scope 2 **147,868 t**.""",
    "sustainability-compliance-q4": """Den Fahrplan freigeben - das ist der einzige Hebel, der heute wirkt.

- **REC-DEMO-LUX-240725** - CO₂ **-3.29%** sofort, bei unverändertem Durchsatz (960 t), 0 Hard-Constraint-Verletzungen, noch PENDING_APPROVAL
- Die Fahrplanoptimierung über den Gesamtplan ist mit **8.7%** modelliert
- Nächstschnellster Hebel: ES-RHF-01 Brennerzone 02 ist **4% fett im Luft/Gas-Verhältnis**, rund 180 kWh/h vermeidbarer Verlust
- Am langsamsten, aber am größten: die eigentliche Scope-1-Prozessroute, die keine Fahrplananpassung erreicht

Bei **€86/t** und einem Puffer von 6.2% ist der Fahrplan das, was die Richtwert-Überschreitung davon abhält, früher als Monat 5 einzutreten. Im Juli 2026 trugen die 100 angenommenen Empfehlungen **11,431 t** erwartetes CO₂-Einsparpotenzial.""",
    # -- knowledge-hub -----------------------------------------------------
    "knowledge-hub-q1": """**PROC-DEMO-0002 - Kühlkreis-Inspektion und Ultraschall-Eskalation.** Status APPROVED, Version 3, erfasst in Session SESS-DEMO-015 und zitiert aus transcript:SESS-DEMO-015#seg-2. Es ist die einzige freigegebene Arbeitsanweisung in der Bibliothek - und diejenige, die für den offenen Herdalert gilt.

Nächster Kandidat, noch nicht verwendbar: **PROC-DEMO-0001 - Herdsektor-Übertemperatur-Verifikation**, Version 2, IN_REVIEW, zitiert aus transcript:SESS-DEMO-014#seg-4 und #seg-7. Sie besagt, benachbarte Schalen-Thermoelemente vor dem Handeln zu vergleichen, Kühlein- und -auslauf-Delta T mit jüngster Durchflusshistorie statt nur aktuellem Durchfluss abzulesen und niemals Alarme zu umgehen oder Steuerungen auf Basis von Interviewrichtlinien zu ändern.

Begründete Antworten werden ausschließlich aus freigegebenen Arbeitsanweisungen abgeleitet, daher kann PROC-DEMO-0001 eingesehen, aber erst nach Expertenfreigabe als Antwort zitiert werden.""",
    "knowledge-hub-q2": """**Der Lückenbereich ist Energie und Versorgung - 58% Abdeckung**, der niedrigste Wert der fünf Domänen.

- Hochofen **82%**
- Qualitätslabor **77%**
- Warmwalzwerk **71%**
- Wärmofen **64%**
- Energie und Versorgung **58%**

Drei erfasste Arbeitsanweisungen haben die 5-Tage-Prüfungs-SLA überschritten (ALERT-KNOWLEDGE-REVIEW-QUEUE), und nur eine der drei Arbeitsanweisungen in der Bibliothek ist freigegeben - die nutzbare Abdeckung liegt daher in jeder Domäne unter der erfassten.

Die Lücke trifft am stärksten dort, wo Fachkräfte ausscheiden: Das Herdfachwissen hinter PROC-DEMO-0001 ist erfasst, aber noch nicht freigegeben, während die Energiedomäne - diejenige mit der €2,688.70/Tag-Fahrplanentscheidung - von Haus aus am wenigsten erfasst hat.""",
    "knowledge-hub-q3": """Zwei der drei Arbeitsanweisungen sind noch nicht verwendbar.

- **PROC-DEMO-0001 - Herdsektor-Übertemperatur-Verifikation.** IN_REVIEW, Version 2, Session SESS-DEMO-014, zwei zitierte Transkript-Segmente (#seg-4, #seg-7). Direkt relevant für den offenen LUX-BF-01-Alert.
- **PROC-DEMO-0003 - Wärmofen-Zonen-Durchwärm-Wiederherstellung.** DRAFT, Version 1, Session SESS-DEMO-016, ein zitiertes Segment (#seg-1).
- Bereits freigegeben: **PROC-DEMO-0002**, Version 3, Kühlkreis-Inspektion und Ultraschall-Eskalation.

**ALERT-KNOWLEDGE-REVIEW-QUEUE** kennzeichnet drei erfasste Arbeitsanweisungen, die die 5-Tage-Prüfungs-SLA überschritten haben. Die Freigabe ist bewusst ein menschlicher Schritt: Die Freigabe von PROC-DEMO-0002 ist als Audit **AUD-0004** mit Akteur ke-demo um 10:15 erfasst, sodass die Kette vom Betreiber-Transkript zur veröffentlichten Arbeitsanweisung nachvollziehbar bleibt.""",
    "knowledge-hub-q4": """Interviewleitfaden, basierend auf PROC-DEMO-0001 und der aktuellen LUX-BF-01-Signatur. Proband **OP-DEMO-014**, erfahrener Hochofenbediener; die Erfassung ist einwilligungspflichtig und das Transkript wird im Rahmen dieses Einwilligungsbereichs aufbewahrt.

- Wenn ein Herdsektor sich erwärmt, der Kühldurchfluss aber normal liest - was prüfen Sie zuerst und in welcher Reihenfolge?
- Welche benachbarten Schalen-Thermoelemente vergleichen Sie, und wie groß muss ein Delta sein, damit Sie handeln? SECTOR-07 steigt derzeit mit 3.4 °C/h gegenüber 0.4 °C/h bei seinen Nachbarn.
- Wie unterscheiden Sie Zustellungsdegradierung von einem driftenden Sensor? PROC-DEMO-0001 nennt Persistenz über Abstiche und langsameres Abkühlen nach dem Abstich - was verwenden Sie noch?
- Was verraten Kühlein- und -auslauf-Delta T zusammen mit der jüngsten Durchflusshistorie, das der aktuelle Durchfluss allein nicht zeigt? Heute liest er 9.4 °C bei 198 m³/h.
- Bei einer geschätzten Dicke von 363 mm gegenüber einem Minimum von 300 mm - was würde Sie veranlassen, das Neuzustellungsfenster vorzuziehen?
- Was ist bei diesem Ofen in der Vergangenheit schiefgelaufen, das ein neuer Bediener nicht erwarten würde?

Sicherheitsgrenze zur Dokumentation: Alarme niemals umgehen und Ofen- oder Kühlsteuerungen niemals auf Basis von Interviewrichtlinien ändern.""",
    # -- executive-overview ------------------------------------------------
    "executive-overview-q1": """Drei der vier Zielkennzahlen sind erreicht, eine ist verfehlt. Die Zahlen stammen vom Juli-2026-Abschluss der Gold-Tabellen.

- **Energieintensität (KPI-ENE-01)** - **10.63 GJ/t** gegen ein Ziel von 16.77, ausgehend von einer Baseline von 19.5. **Erfüllt**, mit Energiekosten von rund €46.5M gegenüber einer €54.1M-Baseline.
- **CO₂-Intensität (KPI-CO₂-01)** - **1.019 tCO₂e/t** gegen ein Ziel von 1.638, ausgehend von einer Baseline von 2.10. **Erfüllt**.
- **Zustellungs-Vorwarnzeit (KPI-FUR-01)** - jede Alert-Episode hat genau bei **21.0 Tagen** ausgelöst, dem angegebenen Minimum, mit unplanned_outage_flag false in jeder Zeile. **Erfüllt**.
- **Hochgüten-Erstdurchlaufausbeute (KPI-QUA-01)** - **0.9494** gegen ein Ziel von 0.972, ausgehend von einer Baseline von 0.90. **Nicht erfüllt**, rund 2.3 Punkte darunter.
- Unterstützend: Fahrplan-Annahmequote **0.862** (100 von 116 angenommen) gegen ein Minimum von 0.70. **Erfüllt**.

Die Fortschrittsbalken auf diesem Bildschirm zeigen 92, 88, 96 und 100 von 100 für Energie, CO₂, Ausbeute und Vorwarnzeit. Qualität ist die ehrliche Lücke - das ist der nächste Fokus der Wissenserfassung.""",
    "executive-overview-q2": """**Saarbrucken (DE)** in der Leistung, **Moselle (LU)** im Risiko.

- Moselle (LU) - Energie -14.2%, CO₂ -22.4%, Ausbeute +8.1%, **3 offene Alerts** einschließlich des einzigen kritischen
- Saarbrucken (DE) - Energie **-11.8%**, CO₂ **-18.6%**, Ausbeute **+6.4%**, 2 offene Alerts: letzter auf allen drei Achsen
- Liege (BE) - Energie -13.1%, CO₂ -20.2%, Ausbeute +7.2%, 1 offener Alert
- Asturias (ES) - Energie -12.5%, CO₂ -19.4%, Ausbeute +7.9%, 2 offene Alerts

Saarbrucken ist der einzige Standort, der auf allen drei Achsen unter dem Programmziel liegt; die offenen Punkte sind kostengetrieben: Strangguss-Kokillenspiegel-Schwingungen über dem 4.5-mm-Band und ein Schrottchargen-Mix 3.1% über der kostenoptimalen Zusammensetzung.

Moselle führt auf jeder Achse, trägt aber die LUX-BF-01-Herdprognose - Risikowert 0.90, 19.65 Tage - die diese Woche die €8M-Frage ist.""",
    "executive-overview-q3": """Vier zugesagte Ergebnisse, gemessen an einem synthetischen Pilotdatensatz, als Ziele formuliert wo sie Ziele sind.

- **Ziele** - Energie pro Tonne -14%, CO₂ pro Tonne -22%, Hochgütenausbeute +8%, mindestens 21 Tage Zustellungsvorwarnung.
- **Gemessen in den Pilotdaten** - Energieintensität 10.63 GJ/t und CO₂-Intensität 1.019 tCO₂e/t im Juli 2026; jeder Zustellungsalert bei genau 21.0 Tagen ausgelöst ohne ungeplanten Ausfall; Hochgüten-Erstdurchlaufausbeute 0.9494, noch unter dem 0.972-Ziel.
- **Gemessen bei einem einzelnen Fahrplan heute** - €2,688.70 gespart (7.25%), Spitzenlast -7.89%, CO₂ -3.29%, null Constraint-Verletzungen.
- **Modelliert, nicht realisiert** - ein verhinderter Ausfall, im Anwendungsszenario mit €8M pro ungeplantem Herdausfall bewertet.

Die Governance hat dasselbe Gewicht wie die Zahlen: fünf Entscheidungsprotokoll-Einträge über fünf Domänen, drei davon modellverknüpft, 100% Unveränderlichkeit, und jede Empfehlung erfordert eine menschliche Entscheidung, bevor sie wirkt.""",
    "executive-overview-q4": """Die Trennung ist klar - die Kacheln belegen es in ihren Tooltips.

**Ziele, keine Messungen:** Energie pro Tonne -14%, CO₂ pro Tonne -22%, Hochgütenausbeute +8%, mindestens 21 Tage Vorwarnzeit. Das sind die flottenweiten Anwendungsszenario-Zusagen.

**In diesem Demo gemessen:**
- Fahrplan - **€2,688.70 (7.25%)** gespart, Spitzenlast 56.0 auf 51.58 MW, CO₂ **-3.29%**, 0 Hard-Verletzungen
- Herd - Risikowert 0.8995 mit **P50 19.65 Tagen** Vorwarnung bei LUX-BF-01, unter dem 21-Tage-Ziel in dieser einzelnen Live-Episode
- Qualitäts-What-if - vorhergesagte Erstdurchlaufausbeute von ca. 88% auf ca. 95%, Modell quality-yield-gbm/2.1.0-demo
- Juli-2026-Gold-Abschluss - 10.63 GJ/t, 1.019 tCO₂e/t, 21.0 Tage Vorwarnung bei jeder Episode, 0.9494 Hochgüten-Erstdurchlaufausbeute

**Modelliert:** der €8M-Wert für vermiedenen Ausfall und die Anzahl eines verhinderten Ausfalls.

Die eine Zahl, die nie als erreicht dargestellt werden darf, ist das CO₂-Ziel: Das Flottenziel ist -22%, während dieses Einzel-Standort-Demo -3.29% bei einem Fahrplan misst.""",
    # -- platform-ops ------------------------------------------------------
    "platform-ops-q1": """**Running** - Kapazität **cap-novasteel-demo-sc**, SKU **F2**, Region Sweden Central, Umgebung demo.

- Heute Morgen wiederaufgenommen: Paused zu Resuming um 07:27, Resuming zu ReadinessCheck um 07:28, ReadinessCheck zu Running um 07:30 - alles durch demo-platform-ops mit Begründung "rehearsal"
- Lifecycle-Richtlinie: nächtliche Pausenprüfung um **01:00 Europe/Luxembourg**
- Die SKU ist zwischen F2, F4 und F8 umschaltbar; die Zustandsänderung ist als Audit **AUD-0005** erfasst
- Der Workspace NovaSteelV3-Demo enthält das Lakehouse lh_novasteelv3_core, die KQL-Datenbank kql-ns-operations und die Ontologie onto_novasteelv3

Es handelt sich um eine Nicht-Produktionskapazität, und der Lifecycle ist bewusst auf Starten, Pausieren und SKU-Wechsel beschränkt - jeder Vorgang wird auditiert.""",
    "platform-ops-q2": """**Kein Fehler.** Vier der fünf letzten Läufe sind erfolgreich abgeschlossen, einer ist noch aktiv.

- RUN-4821 bronze-to-silver - SUCCEEDED, 17:45, **214 s**
- RUN-4820 silver-to-gold - SUCCEEDED, 17:30, **176 s**
- RUN-4819 semantic-refresh - **RUNNING**, gestartet 18:40, 62 s bisher
- RUN-4818 contract-assertions - SUCCEEDED, 17:10, 41 s
- RUN-4817 quarantine-negative-tests - SUCCEEDED, 16:55, 33 s

Beide Guard-Jobs sind bestanden: Contract-Assertions auf den Event-Envelopes und die Negativtests, die belegen, dass fehlerhafte Payloads in der Quarantäne statt in Silver landen. End-to-End-Aktualität beträgt **12 s**. Der einzige offene Punkt ist das Semantic-Refresh.""",
    "platform-ops-q3": """Stabil und gering - es handelt sich um ein F2 mit einer Demo-Arbeitslast.

- Kosten pro Stunde **€2.80**, schwankend um ca. €0.40 auf beiden Seiten im Fenster 06:00-18:00
- Die Auslastung liegt im Schnitt bei ca. **38%**, auf einem gleichmäßigen Profil zwischen rund 26% und 50%
- Der bisherige Verbrauch ist die Summe der 13 stündlichen Punkte im Trend
- Telemetrie-Aktualität **12 s**

Das Profil ist wichtiger als der Gesamtwert: Die Auslastungsspitzen liegen beim Silver-to-Gold- und Semantic-Refresh-Lauf, weshalb die nächtliche Pausenprüfung um 01:00 keinen Durchsatzverlust verursacht. Bei einem F2 ist die Kapazität selbst der Sockelbetrag der Rechnung, sodass das Pausieren zwischen Demos der einzige echte Hebel ist.""",
    "platform-ops-q4": """**Noch nicht - RUN-4819 (semantic-refresh) läuft noch**, 62 s, gestartet um 18:40.

- Die anderen vier Läufe sind abgeschlossen: bronze-to-silver, silver-to-gold, contract-assertions und quarantine-negative-tests - alle SUCCEEDED zwischen 16:55 und 17:45
- Pausieren während eines Semantic-Model-Refreshs hinterlässt das Modell unaktualisiert, sodass Dashboards beim Fortsetzen den vorherigen Gold-Snapshot liefern würden
- Kapazität **cap-novasteel-demo-sc** ist F2, Running seit 07:30, Umgebung demo
- Die Lifecycle-Richtlinie führt ihre Pausenprüfung bereits um **01:00 Europe/Luxembourg** durch; zu diesem Zeitpunkt ist dieser Lauf längst abgeschlossen

Auf SUCCEEDED-Meldung von RUN-4819 warten, dann pausieren. Der Übergang wird wie die anderen mit Akteur und Begründung erfasst.""",
    # -- device-operations -------------------------------------------------
    "device-operations-q1": """**Keine.** Alle **17 Geräte** senden und es sind **0 aktive Vorfälle** injiziert.

- Flotte: 6 in Luxemburg (LUX-BF-01, LUX-BOF-01, LUX-CC-01, LUX-RHF-01, LUX-HSM-01, LUX-UTIL-01), 4 in Deutschland, 4 in Belgien, 3 in Spanien
- **91 Sensorsignale** online in der gesamten Flotte
- Betriebszeit zwischen **99.10% und 99.95%** pro Gerät
- Simulator: Szenario **demo-full**, Seed 240726, Tick 720, ca. 6 abgelaufene Stunden bei 5 s pro Tick

Das einzige Gerät mit einem offenen Alert ist **LUX-BF-01** - die Herdprognose - und das ist ein Prozesszustand, kein Gerätefehler: Seine Thermoelemente, Wärmestrom- und Kühlsignale werden planmäßig veröffentlicht. Der Gerätezustand auf diesem Bildschirm wird anhand von Signal-Aktualität und Alarmanzahl gemessen, sodass ein gesundes Gateway hinter einem kritischen Prozessalert liegen kann.""",
    "device-operations-q2": """Er misst den Gateway-Zustand, nicht den Prozesszustand. Drei Eingaben:

- **Betriebszeit** - der Anteil des Fensters, in dem das Gerät überhaupt gesendet hat. Die Flotte liegt zwischen **99.10% und 99.95%**.
- **Signal-Aktualität** - jedes Signal hat eine erwartete Sendeperiode und wird veraltet, sobald es diese überschreitet. Die Perioden reichen von **1 s** (arc_current bei DE-EAF-01) und 5 s (hearth_shell_temperature, local_heat_flux) bis zu **900 s** (hearth_refractory_estimate, spot_price, grid_carbon_intensity). Ein Signal ist ereignisgesteuert ohne Periode: hot_metal_temperature, nur bei einem Abstich gesendet.
- **Alarmanzahl** - aktive Gerätealarme im Fenster, gewichtet nach Schweregrad.

Ein Gerät ist gesund, wenn alle drei Kriterien erfüllt sind, degradiert wenn Signal-Aktualität oder Alarmanzahl nachlassen, und fehlerhaft wenn es aufhört zu senden. Bei Tick 720 ohne injizierte Vorfälle sind alle **17 Geräte und 91 Signale** gesund - weshalb der LUX-BF-01-Prozessalert neben einem sauberen Gerätewert steht.""",
    "device-operations-q3": """**Derzeit sind keine veraltet** - alle **91 Signale** liegen bei Tick 720 innerhalb ihrer erwarteten Periode.

Die Veralterung der Signale wird je Signal beurteilt, und die Perioden variieren stark:
- **1-5 s** - arc_current (DE-EAF-01), hearth_shell_temperature und local_heat_flux (LUX-BF-01), zinc_bath_temperature (BE-GAL-01)
- **10 s** - bath_temperature bei LUX-BOF-01 und DE-EAF-01
- **60 s** - production_rate
- **900 s** - hearth_refractory_estimate, spot_price, grid_carbon_intensity
- **Ereignisgesteuert** - hot_metal_temperature, nur bei einem Abstich gesendet

Das ist relevant, weil ein Modell nur so aktuell ist wie sein langsamster Eingang. Der Zustellungswert hängt von hearth_refractory_estimate und local_heat_flux ab: Wenn die 900-s-Feuerfest-Schätzung veraltet, hört der **Restnutzungsdauer-P50 von 19.65 Tagen** auf sich zu bewegen, während der Ofen weiter mit ca. 3.0 mm/Tag ausdünnt. Der Fahrplan hat dieselbe Exponierung durch spot_price und grid_carbon_intensity, beide ebenfalls auf 900 s.""",
    "device-operations-q4": """Zwei Möglichkeiten, je nachdem wie lange der Vorfall dauern soll.

**Einzelner Vorfall - degrading-furnace.** Schweregrad hoch, Standarddauer **30 Minuten**, Ziel **LUX-BF-01**, treibt local_heat_flux, hearth_refractory_estimate und hearth_shell_temperature. Im Vorfalls-Panel auf diesem Bildschirm auswählen, Gerät und Dauer bestätigen und injizieren.

**Gesamtszenario - lining-degradation-21d.** Den Simulator auf diesem Szenario statt auf demo-full neu starten, um den vollständigen Degradierungsverlauf statt einer 30-Minuten-Exkursion abzuspielen.

- Aktueller Zustand: Szenario **demo-full**, Seed **240726**, Tick 720, ca. 6 abgelaufene Stunden, 5-s-Ticks, **0 aktive Vorfälle**
- Weitere verfügbare Szenarien: healthy-baseline, energy-price-spike, quality-drift, edge-outage-recovery
- Weitere Vorfälle: cooling-water-loss (kritisch, 15 Min.), sensor-drift (60 Min.), sensor-dropout (10 Min.), energy-price-spike (45 Min., LUX-UTIL-01), quality-drift (45 Min., LUX-CC-01 und LUX-HSM-01), edge-outage-recovery (20 Min.)

Den Effekt auf den Herdzustand innerhalb weniger Ticks erwarten: Risikowert über 0.80 und Restnutzungsdauer-P50 zwischen **19 und 23 Tagen**, was dem Szenario-Bereich entspricht.""",
    # -- dashboards --------------------------------------------------------
    "dashboards-q1": """**Morgendliche Schichtübergabe** - Werksleiter, ca. **6 Minuten**, markiert als täglich und Triage.

Es führt durch Kommandozentrale, dann Betrieb, dann die offenen Alerts - die Reihenfolge, die eine Schichtübergabe tatsächlich benötigt: Was ist kritisch, was hat die Linie getan, was ist noch offen.

Was es derzeit zeigen würde: **16 offene Alerts** (1 kritisch, 8 Warnung, 7 Info, 2 bestätigt), Durchsatz **128.4 t/h** gegen 130, OEE **84.1%**, und ein Arbeitsauftrag - WO-DEMO-LUX-1042 - gegen die Herdprognose angelegt.

Wenn es bei der Übergabe speziell um den Ofen geht, stattdessen **Herdrisiko-Untersuchung** (ca. 8 Minuten) verwenden; es ist das tiefergehende der beiden.""",
    "dashboards-q2": """**Compliance-Nachweispaket** - Nachhaltigkeitsbeauftragter und Auditor, ca. **7 Minuten**, markiert als compliance, audit und eu-ai-act.

Es stellt die Nachweiskette zusammen, nicht die Kennzahlen:
- **5 Entscheidungsprotokolle**, AUD-0001 bis AUD-0005, abdeckend alle **5 Domänen**: Herd, Energie, Qualität, Wissensmanagement und Kapazität
- **3 davon modellverknüpft** - lining-rul-piml/1.3.0-demo, energy-dispatch-milp/1.2.0-demo und quality-yield-gbm/2.1.0-demo
- **100% Unveränderlichkeit**, mit Korrelations-ID run-demo-full-240725, die Herd-, Energie- und Qualitätsentscheidungen an einen einzelnen Lauf knüpft
- Das dahinterliegende Emissionshauptbuch: 96 append-only-Intervallzeilen, Scope 1 und Scope 2 getrennt, ETS bewertet bei €86/t
- Menschliche Entscheidungspunkte: jede Empfehlung trägt Akteur und Zeitstempel - das ist worauf das EU-AI-Act-Nachvollziehbarkeitsargument basiert

Das ist das Paket: Was wurde entschieden, durch welche Modellversion, auf welchen Daten, und von wem freigegeben.""",
    "dashboards-q3": """Sechs Sammlungen, jeweils ein fester Weg durch bereits vorhandene Bildschirme.

- **Morgendliche Schichtübergabe** - Werksleiter, ca. 6 Min., täglich und Triage. Was ist kritisch, was hat die Linie getan, was ist noch offen.
- **Herdrisiko-Untersuchung** - Instandhaltungs- und Zuverlässigkeitsingenieur, ca. 8 Min., Zuverlässigkeit und Ursachenanalyse. Ist das Zustellungsrisiko real, was treibt es, wann muss gehandelt werden.
- **Energie- und Kostenbewertung** - Energiemanager, ca. 7 Min., Energie und Kosten. Was kostet der Fahrplan, was spart die Alternative, was schränkt ihn ein.
- **Qualitätsabweichungs-Überprüfung** - Qualitätsingenieur, ca. 6 Min., Qualität und Ursachenanalyse. Welche Charge, welcher Schritt, welche Anpassung.
- **Compliance-Nachweispaket** - Nachhaltigkeitsbeauftragter und Auditor, ca. 7 Min., compliance, audit und eu-ai-act. Was wurde entschieden, durch welches Modell, von wem freigegeben.
- **Plattformzustand und -kosten** - Platform Ops, ca. 5 Min., Plattform und Kosten. Ist die Pipeline gesund, was kostet sie.

Jede Sammlung enthält drei oder vier geordnete Bildschirme und fügt keine eigenen Daten hinzu - die Zahlen verbleiben bei den Bildschirmen, auf die sie verweist.""",
    "dashboards-q4": """**Herdrisiko-Untersuchung** - Instandhaltungs- und Zuverlässigkeitsingenieur, ca. **8 Minuten**, markiert als Zuverlässigkeit und Ursachenanalyse. Gezeigt werden Zustellungsprognose, dann Thermalexplorer, dann Wartungsplaner - die Reihenfolge, in der die Nachweise aufgebaut werden.

Was es derzeit zeigen würde:
- Zustellungsprognose - LUX-BF-01 / HEARTH-SECTOR-07 bei Risikowert **0.8995**, Restnutzungsdauer **P50 19.65 Tage** (P10 18.69 / P90 20.61)
- Thermalexplorer - SECTOR-07 steigt mit **3.4 °C/h** gegenüber 0.4 °C/h bei Nachbarn, überschreitet den 700 °C-Anomaliegrenzwert
- Wartungsplaner - **WO-DEMO-LUX-1042** offen für den Sektor, Neuzustellungsfenster an Tagen 18-24

Für die umfassendere Übergabe **Morgendliche Schichtübergabe** (ca. 6 Min.) verwenden; für den Audit-Rahmen statt der technischen Seite trägt **Compliance-Nachweispaket** die Entscheidungskette hinter demselben Einsatz.""",
}
