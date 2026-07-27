import type { HelpCatalog } from '../components/help/helpTypes'

export const HELP_DE: HelpCatalog = {
  // ---------------------------------------------------------------- generic
  'generic.kpi': {
    title: 'Kennzahl',
    what: 'Eine Kachel zeigt eine Messgröße, ihren Trendpfeil und den Vergleich mit dem Zielwert.',
    steel:
      'Ein Stahlwerk wird mit wenigen Kennzahlen geführt. Nebeneinander angezeigt zeigen sie der Schichtleitung in Sekunden den Zustand des Werks, ohne Berichte lesen zu müssen.',
    useIt: 'Hebt sich eine Kachel beim \u00dcberfahren mit der Maus hervor, k\u00f6nnen Sie sie anklicken, um die Details hinter der Zahl zu \u00f6ffnen.',
  },
  'generic.chart': {
    title: 'Diagramm',
    what: 'Ein Bild davon, wie sich eine Messgröße über die Zeit verändert hat oder wie sie sich auf Werksteile verteilt.',
    steel:
      'Einzelne Zahlen verbergen die Geschichte. Ein Ofen mit sicherer Durchschnittstemperatur kann trotzdem gefährliche Spitzen haben, und nur ein Diagramm zeigt sie.',
    useIt: 'Fahren Sie über einen Punkt, um den genauen Wert zu sehen. Diagramme in einem Panel können mit der Maximieren-Schaltfläche in der Registerleiste vergrößert werden.',
  },
  'generic.table': {
    title: 'Datentabelle',
    what: 'Die einzelnen Datensätze hinter den Zusammenfassungen, einer pro Zeile.',
    steel: 'Wenn eine Zahl falsch wirkt, finden Sie in der Tabelle die konkrete Charge, den Sensor oder den Arbeitsauftrag, der sie verursacht hat.',
    useIt: 'Klicken Sie auf eine Spaltenüberschrift zum Sortieren, nutzen Sie die Kopfzeilensteuerungen zum Filtern und das Suchfeld zum Finden von Text in der ganzen Tabelle.',
  },
  'generic.tableRow': {
    title: 'Ein Datensatz',
    what: 'Ein einzelnes Element: eine Charge, ein Sensorwert, ein Arbeitsauftrag oder eine Warnung.',
    steel: 'Alles, was im Werk geschieht, wird am Ende als solcher Datensatz festgehalten. Dadurch wird eine Prüfung möglich.',
    useIt: 'Wenn eine Zeile anklickbar ist, öffnet sie die vollständigen Details dieses Elements.',
  },
  'generic.tableHeader': {
    title: 'Spaltenüberschrift',
    what: 'Der Name einer Spalte und die Steuerung, die die Tabelle danach sortiert und filtert.',
    steel: 'Durch Sortieren nach Risiko oder Datum macht ein Ingenieur aus einer langen Liste eine kurze Liste von Dingen, die heute zu erledigen sind.',
    useIt: 'Klicken Sie einmal für aufsteigend, nochmals für absteigend. Filtersteuerungen beschränken die Tabelle auf passende Zeilen.',
  },
  'generic.panel': {
    title: 'Arbeitsbereich-Panel',
    what: 'Ein verschiebbarer Abschnitt des Bildschirms. Panels können an ihrem Reiter an einen Rand gezogen, vergrößert oder gestapelt werden.',
    steel: 'Leitstandbediener beobachten unterschiedliche Dinge. Deshalb passt sich die Anordnung der Person an und nicht umgekehrt.',
    useIt: 'Ziehen Sie den Reiter, um die Anordnung zu ändern. Layout zurücksetzen in der Kopfzeile stellt alles wieder her.',
  },
  'generic.dockTab': {
    title: 'Panel-Reiter',
    what: 'Der Griff eines Panels. Er benennt das Panel und lässt es verschieben.',
    steel: 'Panels, die immer sichtbar bleiben müssen, haben keine Schließen-Schaltfläche. So kann eine kritische Ansicht nicht versehentlich verloren gehen.',
    useIt: 'Ziehen Sie ihn, um das Panel zu bewegen, oder klicken Sie auf Maximieren, damit es den Arbeitsbereich füllt.',
  },
  'generic.button': {
    title: 'Aktion',
    what: 'Eine Steuerung, die die Anzeige ändert oder die Plattform auffordert, etwas zu tun.',
    steel:
      'Alles, was das Anlagenverhalten ändern könnte, ist hier immer nur ein Vorschlag. Ein Mensch genehmigt ihn, bevor er die Ausrüstung erreicht.',
    useIt: 'Fahren Sie darüber, um einen Tooltip zu sehen, der die Aktion beschreibt.',
  },

  // ------------------------------------------------------------ chart types
  'chart.line': {
    title: 'Liniendiagramm',
    what: 'Die Zeit läuft von links nach rechts, die Messgröße von unten nach oben. Die Linie verbindet aufeinanderfolgende Messwerte.',
    steel: 'Stahlprozesse driften langsam, daher ist die Steigung wichtiger als ein einzelner Messwert. Eine steigende Linie ist eine frühe Warnung.',
    useIt: 'Achten Sie auf plötzliche Sprünge und auf eine Steigung, die weiter in dieselbe Richtung läuft.',
  },
  'chart.area': {
    title: 'Flächendiagramm',
    what: 'Ein Liniendiagramm mit ausgefüllter Fläche unter der Linie, wodurch Summen leichter vergleichbar sind.',
    steel: 'Nützlich für Mengen, die sich aufsummieren, etwa verbrauchte Energie oder freigesetzte Emissionen während einer Schicht.',
    useIt: 'Vergleichen Sie die Größe der gefüllten Flächen statt der Höhe der Linie.',
  },
  'chart.bar': {
    title: 'Balkendiagramm',
    what: 'Ein Balken pro Kategorie. Höher bedeutet mehr.',
    steel: 'Gut, um Hochöfen, Stahlgüten oder Schichten auf einen Blick miteinander zu vergleichen.',
    useIt: 'Suchen Sie den Ausreißerbalken. Dort liegt meist das Problem oder die Chance.',
  },
  'chart.heatmap': {
    title: 'Wärmekarte',
    what: 'Ein Raster, in dem Farbe für einen Wert steht. Dunklere oder heißere Farben bedeuten höhere Messwerte.',
    steel:
      'Ein Hochofen ist mit Hunderten Sensoren ausgestattet. Eine Wärmekarte zeigt alle gleichzeitig, sodass ein heißer Punkt am Mantel sofort auffällt.',
    useIt: 'Suchen Sie nach einzelnen hellen Zellen. Eine heiße Zelle zwischen kühlen Zellen bedeutet meist ein lokales Verschleißproblem.',
  },
  'chart.gauge': {
    title: 'Rundanzeige',
    what: 'Eine Skala, die einen Wert gegenüber seinem sicheren Bereich zeigt.',
    steel: 'Sie ähnelt den analogen Instrumenten, die Bediener seit Jahrzehnten auf dem Anlagenboden nutzen. Auf einem Leitstandschirm braucht sie daher kaum Erklärung.',
    useIt: 'Das farbige Band zeigt, ob der aktuelle Wert komfortabel, grenzwertig oder außerhalb der Grenzen liegt.',
  },
  'chart.control': {
    title: 'Regelkarte',
    what: 'Ein Zeitdiagramm mit einer Mittellinie für das Ziel und zwei äußeren Linien für den akzeptablen Bereich.',
    steel:
      'Das ist das klassische Qualitätswerkzeug. Ein Prozess innerhalb der äußeren Linien ist vorhersagbar; ein Punkt außerhalb bedeutet, dass sich etwas geändert hat und untersucht werden muss.',
    useIt: 'Achten Sie auf Punkte außerhalb der Grenzen und auf lange Folgen von Punkten auf einer Seite der Mittellinie.',
  },
  'chart.pareto': {
    title: 'Pareto-Diagramm',
    what: 'Balken von groß nach klein sortiert, mit einer steigenden Linie für die laufende Summe.',
    steel:
      'Der meiste Ausschuss und Nacharbeit entstehen durch wenige Ursachen. Werden die ersten zwei oder drei Balken behoben, verschwindet meist der größte Teil des Verlusts.',
    useIt: 'Finden Sie, wo die Linie 80 Prozent kreuzt. Die Balken links davon sind Ihre Prioritätenliste.',
  },
  'chart.donut': {
    title: 'Ringdiagramm',
    what: 'Ein Ring, der in Segmente geteilt ist; jedes Segment ist ein Anteil am Ganzen.',
    steel: 'Verwendet für Aufteilungen, etwa woher Emissionen stammen, wenn ein Segment leichter zu beurteilen ist als ein Prozentsatz in einer Tabelle.',
    useIt: 'Vergleichen Sie die Segmentgrößen; fahren Sie darüber, um den genauen Anteil zu sehen.',
  },
  'chart.gantt': {
    title: 'Terminbalkendiagramm',
    what: 'Jeder Balken ist eine Aktivität, positioniert und bemessen nach Startzeit und Dauer.',
    steel:
      'Ofenzustellungen und Wartungsstillstände müssen zwischen Produktionskampagnen passen. Auf einer Zeitachse sehen Planer, wie sie Überschneidungen vermeiden.',
    useIt: 'Achten Sie auf Überschneidungen und auf Lücken, die ein Wartungsfenster aufnehmen könnten.',
  },
  'chart.priceLoad': {
    title: 'Preis- und Lastdiagramm',
    what: 'Zwei Dinge auf einer Zeitachse: der Strompreis und die Leistung, die das Werk beziehen will.',
    steel:
      'Strom ist einer der größten Kostenblöcke in der Stahlerzeugung, und sein Preis ändert sich stündlich. Energieintensive Arbeit in billige Stunden zu legen spart echtes Geld.',
    useIt: 'Prüfen Sie, ob die hohen Lastbalken unter den Tiefpunkten der Preislinie liegen.',
  },
  'chart.bullet': {
    title: 'Fortschrittsbalken',
    what: 'Ein Balken, der zeigt, wo der aktuelle Wert zwischen null und seinem Ziel liegt.',
    steel: 'Er gibt schnell ein Gefühl dafür, wie viel einer Verpflichtung, etwa eines jährlichen Emissionsbudgets, bereits verbraucht ist.',
    useIt: 'Die Markierung auf dem Balken ist das Ziel; der gefüllte Teil zeigt, wo Sie tatsächlich stehen.',
  },
  'chart.sparkline': {
    title: 'Mini-Trend',
    what: 'Ein sehr kleines Liniendiagramm ohne Achsen, das nur die jüngste Form der Messgröße zeigt.',
    steel: 'Es passt in eine Kennzahlkachel, sodass Sie die Richtung sehen, ohne den Übersichtsbildschirm zu verlassen.',
    useIt: 'Lesen Sie die Form, nicht die Werte. Klicken Sie auf die Kachel für das vollständige Diagramm.',
  },

  // ------------------------------------------------------- executive layer
  'kpi:energy': {
    title: 'Energieintensität',
    what: 'Strom und Brennstoff zur Herstellung einer Tonne Stahl, in Kilowattstunden pro Tonne.',
    steel:
      'Stahl herzustellen bedeutet, Eisenerz oder Schrott auf rund 1.600 Grad Celsius zu erhitzen. Energie ist daher zugleich größter Kostenblock und größte Emissionsquelle.',
    useIt: 'Vergleichen Sie mit der Ziellinie. Ein Rückgang hier wirkt direkt auf Kosten und Kohlenstoff.',
  },
  'kpi:co2': {
    title: 'Kohlendioxid-Emissionen',
    what: 'Tonnen CO2, die freigesetzt wurden, oder die Minderung gegenüber dem Referenzzeitraum.',
    steel:
      'Stahl verursacht rund sieben Prozent des weltweiten CO2. In Europa muss ein Werk für jede freigesetzte Tonne eine Emissionsberechtigung abgeben, daher hat diese Zahl einen Preis.',
    useIt: 'Lesen Sie sie zusammen mit der Energieintensität. Die meisten Minderungen kommen durch weniger oder saubereren Strom.',
  },
  'kpi:yield': {
    title: 'Ausbeute in Premiumqualität',
    what: 'Der Anteil der Produktion, der die hochwertige Spezifikation auf Anhieb erfüllt.',
    steel:
      'Stahl außerhalb der Spezifikation ist kein Abfall, er wird wieder eingeschmolzen. Das Einschmelzen verbraucht die Energie jedoch zweimal, daher ist Ausbeute auch eine verdeckte Energie- und Kostenkennzahl.',
    useIt: 'Ein Rückgang hier zeigt sich meist kurz danach auf den Qualitätsbildschirmen.',
  },
  'kpi:warning': {
    title: 'Warnvorlauf',
    what: 'Wie viele Tage Vorlauf die Modelle geben, bevor ein vorhergesagtes Problem eintreten würde.',
    steel:
      'Feuerfeste Steine zu bestellen und eine Reparaturmannschaft zu buchen dauert Wochen. Eine Warnung, die zu spät kommt, ist wertlos, daher zählt Vorlaufzeit genauso wie Genauigkeit.',
    useIt: 'Das Pilotziel liegt bei mindestens 21 Tagen. Weniger lässt keine Zeit, einen Stillstand zu planen.',
  },
  'kpi:failures': {
    title: 'Ungeplante Stillstände',
    what: 'Wie oft die Produktion ohne Planung angehalten hat.',
    steel:
      'Ein ungeplanter Hochofenstillstand ist extrem teuer: Das Gefäß muss warm gehalten werden, nachgelagerte Walzwerke bekommen kein Material, und der Neustart verbraucht Energie.',
    useIt: 'Das Ziel der gesamten Plattform ist, diese in geplante Stillstände umzuwandeln.',
  },

  // ---------------------------------------------------------- furnace health
  'kpi:risk': {
    title: 'Risiko der Zustellung',
    what: 'Ein Wert von 0 bis 1, der schätzt, wie wahrscheinlich die Ofenzustellung bald ihre Verschleißgrenze erreicht.',
    steel:
      'Ein Hochofen ist ein Stahlmantel mit hitzebeständigen Steinen, der feuerfesten Zustellung. Der Stein erodiert langsam; ist er durch, erreicht flüssiges Metall den Mantel. Dieser Wert ist die Frühwarnung des Werks.',
    useIt: 'Über 0,8 sollte die Instandhaltungsplanung ein Reparaturfenster buchen.',
  },
  'kpi:days': {
    title: 'Restnutzungsdauer',
    what: 'Geschätzte Betriebstage, bis die Zustellung bei aktueller Rate ihre Verschleißgrenze erreicht.',
    steel:
      'In der Branche ist dies als RUL bekannt. Eine Zustellung zu ersetzen ist eine mehrwöchige Kampagne, daher macht ein Termin Monate im Voraus aus einer Krise ein Projekt.',
    useIt: 'Nutzen Sie die Konfidenzzahl daneben. Kurze Lebensdauer bei geringer Konfidenz verlangt mehr Messung, nicht sofortiges Handeln.',
  },
  'kpi:confidence': {
    title: 'Modellkonfidenz',
    what: 'Wie sicher das Modell seiner eigenen Vorhersage ist, gemessen an den Daten, die es hatte.',
    steel: 'Sensoren fallen aus und Messwerte driften. Konfidenz neben der Antwort zu zeigen verhindert, dass ein Ingenieur einer Zahl aus dünnen Daten vertraut.',
    useIt: 'Geringe Konfidenz ist ein Signal, vor einer Entscheidung die Sensorzustände zu prüfen.',
  },
  'kpi:failDate': {
    title: 'Projiziertes Verschleißdatum',
    what: 'Das Kalenderdatum, auf das die Restlebensdauer-Schätzung zeigt.',
    steel: 'Aus "so vielen Tagen" ein Datum zu machen ermöglicht Planern, es mit Feiertagen, Verfügbarkeit von Fremdfirmen und Auftragsbüchern abzugleichen.',
    useIt: 'Vergleichen Sie es mit dem geplanten Wartungsfenster auf dem Planungsbildschirm.',
  },
  'kpi:anomalies': {
    title: 'Thermische Anomalien',
    what: 'Anzahl der Messwerte, die im gewählten Fenster vom erwarteten Muster abgewichen sind.',
    steel:
      'Ein lokaler heißer Punkt am Ofenmantel ist meist das erste physische Zeichen, dass der Stein dahinter dünner geworden ist.',
    useIt: 'Öffnen Sie die Wärmekarte, um zu sehen, wo sich die Anomalien am Mantel häufen.',
  },
  'kpi:cooling': {
    title: 'Leistung der Wasserkühlung',
    what: 'Wie wirksam das Kühlsystem Wärme aus dem Ofenmantel abführt.',
    steel:
      'Wassergekühlte Kühlelemente sitzen zwischen Stein und Stahlmantel. Wird die Kühlung schwächer, erwärmt sich der Mantel, daher ist dies eine Sicherheitsmessung und nicht nur eine Effizienzmessung.',
    useIt: 'Entscheidend ist die Kombination aus fallendem Wert und steigender Manteltemperatur.',
  },
  'kpi:slope': {
    title: 'Temperaturtrend',
    what: 'Wie schnell die Temperatur steigt oder fällt, in Grad pro Tag.',
    steel: 'Feuerfester Verschleiß ist langsam, daher ist eine anhaltend steigende Steigung von selbst einem Bruchteil Grad pro Tag bedeutsam.',
    useIt: 'Das Vorzeichen ist wichtiger als die Größe. Eine dauerhaft positive Steigung in einem Sektor verdient Aufmerksamkeit.',
  },
  'kpi:sensor': {
    title: 'Sensorabdeckung',
    what: 'Wie viele Temperatursensoren aktuell gesunde Daten melden.',
    steel: 'Vorhersagen sind nur so gut wie ihre Eingaben. Ein Sektor mit toten Sensoren ist praktisch unüberwacht.',
    useIt: 'Prüfen Sie den Geräteflotten-Bildschirm, wenn die Zahl sinkt.',
  },
  'furnace-health/thermal-explorer:kpi:peak': {
    title: 'Höchste Manteltemperatur',
    what: 'Die höchste am Ofenmantel gemessene Temperatur im ausgewählten Zeitraum.',
    steel:
      'Der Mantel sollte viel kühler bleiben als das flüssige Innere. Eine steigende Spitze bedeutet, dass Wärme einen Weg durch die feuerfeste Zustellung findet.',
    useIt: 'Nutzen Sie die Wärmekarte, um den Sektor zu finden, der die Spitze erzeugt hat.',
  },
  'kpi:open': {
    title: 'Offene Arbeitsaufträge',
    what: 'Instandhaltungsarbeiten, die angelegt, aber noch nicht abgeschlossen wurden.',
    steel: 'Stahlwerke laufen kontinuierlich, daher konkurriert Instandhaltung mit Produktion um Zeit. Der Rückstand ist der sichtbare Preis des Aufschiebens.',
    useIt: 'Sortieren Sie die Arbeitsauftragstabelle nach Priorität, um zu sehen, was ins nächste Fenster gezogen werden sollte.',
  },
  'kpi:urgent': {
    title: 'Dringende Arbeitsaufträge',
    what: 'Aufträge, die vor dem nächsten geplanten Stillstand Aufmerksamkeit brauchen.',
    steel: 'Diese Aufträge entscheiden, ob der nächste Stillstand geplant oder erzwungen ist.',
    useIt: 'Alles hier sollte gegen die Länge des Wartungsfensters abgeglichen werden.',
  },
  'kpi:completed': {
    title: 'Abgeschlossene Arbeitsaufträge',
    what: 'Aufträge, die im aktuellen Zeitraum geschlossen wurden.',
    steel: 'Die Abschlussrate im Verhältnis zum Rückstand zeigt, ob die Instandhaltungskapazität zum Bedarf des Werks passt.',
    useIt: 'Lesen Sie sie zusammen mit der offenen Zahl. Beide fallend ist gut, nur die abgeschlossenen fallend ist es nicht.',
  },
  'kpi:window': {
    title: 'Wartungsfenster',
    what: 'Die Länge des nächsten geplanten Produktionsstopps, der für Reparaturen verfügbar ist.',
    steel:
      'Einen Teil eines Ofens neu zuzustellen kann Tage dauern, und das Gefäß muss zuerst abkühlen. Die Arbeit in das Fenster zu bekommen ist das zentrale Problem der Planung.',
    useIt: 'Vergleichen Sie es mit der Gesamtdauer der dringenden Arbeitsaufträge.',
  },

  // ------------------------------------------------------------------ energy
  'kpi:price': {
    title: 'Strom-Spotpreis',
    what: 'Was eine Megawattstunde Strom am Großhandelsmarkt jetzt kostet.',
    steel:
      'Europäische Strompreise ändern sich jede Stunde und können sich innerhalb eines Tages mehrfach unterscheiden. Ein Werk, das flexible Last in günstige Stunden verschieben kann, senkt seine Rechnung ohne weniger zu produzieren.',
    useIt: 'Stellen Sie ihn der geplanten Last im Preis- und Lastdiagramm gegenüber.',
  },
  'kpi:savings': {
    title: 'Projizierte Einsparungen',
    what: 'Geld, das der vorgeschlagene Plan gegenüber derselben Arbeit zu einem Einheitstarif sparen würde.',
    steel: 'Die Einsparung kommt nur aus dem Zeitpunkt. Dieselben Tonnen werden produziert, nur in billigeren Stunden.',
    useIt: 'Dies ist ein Vorschlag. Real wird er erst, wenn ein Bediener den Plan genehmigt.',
  },
  'kpi:shiftable': {
    title: 'Verschiebbare Last',
    what: 'Wie viel des Strombedarfs des Werks in eine andere Stunde verschoben werden kann.',
    steel:
      'Ein Hochofen kann nicht pausiert werden, aber Wiedererwärmungsöfen, Walzwerke und Sauerstoffanlagen haben etwas Flexibilität. Nur dieser flexible Teil kann günstigem Strom folgen.',
    useIt: 'Sie setzt die Obergrenze dessen, was eine Optimierung erreichen kann.',
  },
  'kpi:baseline': {
    title: 'Basisszenario',
    what: 'Wie Kosten und Emissionen ohne jede Lastverschiebung wären.',
    steel: 'Jede behauptete Verbesserung braucht einen Vergleichspunkt. Dies ist diese Referenz.',
    useIt: 'Vergleichen Sie es mit dem optimierten Szenario, um den Nutzen zu lesen.',
  },
  'kpi:optimized': {
    title: 'Optimiertes Szenario',
    what: 'Kosten und Emissionen unter dem Plan, den der Optimierer vorschlägt.',
    steel: 'Der Optimierer respektiert reale Anlagenzwänge wie Mindestlaufzeiten, Rampenraten und Netzanschlussgrenzen, nicht nur den Preis.',
    useIt: 'Prüfen Sie die Kachel für Zwangsverletzungen, bevor Sie der Zahl vertrauen.',
  },
  'kpi:estimate': {
    title: 'Szenarioschätzung',
    what: 'Das Ergebnis der Was-wäre-wenn-Einstellungen, die auf diesem Bildschirm aktuell ausgewählt sind.',
    steel: 'Sie lässt einen Planer eine Idee testen, bevor das Werk darauf festgelegt wird.',
    useIt: 'Ändern Sie die Schieberegler und beobachten Sie, wie diese Zahl reagiert.',
  },
  'kpi:violations': {
    title: 'Zwangsverletzungen',
    what: 'Wie viele Anlagenregeln das aktuelle Szenario verletzen würde.',
    steel:
      'Zwänge bilden physische Realität ab: ein Ofen, der über einer Temperatur bleiben muss, oder ein Walzwerk, das nicht ständig starten und stoppen kann. Ein billiger Plan, der sie verletzt, ist kein Plan.',
    useIt: 'Dies muss null sein, bevor ein Szenario zur Genehmigung vorgeschlagen werden kann.',
  },
  'energy-optimization/load-shift-simulator:kpi:peak': {
    title: 'Spitzenbedarf',
    what: 'Der höchste Strombezug, den das Szenario erreichen würde.',
    steel:
      'Netzanschlüsse werden teilweise nach der höchsten erreichten Spitze abgerechnet, daher spart das Kappen der Spitze Geld, selbst wenn der Gesamtverbrauch gleich bleibt.',
    useIt: 'Beobachten Sie ihn beim Verschieben von Last. Das Verschieben von Arbeit kann versehentlich eine neue, höhere Spitze erzeugen.',
  },
  'kpi:server': {
    title: 'Status des Lösers',
    what: 'Ob die Optimierungsmaschine eine gültige Antwort gefunden hat und wie gut sie ist.',
    steel: 'Klar zu sagen, ob die Optimierung tats\u00e4chlich gel\u00f6st wurde, trennt ein Entscheidungsunterst\u00fctzungswerkzeug von einer Blackbox.',
    useIt: 'Ein unzulässiges Ergebnis bedeutet, dass nicht alle Zwänge gleichzeitig erfüllt werden können. Lockern Sie einen und führen Sie erneut aus.',
  },

  // ----------------------------------------------------------------- quality
  'kpi:firstpass': {
    title: 'Erstdurchlaufquote',
    what: 'Anteil der Chargen, die die Spezifikation ohne Nacharbeit erfüllt haben.',
    steel: 'Nacharbeit bedeutet Wiedereinschmelzen, was Energie zweimal verbraucht und den Auftrag verzögert. Die Erstdurchlaufquote verbindet Qualität und Kosten.',
    useIt: 'Ein Rückgang hier sollte auf eine Ursache im Pareto-Diagramm zurückführbar sein.',
  },
  'kpi:defect': {
    title: 'Fehlerquote',
    what: 'Anteil der Produktion mit einem erfassten Fehler.',
    steel: 'Typische Fehler sind Oberflächenrisse, Schlackeneinschlüsse oder eine Chemie, die außerhalb des Kundenbereichs gedriftet ist.',
    useIt: 'Nutzen Sie das Pareto-Diagramm, um die wenigen dominierenden Fehlertypen zu finden.',
  },
  'kpi:ncr': {
    title: 'Nichtkonformitätsberichte',
    what: 'Formale Datensätze, die angelegt werden, wenn eine Charge ihre Spezifikation nicht erfüllt.',
    steel: 'Kunden aus Automobilbau und Bauwesen prüfen diese Datensätze, daher sind sie Compliance-Pflicht und Qualitätssignal zugleich.',
    useIt: 'Öffnen Sie die Tabelle, um zu sehen, welche Produktgüten betroffen sind.',
  },
  'kpi:cpk': {
    title: 'Prozessfähigkeit (Cpk)',
    what: 'Eine einzelne Zahl, die sagt, wie komfortabel der Prozess innerhalb der Kundentoleranz liegt.',
    steel:
      'Über 1,33 gilt ein Prozess meist als fähig; unter 1,0 sind Fehler eher grundsätzlich zu erwarten als zufällig.',
    useIt: 'Lesen Sie sie mit der Regelkarte. Cpk fasst zusammen, was das Diagramm im Detail zeigt.',
  },
  'kpi:ooc': {
    title: 'Außer Kontrolle liegende Punkte',
    what: 'Messwerte, die außerhalb der statistischen Grenzen der Regelkarte lagen.',
    steel:
      'Außer Kontrolle bedeutet nicht außerhalb der Spezifikation. Es bedeutet, dass sich der Prozess geändert hat, und das ist ein Grund zur Untersuchung, bevor der Kunde es bemerkt.',
    useIt: 'Jedem Punkt sollte eine zugeordnete Ursache gegenüberstehen.',
  },
  'kpi:total': {
    title: 'Gesamtzahl der Messungen',
    what: 'Wie viele Messwerte den Statistiken auf diesem Bildschirm zugrunde liegen.',
    steel: 'Statistische Regeln brauchen genügend Daten, um aussagekräftig zu sein. Eine Fähigkeitszahl aus wenigen Proben ist nicht vertrauenswürdig.',
    useIt: 'Erweitern Sie den Zeitraum, wenn diese Zahl niedrig ist.',
  },
  'kpi:top': {
    title: 'Größter Beitrag',
    what: 'Die einzelne Kategorie, die für den größten Anteil des Problems verantwortlich ist.',
    steel: 'Verbesserungsprogramme gelingen, indem sie eine dominante Ursache nach der anderen beheben, nicht alles gleichzeitig.',
    useIt: 'Das ist der erste Balken im Pareto-Diagramm.',
  },

  // -------------------------------------------------------- sustainability
  'kpi:allowance': {
    title: 'Emissionsberechtigungen',
    what: 'Gehaltene Berechtigungen, von denen jede eine Tonne CO2 abdeckt.',
    steel:
      'Nach dem EU-Emissionshandelssystem (EU-EHS) muss ein Werk pro emittierter Tonne eine Berechtigung abgeben. Einige werden kostenlos zugeteilt, der Rest muss gekauft werden.',
    useIt: 'Vergleichen Sie sie mit der Obergrenze und den tatsächlichen Emissionen, um die Lücke zu sehen.',
  },
  'kpi:cap': {
    title: 'Zuteilungsobergrenze',
    what: 'Die kostenlose Zuteilung, die das Werk für das Compliance-Jahr erhält.',
    steel: 'Die Obergrenze sinkt planmäßig jedes Jahr. Das ist der Mechanismus, der den Sektor zur Dekarbonisierung zwingt.',
    useIt: 'Emissionen über der Obergrenze müssen durch gekaufte Berechtigungen gedeckt werden.',
  },
  'kpi:used': {
    title: 'Verbrauchte Berechtigungen',
    what: 'Wie viel der Zuteilung in diesem Jahr bisher verbraucht wurde.',
    steel: 'Der Verbrauch ist über das Jahr nicht gleichmäßig. Ein kalter Winter oder eine lange Kampagne verschiebt ihn.',
    useIt: 'Vergleichen Sie den verbrauchten Prozentsatz mit dem verstrichenen Anteil des Jahres.',
  },
  'kpi:overage': {
    title: 'Projizierte Unterdeckung',
    what: 'Berechtigungen, die dem Werk bis Jahresende voraussichtlich fehlen.',
    steel: 'Eine Unterdeckung muss am Markt zu dem dann geltenden Kohlenstoffpreis gekauft werden, daher ist sie ein direktes finanzielles Risiko.',
    useIt: 'Multiplizieren Sie mit dem Kohlenstoffpreis, um die Kosten zu sehen, die in der Risikokachel angezeigt werden.',
  },
  'kpi:exposure': {
    title: 'Kohlenstoffkostenrisiko',
    what: 'Der Geldwert der projizierten Unterdeckung an Berechtigungen.',
    steel: 'Das übersetzt eine Umweltzahl in eine Zeile, die die Finanzleitung versteht, und so wird Dekarbonisierung finanziert.',
    useIt: 'Er bewegt sich sowohl mit den Werksemissionen als auch mit dem Marktpreis für Kohlenstoff.',
  },
  'kpi:intensity': {
    title: 'Emissionsintensität',
    what: 'CO2, das pro produzierter Tonne Stahl freigesetzt wird.',
    steel:
      'Intensität ist die faire Art, Werke und Jahre zu vergleichen, weil Gesamtemissionen schon durch geringere Produktion fallen. Intensität fällt nur, wenn der Prozess besser wird.',
    useIt: 'Nutzen Sie dies statt Gesamttonnen, wenn Sie Fortschritt beurteilen.',
  },
  'kpi:target': {
    title: 'Ziel',
    what: 'Der Wert, zu dem sich das Werk verpflichtet hat, neben dem tatsächlichen Wert angezeigt.',
    steel: 'Ziele in dieser Demo sind Pilotverpflichtungen, keine gemessenen Ergebnisse. Der gemessene Wert wird immer daneben gezeigt.',
    useIt: 'Die Lücke zwischen beiden muss das Verbesserungsprogramm schließen.',
  },
  'kpi:records': {
    title: 'Prüfdatensätze',
    what: 'Wie viele Ereignisse in das manipulationssichere Audit-Protokoll geschrieben wurden.',
    steel: 'Aufsichtsbehörden und Kunden fragen beide, wie eine gemeldete Zahl entstanden ist. Jede Berechnung hier hinterlässt einen Datensatz, der das beantwortet.',
    useIt: 'Öffnen Sie die Tabelle, um einzelne Einträge zu prüfen.',
  },
  'kpi:immutable': {
    title: 'Kettenintegrität',
    what: 'Ob das Audit-Protokoll von Anfang bis Ende verifiziert wird.',
    steel:
      'Jeder Eintrag trägt einen kryptografischen Fingerabdruck des vorherigen. Eine Änderung an einem alten Datensatz bricht daher jeden folgenden Fingerabdruck und ist sofort sichtbar.',
    useIt: 'Alles außer verifiziert bedeutet, dass das Protokoll nicht als Grundlage verwendet werden sollte.',
  },
  'kpi:models': {
    title: 'Registrierte Modelle',
    what: 'Wie viele Vorhersagemodelle mit erfasster Version registriert sind.',
    steel: 'Wenn eine Vorhersage eine Entscheidung beeinflusst hat, müssen Sie genau wissen, welche Version welchen Modells sie erzeugt hat.',
    useIt: 'Die Modellversion erscheint neben jeder Vorhersage in der Audit-Tabelle.',
  },
  'kpi:domains': {
    title: 'Abgedeckte Bereiche',
    what: 'Wie viele Bereiche des Werks in der Audit-Spur vertreten sind.',
    steel: 'Teilabdeckung ist eine Compliance-Lücke. Ziel ist, dass jeder entscheidungsrelevante Bereich in dasselbe Protokoll schreibt.',
    useIt: 'Filtern Sie die Audit-Tabelle nach Bereich, um einen Bereich zu prüfen.',
  },

  // --------------------------------------------------------------- knowledge
  'kpi:sessions': {
    title: 'Erfassungssitzungen',
    what: 'Interviews mit erfahrenen Bedienern, die aufgezeichnet und in Verfahrensentwürfe umgewandelt wurden.',
    steel:
      'Viel Wissen in einem Stahlwerk steckt in den Köpfen von Menschen, die den Ofen dreißig Jahre betrieben haben. Es vor ihrem Ruhestand zu erfassen ist ein echtes industrielles Problem.',
    useIt: 'Öffnen Sie eine Sitzung, um das Transkript neben dem daraus entstandenen Entwurf zu sehen.',
  },
  'kpi:coverage': {
    title: 'Verfahrensabdeckung',
    what: 'Anteil kritischer Aufgaben, die jetzt ein schriftliches und genehmigtes Verfahren haben.',
    steel: 'Lücken in der Abdeckung sind Stellen, an denen das Werk davon abhängt, dass eine einzelne Person verfügbar ist.',
    useIt: 'Nutzen Sie sie, um die nächsten Interviews zu priorisieren.',
  },
  'kpi:approved': {
    title: 'Genehmigte Verfahren',
    what: 'Entwürfe, die ein qualifizierter Mensch geprüft und freigegeben hat.',
    steel: 'Ein von einer Maschine geschriebenes und nie geprüftes Verfahren ist eine Haftung. Die Genehmigung ist die Kontrolle, die das Ergebnis nutzbar macht.',
    useIt: 'Nur genehmigte Verfahren werden vom Assistenten als Antworten zurückgegeben.',
  },
  'kpi:review': {
    title: 'Warten auf Prüfung',
    what: 'Entwürfe, die darauf warten, dass ein Mensch sie annimmt, korrigiert oder ablehnt.',
    steel: 'Diese Warteschlange ist das Human-in-the-loop-Tor. Nichts umgeht es.',
    useIt: 'Eine wachsende Warteschlange bedeutet, dass Prüfungskapazität, nicht Erfassungskapazität, der Engpass ist.',
  },

  // -------------------------------------------------------------- operations
  'kpi:oee': {
    title: 'Gesamtanlageneffektivität (OEE)',
    what: 'Eine Zahl, die kombiniert, wie lange Ausrüstung lief, wie schnell sie lief und wie viel der Ausbringung gut war.',
    steel: 'Die Standard-Scorecard der Fertigung. Sie verhindert, dass ein Werk Erfolg bei Verfügbarkeit meldet und gleichzeitig still Produkt verschrottet.',
    useIt: 'Wenn sie fällt, prüfen Sie, welcher der drei Teile es verursacht hat.',
  },
  'kpi:throughput': {
    title: 'Durchsatz',
    what: 'Tonnen Stahl, die im Zeitraum produziert wurden.',
    steel: 'Die Ausbringung des Werks und der Nenner fast jeder anderen Kennzahl in diesem Portal.',
    useIt: 'Lesen Sie Intensitätskennzahlen immer dagegen. Niedrige Ausbringung lässt Gesamtemissionen besser aussehen.',
  },
  'kpi:ontime': {
    title: 'Termingerechte Lieferung',
    what: 'Anteil der Kundenaufträge, die bis zum zugesagten Datum versandt wurden.',
    steel: 'Stahl geht in geplante nachgelagerte Produktionslinien, daher stoppt eine späte Lieferung die Fabrik eines anderen.',
    useIt: 'Späte Lieferungen lassen sich oft auf ungeplante Stillstände oder Nacharbeit zurückführen.',
  },
  'kpi:alerts': {
    title: 'Aktive Warnungen',
    what: 'Zustände, die aktuell als aufmerksamkeitsbedürftig markiert sind.',
    steel: 'Alarmmüdigkeit ist ein echtes Sicherheitsrisiko, daher zielt diese Plattform auf wenige, aussagekräftige Warnungen statt auf viele.',
    useIt: 'Klicken Sie sich durch, um das zugrunde liegende Signal jeder Warnung zu sehen.',
  },

  // ---------------------------------------------------------- platform ops
  'kpi:util': {
    title: 'Kapazitätsauslastung',
    what: 'Wie viel der reservierten Analyse-Rechenkapazität genutzt wird.',
    steel: 'Die Plattform läuft bewusst auf kleiner, stundenweise bezahlter Kapazität, damit eine Demonstrationsumgebung nicht wie eine Produktionsumgebung kostet.',
    useIt: 'Dauerhaft hohe Auslastung ist das Signal zum Hochskalieren, bevor Aufträge in Warteschlangen geraten.',
  },
  'kpi:utilization': {
    title: 'Kapazitätsauslastung',
    what: 'Wie viel der reservierten Analyse-Rechenkapazität genutzt wird.',
    steel: 'Analysekapazität wird stundenweise berechnet, ob sie beschäftigt ist oder nicht, daher ist Leerlaufkapazität reine Verschwendung.',
    useIt: 'Nutzen Sie sie mit der Kostenkachel, um zu beurteilen, ob die aktuelle Größe passt.',
  },
  'kpi:spend': {
    title: 'Plattformausgaben',
    what: 'Was die Analyseplattform im angezeigten Zeitraum gekostet hat.',
    steel: 'Ein Entscheidungsunterstützungssystem muss weniger kosten als die Verluste, die es verhindert. Die Kosten offen zu zeigen gehört zu diesem Argument.',
    useIt: 'Vergleichen Sie sie mit den Einsparungen auf den Energiebildschirmen.',
  },
  'kpi:cost': {
    title: 'Kosten',
    what: 'Der Geldbetrag für das Element, das auf dieser Kachel gezeigt wird.',
    steel: 'Jede technische Entscheidung auf dieser Plattform hat einen Preis, und er ist bewusst sichtbar statt versteckt.',
    useIt: 'Öffnen Sie die Kostentabelle für die Aufschlüsselung nach Dienst.',
  },
  'kpi:rate': {
    title: 'Verarbeitungsrate',
    what: 'Wie viele Datensätze die Pipeline pro Zeiteinheit verarbeitet.',
    steel: 'Sensordaten kommen kontinuierlich an. Wenn die Pipeline langsamer verarbeitet als Daten ankommen, fallen Dashboards unbemerkt zurück.',
    useIt: 'Lesen Sie sie mit der Datenaktualität. Gesunde Rate, aber alte Daten bedeuten, dass etwas vorgelagert gestoppt hat.',
  },
  'kpi:fresh': {
    title: 'Datenaktualität',
    what: 'Wie lange es her ist, dass der neueste Datenpunkt angekommen ist.',
    steel: 'Ein Leitstandschirm mit Temperaturen von gestern ist schlimmer als gar kein Bildschirm, weil er aktuell aussieht.',
    useIt: 'Wenn dieser Wert wächst, behandeln Sie jede andere Zahl im Portal als verdächtig, bis er sich erholt.',
  },
}
