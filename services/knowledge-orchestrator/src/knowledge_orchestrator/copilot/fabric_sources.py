"""Fabric artefacts, query steps and card structure shared by the answer packs.

Why this module exists
----------------------
Two card packs cite the same capacity: the screen chips
(``fabric_answer_data``) and the per-persona questions
(``fabric_persona_data``). Both need the same artefact names, the same
``FabricDataset``/``FabricCard`` shape and the same query helpers, so those live
here and neither pack imports the other.

What a query step is for
------------------------
Every predefined question is answered by the Fabric data agent
``da-novasteelv3``, and the panel now shows *how*: each cited dataset carries the
statement the agent issued against it, the row count it came back with, and how
long it took. That turns the answer from an assertion into a retrieval an
evaluator can follow -- lakehouse SQL endpoint, Eventhouse KQL, or a GQL
traversal of the ontology -- which is exactly the interaction a live
``da-novasteelv3`` session would produce.

The statements are the deterministic stand-in described in
``docs/architecture/copilot-fabric-data-agent.md`` option A: real query text
against the real gold and KQL schemas, resolved from a curated result so the
demo is reproducible, works offline, and never depends on an F2 being resumed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

WORKSPACE: Final[str] = "NovaSteelV3-Demo"
LAKEHOUSE: Final[str] = "lh_novasteelv3_core"
KQL_DATABASE: Final[str] = "kql-ns-operations"
ONTOLOGY: Final[str] = "onto_novasteelv3"
DATA_AGENT: Final[str] = "da-novasteelv3"

SQL_ENGINE: Final[str] = "T-SQL"
KQL_ENGINE: Final[str] = "KQL"
GQL_ENGINE: Final[str] = "GQL"


@dataclass(frozen=True)
class FabricDataset:
    """One Fabric artefact the data agent queried, and the step it ran there."""

    source_id: str
    title: str
    snippet: str
    engine: str = SQL_ENGINE
    statement: str = ""
    rows: int = 0
    elapsed_ms: int = 0


@dataclass(frozen=True)
class FabricCard:
    """One predefined question and the answer the platform serves for it.

    A card is addressed either by its position among a screen's chips
    (``section`` plus ``index``) or by the verbatim ``prompts`` of a persona
    question, which the panel sends as free text.
    """

    card_id: str
    datasets: tuple[FabricDataset, ...]
    body: dict[str, str]
    section: str = ""
    index: int = -1
    prompts: tuple[str, ...] = ()

    @property
    def total_rows(self) -> int:
        return sum(dataset.rows for dataset in self.datasets)

    @property
    def total_elapsed_ms(self) -> int:
        return sum(dataset.elapsed_ms for dataset in self.datasets)


def gold(table: str, snippet: str, statement: str, rows: int, elapsed_ms: int) -> FabricDataset:
    """A gold Delta table read through the lakehouse SQL analytics endpoint."""
    return FabricDataset(
        source_id=f"fabric:{LAKEHOUSE}.{table}",
        title=f"{LAKEHOUSE}.{table}",
        snippet=snippet,
        engine=SQL_ENGINE,
        statement=statement,
        rows=rows,
        elapsed_ms=elapsed_ms,
    )


def kql(table: str, snippet: str, statement: str, rows: int, elapsed_ms: int) -> FabricDataset:
    """An Eventhouse table read with KQL, outside the gold history cut-off."""
    return FabricDataset(
        source_id=f"fabric:{KQL_DATABASE}.{table}",
        title=f"{KQL_DATABASE}.{table}",
        snippet=snippet,
        engine=KQL_ENGINE,
        statement=statement,
        rows=rows,
        elapsed_ms=elapsed_ms,
    )


def graph(snippet: str, statement: str, rows: int, elapsed_ms: int) -> FabricDataset:
    """A traversal of the ontology GraphModel."""
    return FabricDataset(
        source_id=f"fabric:{ONTOLOGY}",
        title=f"{ONTOLOGY} (GQL)",
        snippet=snippet,
        engine=GQL_ENGINE,
        statement=statement,
        rows=rows,
        elapsed_ms=elapsed_ms,
    )


def bodies(card_id: str, packs: dict[str, dict[str, str]]) -> dict[str, str]:
    """Collect every translation that exists for one card."""
    return {
        language: pack[card_id]
        for language, pack in packs.items()
        if card_id in pack and pack[card_id].strip()
    }
