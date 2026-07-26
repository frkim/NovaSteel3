"""Curated public-context corpus for the Copilot "Online search" toggle.

The demo runs in a controlled environment with no outbound internet access from
the container, so ticking "Online search" does not hit a live search engine.
Instead it unlocks this small corpus of stable, public regulatory and market
context that the offline agent is otherwise not allowed to use.

That distinction is the point of the toggle and is stated in the answer itself:
with the box unticked the assistant answers strictly from NovaSteel's internal
material; with it ticked it may add clearly-labelled public context.

Every entry is deliberately durable (structural rules and their official
sources) rather than a dated headline, so the demo cannot go stale mid-defence.
Entries carry the official URL so a reviewer can verify them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .context import ResolvedContext, tokenize
from .models import DEFAULT_LANGUAGE

MAX_HITS = 3


@dataclass(frozen=True)
class OnlineHit:
    """One piece of public context surfaced by the online-search toggle."""

    source_id: str
    title: str
    snippet: str
    url: str
    concepts: frozenset[str] = field(default_factory=frozenset)
    triggers: frozenset[str] = field(default_factory=frozenset)


def _hit(
    source_id: str,
    title: dict[str, str],
    snippet: dict[str, str],
    url: str,
    concepts: tuple[str, ...],
    triggers: tuple[str, ...] = (),
) -> tuple[str, dict[str, str], dict[str, str], str, tuple[str, ...], tuple[str, ...]]:
    return source_id, title, snippet, url, concepts, triggers


# Raw multilingual corpus. Rendered into OnlineHit for a specific language by
# ``online_context``.
_CORPUS: tuple[tuple[str, dict[str, str], dict[str, str], str, tuple[str, ...], tuple[str, ...]], ...] = (
    _hit(
        "eu-ets-overview",
        {
            "en": "EU Emissions Trading System \u2014 how the cap works",
            "fr": "Syst\u00e8me d'\u00e9change de quotas de l'UE \u2014 fonctionnement du plafond",
            "de": "EU-Emissionshandelssystem \u2014 Funktionsweise der Obergrenze",
            "nl": "EU-emissiehandelssysteem \u2014 hoe het plafond werkt",
            "es": "R\u00e9gimen de comercio de derechos de emisi\u00f3n de la UE \u2014 c\u00f3mo funciona el l\u00edmite",
        },
        {
            "en": "The EU ETS caps total emissions from covered installations and lets participants trade allowances (EUAs). The cap declines every year, so an installation either abates or buys allowances at the prevailing market price.",
            "fr": "Le SEQE-UE plafonne les \u00e9missions totales des installations couvertes et permet d'\u00e9changer des quotas (EUA). Le plafond baisse chaque ann\u00e9e : une installation doit donc r\u00e9duire ses \u00e9missions ou acheter des quotas au prix du march\u00e9.",
            "de": "Das EU-EHS begrenzt die Gesamtemissionen der erfassten Anlagen und erlaubt den Handel mit Zertifikaten (EUA). Die Obergrenze sinkt j\u00e4hrlich, sodass eine Anlage entweder mindert oder Zertifikate zum Marktpreis kauft.",
            "nl": "Het EU-ETS begrenst de totale uitstoot van gedekte installaties en laat deelnemers emissierechten (EUA's) verhandelen. Het plafond daalt jaarlijks, dus een installatie reduceert of koopt rechten tegen de marktprijs.",
            "es": "El RCDE UE limita las emisiones totales de las instalaciones cubiertas y permite negociar derechos (EUA). El l\u00edmite baja cada a\u00f1o, por lo que una instalaci\u00f3n debe reducir emisiones o comprar derechos al precio de mercado.",
        },
        "https://climate.ec.europa.eu/eu-action/eu-emissions-trading-system-eu-ets_en",
        ("ets_exposure", "emissions", "target_vs_evidence"),
        ("ets", "eua", "allowance", "quota", "announcement", "announcements", "news", "actualite", "nachricht", "nieuws", "noticia"),
    ),
    _hit(
        "eu-ets-free-allocation-phaseout",
        {
            "en": "Free allocation for steel is being phased out alongside CBAM",
            "fr": "L'allocation gratuite pour l'acier dispara\u00eet progressivement avec le MACF",
            "de": "Die kostenlose Zuteilung f\u00fcr Stahl wird parallel zum CBAM abgebaut",
            "nl": "Gratis toewijzing voor staal wordt afgebouwd samen met CBAM",
            "es": "La asignaci\u00f3n gratuita para el acero se elimina progresivamente junto con el MAFC",
        },
        {
            "en": "Steel is a CBAM sector, and the free allowances it historically received are being phased down over the 2026-2034 window as the carbon border adjustment is phased in. The practical effect is that a tonne of CO2 progressively becomes a real cash cost.",
            "fr": "L'acier est un secteur MACF : les quotas gratuits dont il b\u00e9n\u00e9ficiait sont r\u00e9duits sur la p\u00e9riode 2026-2034 \u00e0 mesure que l'ajustement carbone aux fronti\u00e8res mont\u00e9e en puissance. Concr\u00e8tement, la tonne de CO2 devient un co\u00fbt de tr\u00e9sorerie r\u00e9el.",
            "de": "Stahl ist ein CBAM-Sektor: Die bisher kostenlos zugeteilten Zertifikate werden zwischen 2026 und 2034 abgebaut, w\u00e4hrend der CO2-Grenzausgleich eingef\u00fchrt wird. Praktisch wird eine Tonne CO2 damit schrittweise zu echten Kosten.",
            "nl": "Staal is een CBAM-sector: de historisch gratis toegekende rechten worden tussen 2026 en 2034 afgebouwd terwijl de koolstofgrenscorrectie wordt ingevoerd. Praktisch wordt een ton CO2 daarmee een echte kaskost.",
            "es": "El acero es un sector MAFC: los derechos gratuitos que recib\u00eda se reducen entre 2026 y 2034 a medida que se implanta el ajuste en frontera por carbono. En la pr\u00e1ctica, la tonelada de CO2 pasa a ser un coste real de caja.",
        },
        "https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en",
        ("ets_exposure", "cbam", "emissions"),
        ("cbam", "free", "allocation", "gratuit", "kostenlos", "gratis", "phase", "2026", "2034"),
    ),
    _hit(
        "day-ahead-market",
        {
            "en": "European day-ahead power markets clear hourly",
            "fr": "Les march\u00e9s europ\u00e9ens de l'\u00e9lectricit\u00e9 J-1 se r\u00e8glent \u00e0 l'heure",
            "de": "Europ\u00e4ische Day-Ahead-Strommarkt werden st\u00fcndlich abgerechnet",
            "nl": "Europese day-ahead-elektriciteitsmarkten klaren per uur",
            "es": "Los mercados el\u00e9ctricos diarios europeos casan por horas",
        },
        {
            "en": "Day-ahead auctions set an hourly clearing price for the following day across coupled European bidding zones. That hourly granularity is what makes industrial load shifting economically meaningful.",
            "fr": "Les ench\u00e8res J-1 fixent un prix horaire pour le lendemain sur les zones de march\u00e9 europ\u00e9ennes coupl\u00e9es. C'est cette granularit\u00e9 horaire qui rend le d\u00e9calage de charge industriel \u00e9conomiquement pertinent.",
            "de": "Day-Ahead-Auktionen legen f\u00fcr den Folgetag st\u00fcndliche Preise in den gekoppelten europ\u00e4ischen Gebotszonen fest. Diese st\u00fcndliche Granularit\u00e4t macht industrielle Lastverschiebung wirtschaftlich sinnvoll.",
            "nl": "Day-ahead-veilingen bepalen een uurprijs voor de volgende dag in de gekoppelde Europese biedzones. Die granulariteit per uur maakt industriele lastverschuiving economisch zinvol.",
            "es": "Las subastas diarias fijan un precio horario para el d\u00eda siguiente en las zonas de oferta europeas acopladas. Esa granularidad horaria hace que el desplazamiento de carga industrial tenga sentido econ\u00f3mico.",
        },
        "https://www.entsoe.eu/data/transparency-platform/",
        ("spot_price", "load_shift", "energy_cost"),
        ("market", "marche", "markt", "mercado", "price", "prix", "preis", "prijs", "precio", "spot"),
    ),
    _hit(
        "grid-carbon-intensity",
        {
            "en": "Grid carbon intensity varies hour by hour",
            "fr": "L'intensit\u00e9 carbone du r\u00e9seau varie d'heure en heure",
            "de": "Die Netz-CO2-Intensit\u00e4t schwankt st\u00fcndlich",
            "nl": "De koolstofintensiteit van het net varieert per uur",
            "es": "La intensidad de carbono de la red var\u00eda hora a hora",
        },
        {
            "en": "Published grid mix data shows carbon intensity moving by a factor of several between windy nights and low-renewable evening peaks. Shifting load toward low-intensity hours reduces reported Scope 2 emissions without changing production volume.",
            "fr": "Les donn\u00e9es publi\u00e9es de mix \u00e9lectrique montrent une intensit\u00e9 carbone variant d'un facteur plusieurs entre nuits vent\u00e9es et pointes du soir peu renouvelables. D\u00e9caler la charge vers les heures peu intenses r\u00e9duit les \u00e9missions Scope 2 sans changer le volume produit.",
            "de": "Ver\u00f6ffentlichte Strommixdaten zeigen eine CO2-Intensit\u00e4t, die zwischen windigen N\u00e4chten und erneuerbarenarmen Abendspitzen um ein Mehrfaches schwankt. Lastverschiebung in intensit\u00e4tsarme Stunden senkt die berichteten Scope-2-Emissionen ohne Produktions\u00e4nderung.",
            "nl": "Gepubliceerde netmixdata tonen een koolstofintensiteit die tussen winderige nachten en hernieuwbaar-arme avondpieken een veelvoud verschilt. Last verschuiven naar uren met lage intensiteit verlaagt de gerapporteerde Scope 2-uitstoot zonder productieverlies.",
            "es": "Los datos publicados del mix el\u00e9ctrico muestran una intensidad de carbono que var\u00eda varias veces entre noches ventosas y picos vespertinos con poca renovable. Desplazar carga a horas de baja intensidad reduce las emisiones de alcance 2 sin cambiar el volumen producido.",
        },
        "https://www.eea.europa.eu/en/analysis/indicators/greenhouse-gas-emission-intensity-of-1",
        ("carbon_intensity", "emissions", "load_shift"),
        ("intensity", "intensite", "intensitat", "intensiteit", "intensidad", "grid", "reseau", "netz", "net", "red"),
    ),
    _hit(
        "eaf-decarbonisation",
        {
            "en": "Electric arc furnace routes shift emissions toward electricity",
            "fr": "La fili\u00e8re four \u00e9lectrique d\u00e9place les \u00e9missions vers l'\u00e9lectricit\u00e9",
            "de": "Die Elektrolichtbogenofen-Route verlagert Emissionen zum Strom",
            "nl": "De vlamboogovenroute verschuift uitstoot naar elektriciteit",
            "es": "La ruta de horno de arco el\u00e9ctrico desplaza las emisiones a la electricidad",
        },
        {
            "en": "Scrap-based electric arc furnace production has a markedly lower direct CO2 footprint than the blast-furnace route, but it moves a large share of the footprint into purchased electricity, which is why grid carbon intensity and energy scheduling become compliance levers.",
            "fr": "La production au four \u00e0 arc \u00e9lectrique \u00e0 base de ferraille a une empreinte CO2 directe nettement plus faible que la fili\u00e8re haut fourneau, mais elle transf\u00e8re une part importante de l'empreinte vers l'\u00e9lectricit\u00e9 achet\u00e9e : l'intensit\u00e9 carbone du r\u00e9seau et la planification \u00e9nerg\u00e9tique deviennent des leviers de conformit\u00e9.",
            "de": "Schrottbasierte Elektrolichtbogenofen-Produktion hat einen deutlich geringeren direkten CO2-Fu\u00dfabdruck als die Hochofenroute, verlagert aber einen gro\u00dfen Anteil in den bezogenen Strom. Netz-CO2-Intensit\u00e4t und Energieplanung werden damit zu Compliance-Hebeln.",
            "nl": "Schrootgebaseerde vlamboogovenproductie heeft een duidelijk lagere directe CO2-voetafdruk dan de hoogovenroute, maar verschuift een groot deel naar ingekochte elektriciteit. Netkoolstofintensiteit en energieplanning worden zo compliance-hefbomen.",
            "es": "La producci\u00f3n en horno de arco el\u00e9ctrico a partir de chatarra tiene una huella directa de CO2 mucho menor que la ruta de alto horno, pero traslada gran parte de la huella a la electricidad comprada: la intensidad de carbono de la red y la planificaci\u00f3n energ\u00e9tica pasan a ser palancas de cumplimiento.",
        },
        "https://www.iea.org/energy-system/industry/steel",
        ("emissions", "energy_cost", "throughput", "ets_exposure"),
        ("eaf", "arc", "scrap", "ferraille", "schrott", "schroot", "chatarra", "decarbonisation", "decarbonization"),
    ),
    _hit(
        "predictive-maintenance-practice",
        {
            "en": "Condition-based maintenance relies on uncertainty bands, not point dates",
            "fr": "La maintenance conditionnelle repose sur des intervalles d'incertitude, pas sur une date unique",
            "de": "Zustandsorientierte Instandhaltung nutzt Unsicherheitsb\u00e4nder, keine Punktdaten",
            "nl": "Toestandsafhankelijk onderhoud steunt op onzekerheidsbanden, niet op \u00e9\u00e9n datum",
            "es": "El mantenimiento basado en condici\u00f3n se apoya en bandas de incertidumbre, no en una fecha \u00fanica",
        },
        {
            "en": "Established reliability practice is to plan against a confidence band (for example P10-P90) rather than a single predicted failure date, and to require a corroborating signal before acting. That is why NovaSteel shows a band and a corroboration check next to every remaining-life figure.",
            "fr": "La pratique \u00e9tablie en fiabilit\u00e9 consiste \u00e0 planifier sur un intervalle de confiance (par exemple P10-P90) plut\u00f4t que sur une date de d\u00e9faillance unique, et \u00e0 exiger un signal corroborant avant d'agir. C'est pourquoi NovaSteel affiche un intervalle et une v\u00e9rification \u00e0 c\u00f4t\u00e9 de chaque dur\u00e9e de vie restante.",
            "de": "Etablierte Zuverl\u00e4ssigkeitspraxis plant gegen ein Konfidenzband (etwa P10-P90) statt gegen ein einzelnes Ausfalldatum und verlangt ein best\u00e4tigendes Signal vor dem Handeln. Deshalb zeigt NovaSteel neben jeder Restlebensdauer ein Band und eine Gegenpr\u00fcfung.",
            "nl": "Gangbare betrouwbaarheidspraktijk plant tegen een betrouwbaarheidsband (bijvoorbeeld P10-P90) in plaats van \u00e9\u00e9n voorspelde storingsdatum, en vraagt een bevestigend signaal voor actie. Daarom toont NovaSteel bij elke resterende levensduur een band en een controle.",
            "es": "La pr\u00e1ctica establecida de fiabilidad planifica contra una banda de confianza (por ejemplo P10-P90) en lugar de una \u00fanica fecha de fallo, y exige una se\u00f1al corroborante antes de actuar. Por eso NovaSteel muestra una banda y una comprobaci\u00f3n junto a cada vida \u00fatil restante.",
        },
        "https://www.iso.org/standard/64046.html",
        ("lining_risk", "remaining_useful_life", "maintenance_window", "thermal_signature"),
        ("maintenance", "predictive", "predictif", "vorausschauend", "voorspellend", "predictivo", "reliability", "fiabilite"),
    ),
    _hit(
        "spc-standard",
        {
            "en": "Control charts are the standard tool for separating signal from noise",
            "fr": "Les cartes de contr\u00f4le sont l'outil standard pour distinguer signal et bruit",
            "de": "Regelkarten sind das Standardwerkzeug zur Trennung von Signal und Rauschen",
            "nl": "Regelkaarten zijn het standaardgereedschap om signaal van ruis te scheiden",
            "es": "Los gr\u00e1ficos de control son la herramienta est\u00e1ndar para separar se\u00f1al de ruido",
        },
        {
            "en": "Statistical process control uses control limits derived from the process itself, so an operator reacts to genuine special-cause variation rather than to normal scatter. Capability indices then express whether the process fits inside the specification.",
            "fr": "La ma\u00eetrise statistique des proc\u00e9d\u00e9s utilise des limites d\u00e9riv\u00e9es du proc\u00e9d\u00e9 lui-m\u00eame : l'op\u00e9rateur r\u00e9agit \u00e0 une variation de cause sp\u00e9ciale r\u00e9elle et non \u00e0 la dispersion normale. Les indices de capabilit\u00e9 indiquent ensuite si le proc\u00e9d\u00e9 tient dans la sp\u00e9cification.",
            "de": "Die statistische Prozesslenkung nutzt aus dem Prozess selbst abgeleitete Eingriffsgrenzen, sodass Bediener auf echte spezielle Ursachen und nicht auf normale Streuung reagieren. Prozessf\u00e4higkeitsindizes zeigen dann, ob der Prozess in die Spezifikation passt.",
            "nl": "Statistische procesbeheersing gebruikt regelgrenzen die uit het proces zelf volgen, zodat een operator reageert op echte bijzondere oorzaken en niet op normale spreiding. Capabiliteitsindices tonen vervolgens of het proces binnen de specificatie past.",
            "es": "El control estad\u00edstico de procesos usa l\u00edmites derivados del propio proceso, de modo que el operador reacciona a variaci\u00f3n por causa especial real y no a la dispersi\u00f3n normal. Los \u00edndices de capacidad indican luego si el proceso cabe en la especificaci\u00f3n.",
        },
        "https://www.iso.org/standard/75362.html",
        ("spc", "defect", "yield", "genealogy"),
        ("spc", "control", "chart", "cpk", "sigma", "capability"),
    ),
    _hit(
        "fabric-capacity-billing",
        {
            "en": "Microsoft Fabric capacity is billed while it is running",
            "fr": "La capacit\u00e9 Microsoft Fabric est factur\u00e9e tant qu'elle fonctionne",
            "de": "Microsoft Fabric-Kapazit\u00e4t wird w\u00e4hrend des Betriebs berechnet",
            "nl": "Microsoft Fabric-capaciteit wordt gefactureerd zolang die draait",
            "es": "La capacidad de Microsoft Fabric se factura mientras est\u00e1 en marcha",
        },
        {
            "en": "A Fabric F-SKU capacity is charged for the time it is active and can be paused and resumed, which is why a demo environment pauses it outside working hours and starts it on demand from the portal.",
            "fr": "Une capacit\u00e9 Fabric F-SKU est factur\u00e9e sur son temps d'activit\u00e9 et peut \u00eatre suspendue puis reprise : c'est pourquoi un environnement de d\u00e9monstration la suspend hors heures ouvr\u00e9es et la d\u00e9marre \u00e0 la demande depuis le portail.",
            "de": "Eine Fabric-F-SKU-Kapazit\u00e4t wird f\u00fcr ihre aktive Zeit berechnet und kann pausiert und fortgesetzt werden. Deshalb pausiert eine Demoumgebung sie au\u00dferhalb der Arbeitszeit und startet sie bei Bedarf aus dem Portal.",
            "nl": "Een Fabric F-SKU-capaciteit wordt gefactureerd voor de tijd dat die actief is en kan gepauzeerd en hervat worden. Daarom pauzeert een demo-omgeving die buiten kantooruren en start men die op verzoek vanuit de portal.",
            "es": "Una capacidad Fabric F-SKU se cobra por el tiempo que est\u00e1 activa y puede pausarse y reanudarse; por eso un entorno de demostraci\u00f3n la pausa fuera del horario laboral y la inicia bajo demanda desde el portal.",
        },
        "https://learn.microsoft.com/fabric/enterprise/pause-resume",
        ("capacity", "cost_telemetry", "pipeline_job"),
        ("fabric", "capacity", "sku", "billing", "facturation", "abrechnung", "facturatie", "facturacion", "pause"),
    ),
)


def _matches(concept_keys: set[str], tokens: set[str], entry) -> int:
    _, _, _, _, concepts, triggers = entry
    score = 0
    score += 10 * len(concept_keys & set(concepts))
    score += 3 * len(tokens & set(triggers))
    return score


def online_context(
    resolved: ResolvedContext,
    question: str,
    language: str = DEFAULT_LANGUAGE,
    *,
    limit: int = MAX_HITS,
) -> list[OnlineHit]:
    """Return public context relevant to a resolved question.

    Ranked by overlap with the resolved concepts first and the raw question
    wording second, so "what are the latest ETS announcements" surfaces the ETS
    entries even from a screen where ETS is not the primary concept.
    """
    concept_keys = {concept.key for concept in resolved.concepts}
    tokens = tokenize(question)

    scored: list[tuple[int, OnlineHit]] = []
    for entry in _CORPUS:
        score = _matches(concept_keys, tokens, entry)
        if score <= 0:
            continue
        source_id, titles, snippets, url, concepts, triggers = entry
        scored.append(
            (
                score,
                OnlineHit(
                    source_id=source_id,
                    title=titles.get(language) or titles[DEFAULT_LANGUAGE],
                    snippet=snippets.get(language) or snippets[DEFAULT_LANGUAGE],
                    url=url,
                    concepts=frozenset(concepts),
                    triggers=frozenset(triggers),
                ),
            )
        )

    scored.sort(key=lambda row: (-row[0], row[1].source_id))
    return [hit for _, hit in scored[:limit]]
