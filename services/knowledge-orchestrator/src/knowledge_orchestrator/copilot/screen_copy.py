"""Localized screen descriptions for the NovaSteel Copilot chat assistant.

Pure data module: no logic lives here. Consumed by
``knowledge_orchestrator.copilot.context``.
"""

from __future__ import annotations

from typing import Final

LANGUAGES: Final[tuple[str, ...]] = ("en", "fr", "de", "nl", "es")

# section-slug -> language -> one-sentence description of what the screen shows
SCREEN_SUMMARIES: Final[dict[str, dict[str, str]]] = {
    "command-center": {
        "en": (
            "Cross-persona triage: the highest-severity signals across furnace, "
            "energy, quality and compliance, each with a next-best action."
        ),
        "fr": (
            "Triage interprofils : les signaux les plus critiques liés au four, "
            "à l'énergie, à la qualité et à la conformité, chacun associé à la "
            "meilleure action suivante."
        ),
        "de": (
            "Rollenübergreifende Triage: die Signale mit höchster Schwere über "
            "Ofen, Energie, Qualität und Compliance hinweg, jeweils mit der "
            "nächsten empfohlenen Maßnahme."
        ),
        "nl": (
            "Roloverstijgende triage: de signalen met de hoogste ernst voor oven, "
            "energie, kwaliteit en compliance, telkens met een beste vervolgstap."
        ),
        "es": (
            "Triaje transversal entre perfiles: las señales de mayor severidad en "
            "horno, energía, calidad y cumplimiento, cada una con la mejor acción "
            "siguiente."
        ),
    },
    "operations": {
        "en": (
            "Live production health: throughput versus target, OEE, and incident "
            "triage for the selected site."
        ),
        "fr": (
            "Santé de production en temps réel : débit par rapport à l'objectif, "
            "TRS / OEE et triage des incidents pour le site sélectionné."
        ),
        "de": (
            "Live-Produktionszustand: Durchsatz gegenüber Ziel, OEE und "
            "Vorfalltriage für den ausgewählten Standort."
        ),
        "nl": (
            "Actuele productiestatus: doorvoer versus doel, OEE en incidenttriage "
            "voor de geselecteerde site."
        ),
        "es": (
            "Salud de producción en vivo: producción frente al objetivo, OEE y "
            "triaje de incidentes para la planta seleccionada."
        ),
    },
    "furnace-health": {
        "en": (
            "Refractory lining wear forecasting, thermal signatures and the "
            "maintenance plan derived from remaining useful life."
        ),
        "fr": (
            "Prévision de l'usure du garnissage réfractaire, signatures thermiques "
            "et plan de maintenance dérivé de la durée de vie utile restante."
        ),
        "de": (
            "Prognose des Verschleißes der feuerfesten Zustellung, thermische "
            "Signaturen und der aus der Restnutzungsdauer abgeleitete "
            "Instandhaltungsplan."
        ),
        "nl": (
            "Voorspelling van slijtage van de vuurvaste bekleding, thermische "
            "profielen en het onderhoudsplan afgeleid van de resterende nuttige "
            "levensduur."
        ),
        "es": (
            "Previsión del desgaste del revestimiento refractario, firmas térmicas "
            "y plan de mantenimiento derivado de la vida útil restante."
        ),
    },
    "energy-optimization": {
        "en": (
            "Constrained dispatch proposals scored against day-ahead spot prices "
            "and grid carbon intensity."
        ),
        "fr": (
            "Propositions d'ordonnancement sous contraintes, évaluées au regard "
            "des prix spot day-ahead et de l'intensité carbone du réseau."
        ),
        "de": (
            "Restriktionskonforme Einsatzvorschläge, bewertet gegen "
            "Day-Ahead-Spotpreise und die CO₂-Intensität des Stromnetzes."
        ),
        "nl": (
            "Dispatchvoorstellen binnen beperkingen, beoordeeld tegenover "
            "day-ahead spotprijzen en de koolstofintensiteit van het net."
        ),
        "es": (
            "Propuestas de despacho con restricciones, puntuadas frente a precios "
            "spot diarios anticipados y la intensidad de carbono de la red."
        ),
    },
    "quality": {
        "en": (
            "Batch quality outcomes, genealogy back to source heats, bounded "
            "what-if analysis and statistical process control."
        ),
        "fr": (
            "Résultats qualité par lot, généalogie jusqu'aux coulées sources, "
            "analyse what-if bornée et maîtrise statistique des procédés."
        ),
        "de": (
            "Qualitätsergebnisse je Charge, Genealogie zurück zu den "
            "Ursprungsschmelzen, begrenzte Was-wäre-wenn-Analyse und "
            "statistische Prozessregelung."
        ),
        "nl": (
            "Kwaliteitsuitkomsten per batch, genealogie terug naar oorspronkelijke "
            "smelten, begrensde what-if-analyse en statistische procesbeheersing."
        ),
        "es": (
            "Resultados de calidad por lote, genealogía hasta las coladas de "
            "origen, análisis what-if acotado y control estadístico de procesos."
        ),
    },
    "sustainability-compliance": {
        "en": (
            "Emissions ledger, EU ETS and CBAM exposure, and the auditable "
            "evidence trail behind every reported figure."
        ),
        "fr": (
            "Registre des émissions, exposition à l'EU ETS et au CBAM, et piste "
            "de preuves auditable derrière chaque chiffre déclaré."
        ),
        "de": (
            "Emissionsregister, Exposition gegenüber EU ETS und CBAM sowie die "
            "auditierbare Nachweiskette hinter jeder berichteten Kennzahl."
        ),
        "nl": (
            "Emissiegrootboek, blootstelling aan EU ETS en CBAM, en het "
            "auditeerbare bewijsspoor achter elk gerapporteerd cijfer."
        ),
        "es": (
            "Libro de emisiones, exposición a EU ETS y CBAM, y la pista de "
            "evidencia auditable detrás de cada cifra reportada."
        ),
    },
    "knowledge-hub": {
        "en": (
            "Search over approved procedures, plus governance of consent-bound "
            "capture and human review."
        ),
        "fr": (
            "Recherche dans les procédures approuvées, avec gouvernance de la "
            "captation soumise au consentement et de la revue humaine."
        ),
        "de": (
            "Suche über freigegebene Verfahren sowie Governance für "
            "einwilligungsgebundene Erfassung und menschliche Prüfung."
        ),
        "nl": (
            "Zoeken in goedgekeurde procedures, plus governance van vastlegging "
            "op basis van toestemming en menselijke beoordeling."
        ),
        "es": (
            "Búsqueda en procedimientos aprobados, más gobernanza de la captura "
            "sujeta a consentimiento y revisión humana."
        ),
    },
    "executive-overview": {
        "en": (
            "Cross-site KPIs with pilot targets shown next to measured evidence, "
            "and an optional board report."
        ),
        "fr": (
            "KPI multisites avec objectifs pilotes affichés à côté des preuves "
            "mesurées, et rapport de conseil d'administration en option."
        ),
        "de": (
            "Standortübergreifende KPIs mit Pilotzielen neben gemessenen "
            "Nachweisen und einem optionalen Vorstandsbericht."
        ),
        "nl": (
            "Site-overstijgende KPI's met pilotdoelen naast gemeten bewijs, en "
            "een optioneel bestuursrapport."
        ),
        "es": (
            "KPI entre plantas con objetivos piloto mostrados junto a evidencia "
            "medida, y un informe opcional para el consejo."
        ),
    },
    "platform-ops": {
        "en": (
            "Restricted non-production Fabric capacity lifecycle, pipeline job "
            "health and cost telemetry."
        ),
        "fr": (
            "Cycle de vie restreint de la capacité Fabric hors production, santé "
            "des jobs de pipeline et télémétrie des coûts."
        ),
        "de": (
            "Eingeschränkter Lebenszyklus der Nichtproduktions-Fabric-Kapazität, "
            "Zustand der Pipeline-Jobs und Kostentelemetrie."
        ),
        "nl": (
            "Beperkte levenscyclus van niet-productie Fabric-capaciteit, "
            "gezondheid van pipelinejobs en kostentelemetrie."
        ),
        "es": (
            "Ciclo de vida restringido de la capacidad Fabric no productiva, "
            "salud de trabajos de canalización y telemetría de costes."
        ),
    },
}
