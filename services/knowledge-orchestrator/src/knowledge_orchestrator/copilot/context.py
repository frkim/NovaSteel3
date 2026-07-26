"""Screen-context resolution for the Copilot chat assistant.

The panel is docked next to a live dashboard, so a question is almost never
self-contained. "What is the risk?" means *lining risk* on Furnace Health and
*ETS exposure* on Sustainability & Compliance. This module turns the shell's
navigation state plus the raw question into an ordered list of concepts that
the agent grounds its answer on.

Deliberately decoupled from the glossary: concepts carry a canonical English
label and the glossary is searched by text, so neither file has to know the
other's identifiers.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .models import ScreenContext
from .screen_copy import SCREEN_SUMMARIES

_TOKEN = re.compile(r"[a-z0-9]+")


def _fold(text: str) -> str:
    """Lowercase and strip accents so ``Émissions`` matches ``emissions``."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def tokenize(text: str) -> set[str]:
    return set(_TOKEN.findall(_fold(text)))


@dataclass(frozen=True)
class Concept:
    """A domain notion the assistant can ground an answer on.

    ``label`` is the canonical English term shown to the user. ``glossary_id``
    pins the concept to a specific glossary entry when the wording differs from
    the glossary's own term (for example *Maintenance window* is defined under
    *Work order*); when it is ``None`` the glossary is searched by label.
    ``triggers`` are folded, accent-free words in any of the five supported
    languages that should surface this concept.
    """

    key: str
    label: str
    triggers: frozenset[str] = field(default_factory=frozenset)
    glossary_id: str | None = None

    def matches(self, tokens: set[str]) -> bool:
        """Match a trigger as a whole word, or inside a compound noun.

        German and Dutch build single words out of several morphemes --
        *Zustellungsrisiko*, *vuurvastrisico* -- so whole-token matching alone
        would silently fail for two of the five supported languages. Only
        triggers of five characters or more are matched inside a token, which
        keeps short codes such as ``rul``, ``oee`` and ``spc`` from firing on
        unrelated words.
        """
        if self.triggers & tokens:
            return True
        compoundable = [trigger for trigger in self.triggers if len(trigger) >= 5]
        return any(
            trigger in token
            for token in tokens
            for trigger in compoundable
            if len(token) > len(trigger)
        )


def _concept(key: str, label: str, *triggers: str, glossary_id: str | None = None) -> Concept:
    return Concept(
        key=key,
        label=label,
        triggers=frozenset(_fold(t) for t in triggers),
        glossary_id=glossary_id,
    )


# --- Concepts -------------------------------------------------------------
# Triggers cover EN/FR/DE/NL/ES so a question asked in any supported language
# resolves to the same concept.

LINING_RISK = _concept(
    "lining_risk",
    "Lining risk",
    "lining", "refractory", "revetement", "garnissage", "refractaire",
    "zustellung", "feuerfest", "vuurvast", "bekleding", "revestimiento",
    "refractario",
    glossary_id="lining-risk",
)
RUL = _concept(
    "remaining_useful_life",
    "Remaining useful life",
    "rul", "remaining", "life", "lifetime", "duree", "restante", "vie",
    "restlebensdauer", "lebensdauer", "resterende", "levensduur",
    "util", "restante",
    glossary_id="remaining-useful-life",
)
THERMAL_SIGNATURE = _concept(
    "thermal_signature",
    "Thermal signature",
    "thermal", "signature", "temperature", "thermique", "thermisch",
    "thermische", "termica", "termico", "hotspot", "hot",
    glossary_id="thermal-signature",
)
CAMPAIGN = _concept(
    "campaign",
    "Furnace campaign",
    "campaign", "campagne", "kampagne", "campana", "heat", "coulee",
    "charge", "schmelze",
    glossary_id="refractory",
)
MAINTENANCE_WINDOW = _concept(
    "maintenance_window",
    "Maintenance window",
    "maintenance", "window", "fenetre", "wartung", "wartungsfenster",
    "onderhoud", "mantenimiento", "shutdown", "arret", "stillstand",
    glossary_id="work-order",
)

SPOT_PRICE = _concept(
    "spot_price",
    "Spot price",
    "spot", "price", "prix", "preis", "prijs", "precio", "tariff", "tarif",
    "market", "marche", "markt", "mercado",
    glossary_id="spot-price",
)
LOAD_SHIFT = _concept(
    "load_shift",
    "Load shift",
    "load", "shift", "shifting", "decalage", "charge", "lastverschiebung",
    "verschuiving", "belasting", "desplazamiento", "carga", "schedule",
    "planning", "dispatch",
    glossary_id="load-shifting",
)
CARBON_INTENSITY = _concept(
    "carbon_intensity",
    "Carbon intensity",
    "carbon", "intensity", "carbone", "intensite", "kohlenstoff",
    "intensitat", "koolstof", "intensiteit", "carbono", "intensidad",
    "gco2", "grid",
    glossary_id="carbon-intensity",
)
ENERGY_COST = _concept(
    "energy_cost",
    "Energy cost",
    "energy", "cost", "energie", "cout", "kosten", "coste", "costo",
    "energia", "mwh", "kwh", "consumption", "consommation", "verbrauch",
    "verbruik", "consumo", "savings", "economies", "einsparung",
    "besparing", "ahorro",
    glossary_id="energy-intensity-gj-per-tonne",
)

YIELD = _concept(
    "yield",
    "Yield",
    "yield", "rendement", "ausbeute", "opbrengst", "rendimiento",
    "prime", "firstpass",
    glossary_id="yield",
)
DEFECT = _concept(
    "defect",
    "Defect rate",
    "defect", "defects", "defaut", "defauts", "fehler", "defect",
    "defecten", "defecto", "defectos", "scrap", "rebut", "ausschuss",
    "afkeur", "chatarra",
    glossary_id="cpk",
)
SPC = _concept(
    "spc",
    "Statistical process control",
    "spc", "control", "controle", "regelkarte", "cpk", "sigma",
    "capability", "capabilite", "chart",
    glossary_id="spc",
)
GENEALOGY = _concept(
    "genealogy",
    "Batch genealogy",
    "genealogy", "genealogie", "batch", "lot", "charge", "partij",
    "lote", "traceability", "tracabilite", "rueckverfolgbarkeit",
    "traceerbaarheid", "trazabilidad",
    glossary_id="batch-genealogy",
)

ETS_EXPOSURE = _concept(
    "ets_exposure",
    "EU ETS exposure",
    "ets", "eua", "allowance", "allowances", "quota", "quotas",
    "zertifikat", "zertifikate", "emissierecht", "emissierechten",
    "derecho", "derechos", "exposure", "exposition", "risiko",
    "blootstelling", "exposicion",
    glossary_id="eu-ets",
)
CBAM = _concept(
    "cbam",
    "CBAM",
    "cbam", "border", "frontiere", "grenzausgleich", "grens", "frontera",
    "import", "importation", "einfuhr", "invoer", "importacion",
    glossary_id="cbam",
)
EMISSIONS = _concept(
    "emissions",
    "Emissions ledger",
    "emission", "emissions", "co2", "carbon", "ghg", "ausstoss",
    "uitstoot", "emision", "emisiones", "scope", "ledger", "registre",
    "hauptbuch", "grootboek", "libro",
    glossary_id="scope-1-2-emissions",
)

THROUGHPUT = _concept(
    "throughput",
    "Throughput",
    "throughput", "production", "output", "debit", "durchsatz",
    "doorvoer", "rendimiento", "tonnes", "tons", "tonnage", "tph",
    glossary_id="tap-to-tap-time",
)
OEE = _concept(
    "oee",
    "OEE",
    "oee", "availability", "disponibilite", "verfugbarkeit",
    "beschikbaarheid", "disponibilidad", "utilisation", "auslastung",
    glossary_id="oee",
)
INCIDENT = _concept(
    "incident",
    "Incident",
    "incident", "incidents", "alert", "alerts", "alerte", "alertes",
    "alarm", "alarme", "storing", "alerta", "alertas", "stoppage",
    "downtime", "panne", "ausfall", "stilstand", "parada",
    glossary_id="rca",
)

PROCEDURE = _concept(
    "procedure",
    "Approved procedure",
    "procedure", "procedures", "sop", "verfahren", "arbeitsanweisung",
    "procedimiento", "procedimientos", "instruction", "anleitung",
    "instructie", "knowledge", "connaissance", "wissen", "kennis",
    "conocimiento",
    glossary_id="approved-procedure",
)
CONSENT = _concept(
    "consent",
    "Capture consent",
    "consent", "consentement", "einwilligung", "toestemming",
    "consentimiento", "capture", "captation", "erfassung", "vastlegging",
    "captura", "gdpr", "rgpd", "privacy", "vie", "privee", "datenschutz",
    glossary_id="capture-consent",
)

CAPACITY = _concept(
    "capacity",
    "Fabric capacity",
    "capacity", "capacite", "kapazitat", "capaciteit", "capacidad",
    "fabric", "sku", "f2", "f4", "f8", "cu", "pause", "paused", "resume",
    "suspendu", "pausiert", "gepauzeerd", "pausado",
    glossary_id="fabric-capacity-unit",
)
PIPELINE_JOB = _concept(
    "pipeline_job",
    "Pipeline job",
    "job", "jobs", "pipeline", "pipelines", "tache", "taches", "auftrag",
    "auftrage", "taak", "taken", "trabajo", "trabajos", "refresh",
    "actualisation", "aktualisierung", "vernieuwing", "actualizacion",
    glossary_id="medallion-architecture",
)
COST_TELEMETRY = _concept(
    "cost_telemetry",
    "Platform cost telemetry",
    "cost", "costs", "spend", "budget", "cout", "couts", "kosten",
    "coste", "costes", "telemetry", "telemetrie", "telemetria",
    glossary_id="fabric-capacity-unit",
)

TARGET_VS_EVIDENCE = _concept(
    "target_vs_evidence",
    "Target versus measured evidence",
    "target", "targets", "objectif", "objectifs", "ziel", "ziele",
    "doel", "doelen", "objetivo", "objetivos", "measured", "mesure",
    "gemessen", "gemeten", "medido", "evidence", "preuve", "nachweis",
    "bewijs", "evidencia", "actual", "reel", "tatsachlich",
    "werkelijk", "real",
)


@dataclass(frozen=True)
class ScreenProfile:
    """What the assistant knows about a dashboard section."""

    section: str
    title: str
    persona: str
    summary: str
    concepts: tuple[Concept, ...]
    sub_views: dict[str, tuple[Concept, ...]] = field(default_factory=dict)

    @property
    def default_concept(self) -> Concept:
        """The notion a bare, ambiguous question resolves to on this screen."""
        return self.concepts[0]

    def summary_in(self, language: str) -> str:
        """Return the screen description in a supported language.

        Falls back to the English ``summary`` so a screen added before its copy
        is translated still produces a complete answer.
        """
        return SCREEN_SUMMARIES.get(self.section, {}).get(language) or self.summary


_PROFILES: tuple[ScreenProfile, ...] = (
    ScreenProfile(
        section="command-center",
        title="Command Center",
        persona="Plant Manager",
        summary=(
            "Cross-persona triage: the highest-severity signals across furnace, "
            "energy, quality and compliance, each with a next-best action."
        ),
        concepts=(INCIDENT, LINING_RISK, ENERGY_COST, YIELD, ETS_EXPOSURE, THROUGHPUT),
    ),
    ScreenProfile(
        section="operations",
        title="Operations",
        persona="Plant Manager",
        summary=(
            "Live production health: throughput versus target, OEE, and incident "
            "triage for the selected site."
        ),
        concepts=(THROUGHPUT, OEE, INCIDENT, YIELD, ENERGY_COST),
    ),
    ScreenProfile(
        section="furnace-health",
        title="Furnace Health",
        persona="Furnace Operator & Maintenance/Reliability Engineer",
        summary=(
            "Refractory lining wear forecasting, thermal signatures and the "
            "maintenance plan derived from remaining useful life."
        ),
        concepts=(LINING_RISK, RUL, THERMAL_SIGNATURE, CAMPAIGN, MAINTENANCE_WINDOW),
        sub_views={
            "lining-forecast": (LINING_RISK, RUL, CAMPAIGN),
            "thermal-explorer": (THERMAL_SIGNATURE, LINING_RISK, CAMPAIGN),
            "maintenance-planner": (MAINTENANCE_WINDOW, RUL, LINING_RISK),
        },
    ),
    ScreenProfile(
        section="energy-optimization",
        title="Energy Optimization",
        persona="Energy Manager",
        summary=(
            "Constrained dispatch proposals scored against day-ahead spot prices "
            "and grid carbon intensity."
        ),
        concepts=(ENERGY_COST, SPOT_PRICE, LOAD_SHIFT, CARBON_INTENSITY),
        sub_views={
            "spot-price-schedule": (SPOT_PRICE, CARBON_INTENSITY, ENERGY_COST),
            "load-shift-simulator": (LOAD_SHIFT, ENERGY_COST, SPOT_PRICE),
        },
    ),
    ScreenProfile(
        section="quality",
        title="Quality",
        persona="Quality Engineer",
        summary=(
            "Batch quality outcomes, genealogy back to source heats, bounded "
            "what-if analysis and statistical process control."
        ),
        concepts=(YIELD, DEFECT, GENEALOGY, SPC),
        sub_views={
            "batches": (YIELD, GENEALOGY, DEFECT),
            "spc": (SPC, DEFECT, YIELD),
        },
    ),
    ScreenProfile(
        section="sustainability-compliance",
        title="Sustainability & Compliance",
        persona="Sustainability Officer",
        summary=(
            "Emissions ledger, EU ETS and CBAM exposure, and the auditable "
            "evidence trail behind every reported figure."
        ),
        concepts=(ETS_EXPOSURE, EMISSIONS, CBAM, TARGET_VS_EVIDENCE),
        sub_views={
            "emissions-ledger": (EMISSIONS, TARGET_VS_EVIDENCE, ETS_EXPOSURE),
            "ets-exposure": (ETS_EXPOSURE, CBAM, EMISSIONS),
            "audit": (TARGET_VS_EVIDENCE, EMISSIONS, CONSENT),
        },
    ),
    ScreenProfile(
        section="knowledge-hub",
        title="Knowledge Hub",
        persona="Knowledge Engineer/Admin",
        summary=(
            "Search over approved procedures, plus governance of consent-bound "
            "capture and human review."
        ),
        concepts=(PROCEDURE, CONSENT),
        sub_views={
            "procedures": (PROCEDURE, CONSENT),
            "capture-status": (CONSENT, PROCEDURE),
        },
    ),
    ScreenProfile(
        section="executive-overview",
        title="Executive Overview",
        persona="Executive",
        summary=(
            "Cross-site KPIs with pilot targets shown next to measured evidence, "
            "and an optional board report."
        ),
        concepts=(TARGET_VS_EVIDENCE, ENERGY_COST, EMISSIONS, YIELD, THROUGHPUT),
        sub_views={
            "overview": (TARGET_VS_EVIDENCE, ENERGY_COST, EMISSIONS),
            "board-report": (TARGET_VS_EVIDENCE, EMISSIONS, ENERGY_COST),
        },
    ),
    ScreenProfile(
        section="platform-ops",
        title="Platform Ops",
        persona="Platform Ops",
        summary=(
            "Restricted non-production Fabric capacity lifecycle, pipeline job "
            "health and cost telemetry."
        ),
        concepts=(CAPACITY, PIPELINE_JOB, COST_TELEMETRY),
        sub_views={
            "capacity": (CAPACITY, COST_TELEMETRY),
            "jobs": (PIPELINE_JOB, CAPACITY),
            "cost-telemetry": (COST_TELEMETRY, CAPACITY),
        },
    ),
)

PROFILES_BY_SECTION: dict[str, ScreenProfile] = {p.section: p for p in _PROFILES}
DEFAULT_PROFILE = PROFILES_BY_SECTION["command-center"]

ALL_CONCEPTS: tuple[Concept, ...] = tuple(
    {concept.key: concept for profile in _PROFILES for concept in profile.concepts}.values()
)


def profile_for(section: str) -> ScreenProfile:
    """Return the profile for a section slug, falling back to the Command Center."""
    return PROFILES_BY_SECTION.get((section or "").strip().lower(), DEFAULT_PROFILE)


@dataclass(frozen=True)
class ResolvedContext:
    """The grounding decision made for one question."""

    profile: ScreenProfile
    concepts: tuple[Concept, ...]
    matched_explicitly: bool

    @property
    def primary(self) -> Concept:
        return self.concepts[0]

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(concept.label for concept in self.concepts)


def resolve(question: str, context: ScreenContext, *, limit: int = 3) -> ResolvedContext:
    """Rank the concepts a question is most likely about.

    Concepts named explicitly in the question win, in the screen's own priority
    order. When nothing is named -- the "what is the risk?" case -- the screen's
    sub-view ordering decides, which is exactly the disambiguation the operator
    expects.
    """
    profile = profile_for(context.section)
    sub_view = (context.sub_view or "").strip().lower()
    ordered = profile.sub_views.get(sub_view, profile.concepts)
    # Sub-view concepts first, then the rest of the screen, de-duplicated.
    candidates: list[Concept] = []
    for concept in (*ordered, *profile.concepts):
        if concept.key not in {existing.key for existing in candidates}:
            candidates.append(concept)

    tokens = tokenize(question)
    explicit = [concept for concept in candidates if concept.matches(tokens)]
    if explicit:
        return ResolvedContext(profile, tuple(explicit[:limit]), True)
    return ResolvedContext(profile, tuple(candidates[:limit]), False)
