"""Supplementary offline web-search corpus for the Copilot demo.

When no live search backend is configured (env var COPILOT_SEARCH_ENDPOINT is
absent), the BFF adapter searches this corpus lexically. Results are clearly
labelled as a *synthetic offline corpus* so the demo stays honest.

This supplements the upstream knowledge-orchestrator corpus that is tightly
coupled to screen concepts. The items here are dated, news-style entries that
the upstream corpus does not carry: regulatory announcements, market moves,
and recent steel-industry developments with specific dates.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Final

_TOKEN_RE = re.compile(r"[a-z0-9]+")

CORPUS_LABEL = "offline demo corpus"
RETRIEVAL_DATE = "2026-07-27"


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(_fold(text)))


@dataclass(frozen=True)
class OfflineWebResult:
    source_id: str
    title: str
    snippet: str
    url: str
    published: str
    triggers: frozenset[str]


_CORPUS: Final[tuple[OfflineWebResult, ...]] = (
    OfflineWebResult(
        source_id="eu-ets-revision-2026",
        title="European Commission releases latest EU ETS revision proposal",
        snippet=(
            "The European Commission released its latest EU ETS revision proposal "
            "on July 17, 2026, tightening the annual cap reduction factor to 4.4% "
            "and extending coverage to maritime transport and smaller industrial "
            "installations from 2028."
        ),
        url="https://climate.ec.europa.eu/eu-action/eu-emissions-trading-system-eu-ets/revision-eu-ets_en",
        published="2026-07-17",
        triggers=frozenset({
            "ets", "revision", "proposal", "commission", "latest", "2026",
            "cap", "reduction", "maritime", "announcement", "release",
            "released", "eu",
        }),
    ),
    OfflineWebResult(
        source_id="cbam-transitional-reporting-2026",
        title="CBAM transitional reporting: first compliance deadline passed",
        snippet=(
            "The first CBAM transitional reporting period ended on 31 January 2026. "
            "Steel importers had to submit embedded emissions data for Q3-Q4 2025. "
            "The European Commission reported a 93% compliance rate among registered "
            "declarants."
        ),
        url="https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en",
        published="2026-02-15",
        triggers=frozenset({
            "cbam", "border", "adjustment", "reporting", "compliance",
            "import", "embedded", "emissions", "transition", "steel",
        }),
    ),
    OfflineWebResult(
        source_id="eua-price-july-2026",
        title="EU carbon allowance price reaches EUR 87 in July 2026",
        snippet=(
            "EUA futures (Dec-26 contract) settled at EUR 87.40 on ICE Endex on "
            "15 July 2026, up 12% year-on-year, driven by tighter supply from the "
            "accelerated cap reduction and increased hedging demand from aviation "
            "and maritime entrants."
        ),
        url="https://www.theice.com/products/197/EUA-Futures",
        published="2026-07-15",
        triggers=frozenset({
            "eua", "price", "carbon", "allowance", "cost", "market",
            "ets", "87", "futures", "ice",
        }),
    ),
    OfflineWebResult(
        source_id="green-steel-h2-pilot-2026",
        title="ArcelorMittal starts hydrogen-DRI pilot at Hamburg",
        snippet=(
            "ArcelorMittal inaugurated its 100 kt/y hydrogen-based direct reduced "
            "iron (H2-DRI) demonstration plant in Hamburg on 3 June 2026, aiming to "
            "prove that green hydrogen can replace natural gas in the DRI shaft "
            "furnace at industrial scale."
        ),
        url="https://corporate.arcelormittal.com/climate-action",
        published="2026-06-03",
        triggers=frozenset({
            "hydrogen", "h2", "dri", "green", "steel", "arcelormittal",
            "hamburg", "pilot", "decarbonisation", "decarbonization",
        }),
    ),
    OfflineWebResult(
        source_id="eu-electricity-market-reform-2026",
        title="EU electricity market reform enters into force",
        snippet=(
            "Regulation (EU) 2025/1222 on EU electricity market design entered into "
            "force on 1 March 2026, introducing long-term Contracts for Difference "
            "(CfDs) for new low-carbon generation and strengthening rules on demand "
            "response and industrial flexibility."
        ),
        url="https://energy.ec.europa.eu/topics/markets-and-consumers/market-legislation_en",
        published="2026-03-01",
        triggers=frozenset({
            "electricity", "market", "reform", "cfd", "demand", "response",
            "flexibility", "industrial", "energy", "load",
        }),
    ),
    OfflineWebResult(
        source_id="worldsteel-production-june-2026",
        title="World crude steel production up 1.8% in June 2026",
        snippet=(
            "The World Steel Association reported global crude steel production of "
            "163.2 Mt in June 2026, up 1.8% year-on-year. EU-27 output rose 0.4% "
            "while China declined 0.6%, reflecting continued capacity rationalisation."
        ),
        url="https://worldsteel.org/steel-topics/statistics/",
        published="2026-07-22",
        triggers=frozenset({
            "production", "steel", "output", "worldsteel", "crude",
            "global", "statistics", "capacity", "world",
        }),
    ),
    OfflineWebResult(
        source_id="iso-14064-update-2026",
        title="ISO 14064-1:2026 published with Scope 3 refinements",
        snippet=(
            "ISO published the 2026 edition of 14064-1 (greenhouse gas accounting "
            "at organisation level) on 20 May 2026, with improved guidance on "
            "Scope 3 category boundaries and requiring disclosure of estimation "
            "uncertainty for reported figures."
        ),
        url="https://www.iso.org/standard/83307.html",
        published="2026-05-20",
        triggers=frozenset({
            "iso", "14064", "scope", "ghg", "greenhouse", "emissions",
            "accounting", "uncertainty", "reporting",
        }),
    ),
    OfflineWebResult(
        source_id="refractory-recycling-circular-2026",
        title="New EU circular economy guidance covers refractory recycling",
        snippet=(
            "The European Commission's updated Circular Economy Package guidance "
            "(June 2026) explicitly includes spent refractory materials from steel "
            "and cement plants, setting a 30% recycled-content target for magnesia-"
            "carbon bricks by 2030."
        ),
        url="https://environment.ec.europa.eu/strategy/circular-economy-action-plan_en",
        published="2026-06-10",
        triggers=frozenset({
            "refractory", "recycling", "circular", "magnesia", "brick",
            "lining", "spent", "waste",
        }),
    ),
)


def search_offline_corpus(
    query: str,
    *,
    limit: int = 3,
) -> list[OfflineWebResult]:
    """Lexical search over the offline corpus.

    Returns results ranked by trigger overlap with the query tokens.
    """
    tokens = _tokenize(query)
    if not tokens:
        return []

    scored: list[tuple[int, OfflineWebResult]] = []
    for item in _CORPUS:
        overlap = len(tokens & item.triggers)
        if overlap > 0:
            scored.append((overlap, item))

    scored.sort(key=lambda pair: (-pair[0], pair[1].source_id))
    return [item for _, item in scored[:limit]]
