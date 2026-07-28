"""Foundry IQ knowledge bases — the layer that lets an agent answer from procedures.

A knowledge base is an Azure AI Search data-plane object that sits *above* one or
more knowledge sources. When queried it plans the query (decomposing a compound
question into sub-queries), runs keyword, vector and hybrid retrieval in parallel
across its sources, reranks semantically, enforces the caller's permissions and
returns cited, synthesized results.

Why this matters here: the alternative would be to give the hosted procedure agent a
hand-rolled retrieval tool and re-implement query planning and citation assembly in
Python. Foundry IQ does that server-side and — crucially — exposes the knowledge base
over MCP, so attaching it to a Foundry agent is a connection plus one tool
declaration rather than a tool-calling loop we own and have to keep grounded.

Two sources are supported:

``procedures``
    An index knowledge source over the ``novasteel-procedures`` index built by
    :mod:`knowledge_orchestrator.search_store`. Always present.

``web`` (optional, off by default)
    A *web* knowledge source, which is the concrete form of the "Web IQ" capability:
    live Bing results retrieved inside the same agentic-retrieval pipeline, optionally
    restricted to an allow-list of domains. This is what backs the Copilot's "Online
    search" toggle when ``ONLINE_SEARCH_MODE=web_iq``.

    **Compliance caveat, deliberately loud:** the web knowledge source is a First
    Party Consumption Service. The Microsoft DPA does not apply to it, query content
    leaves the Azure compliance and geographic boundary, and it is unavailable in
    sovereign clouds. For a plant-floor assistant whose questions can themselves
    reveal process detail, that is a real disclosure. So it is opt-in, defaults to
    off, and is domain-restricted to public standards bodies unless overridden.

Everything here is data-plane: none of it can be expressed in Bicep, which is why
``infra/bicep/modules/ai-search.bicep`` only outputs the agreed names.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

ENV_KNOWLEDGE_BASE = "FOUNDRY_KNOWLEDGE_BASE"
ENV_ONLINE_SEARCH_MODE = "ONLINE_SEARCH_MODE"
ENV_WEB_ALLOWED_DOMAINS = "ONLINE_SEARCH_ALLOWED_DOMAINS"

DEFAULT_KNOWLEDGE_BASE = "novasteel-procedures-kb"
PROCEDURE_SOURCE_NAME = "novasteel-procedures-source"
WEB_SOURCE_NAME = "novasteel-web-source"

# Answer synthesis and LLM query planning are preview-only; the GA surface
# (2026-04-01) supports extractive retrieval only. We want synthesis, so the preview
# api-version is pinned explicitly rather than relying on the SDK default.
KNOWLEDGE_API_VERSION = "2026-05-01-preview"

# Restricting the web source to standards and regulatory bodies keeps "Online search"
# useful for the thing operators actually ask about — what a norm requires — while
# keeping the query surface narrow. Overridable via ONLINE_SEARCH_ALLOWED_DOMAINS.
DEFAULT_ALLOWED_DOMAINS: tuple[str, ...] = (
    "iso.org",
    "cen.eu",
    "cenelec.eu",
    "osha.gov",
    "echa.europa.eu",
    "eur-lex.europa.eu",
)

ONLINE_MODE_WEB_IQ = "web_iq"
ONLINE_MODE_WEB_SEARCH = "web_search"
ONLINE_MODE_OFFLINE = "offline"


@dataclass(frozen=True)
class KnowledgeBaseConfig:
    """Resolved configuration for the Foundry IQ knowledge base."""

    search_endpoint: str
    index_name: str
    knowledge_base_name: str = DEFAULT_KNOWLEDGE_BASE
    foundry_endpoint: str = ""
    chat_deployment: str = ""
    embed_deployment: str = ""
    include_web_source: bool = False
    allowed_domains: tuple[str, ...] = DEFAULT_ALLOWED_DOMAINS

    @property
    def mcp_url(self) -> str:
        """MCP endpoint an agent connects to in order to query this knowledge base."""
        return (
            f"{self.search_endpoint}/knowledgebases/{self.knowledge_base_name}"
            f"/mcp?api-version={KNOWLEDGE_API_VERSION}"
        )


def online_search_mode() -> str:
    """Return the configured online-search backend, defaulting to ``offline``.

    Anything unrecognised is treated as ``offline``. Failing closed matters here:
    a typo in the environment must not silently start routing operator questions to
    a public web index.
    """
    mode = os.environ.get(ENV_ONLINE_SEARCH_MODE, "").strip().lower()
    if mode in (ONLINE_MODE_WEB_IQ, ONLINE_MODE_WEB_SEARCH, ONLINE_MODE_OFFLINE):
        return mode
    if mode:
        logger.warning(
            "Unrecognised %s=%r — defaulting to 'offline'. Online search stays on the "
            "curated in-repo corpus.",
            ENV_ONLINE_SEARCH_MODE,
            mode,
        )
    return ONLINE_MODE_OFFLINE


def _allowed_domains_from_env() -> tuple[str, ...]:
    raw = os.environ.get(ENV_WEB_ALLOWED_DOMAINS, "").strip()
    if not raw:
        return DEFAULT_ALLOWED_DOMAINS
    domains = tuple(d.strip() for d in raw.split(",") if d.strip())
    return domains or DEFAULT_ALLOWED_DOMAINS


def knowledge_base_config_from_env() -> Optional[KnowledgeBaseConfig]:
    """Build a :class:`KnowledgeBaseConfig` from the environment, or ``None``."""
    from .search_store import (
        DEFAULT_INDEX_NAME,
        ENV_EMBED_DEPLOYMENT,
        ENV_FOUNDRY_ENDPOINT,
        ENV_SEARCH_ENDPOINT,
        ENV_SEARCH_INDEX,
    )

    endpoint = os.environ.get(ENV_SEARCH_ENDPOINT, "").strip().rstrip("/")
    if not endpoint:
        return None

    return KnowledgeBaseConfig(
        search_endpoint=endpoint,
        index_name=os.environ.get(ENV_SEARCH_INDEX, "").strip() or DEFAULT_INDEX_NAME,
        knowledge_base_name=(
            os.environ.get(ENV_KNOWLEDGE_BASE, "").strip() or DEFAULT_KNOWLEDGE_BASE
        ),
        foundry_endpoint=os.environ.get(ENV_FOUNDRY_ENDPOINT, "").strip().rstrip("/"),
        chat_deployment=os.environ.get("FOUNDRY_CHAT_DEPLOYMENT", "").strip(),
        embed_deployment=os.environ.get(ENV_EMBED_DEPLOYMENT, "").strip(),
        include_web_source=online_search_mode() == ONLINE_MODE_WEB_IQ,
        allowed_domains=_allowed_domains_from_env(),
    )


@dataclass
class KnowledgeBaseProvisionResult:
    """What :meth:`FoundryIQProvisioner.provision` actually managed to create."""

    knowledge_base_name: str
    sources: list[str] = field(default_factory=list)
    web_source_enabled: bool = False
    provisioned: bool = False
    reason: str = ""


class FoundryIQProvisioner:
    """Creates the knowledge sources and knowledge base at the Search data plane.

    Idempotent: every call is a create-or-update, so running it on each cold start is
    safe and keeps the knowledge base in step with configuration changes.
    """

    def __init__(self, config: KnowledgeBaseConfig, credential: Any = None) -> None:
        self._config = config
        self._credential = credential

    def _get_credential(self) -> Any:
        if self._credential is None:
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()
        return self._credential

    def _index_client(self) -> Any:
        from azure.search.documents.indexes import SearchIndexClient

        return SearchIndexClient(
            endpoint=self._config.search_endpoint,
            credential=self._get_credential(),
            api_version=KNOWLEDGE_API_VERSION,
        )

    def _completion_model(self) -> Any:
        """Model the knowledge base uses for query planning and answer synthesis."""
        from azure.search.documents.indexes.models import (
            AzureOpenAIVectorizerParameters,
            KnowledgeBaseAzureOpenAIModel,
        )

        return KnowledgeBaseAzureOpenAIModel(
            azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                resource_url=self._config.foundry_endpoint,
                deployment_name=self._config.chat_deployment,
                model_name=self._config.chat_deployment,
            )
        )

    def _create_procedure_source(self, client: Any) -> str:
        from azure.search.documents.indexes.models import (
            SearchIndexKnowledgeSource,
            SearchIndexKnowledgeSourceParameters,
        )

        source = SearchIndexKnowledgeSource(
            name=PROCEDURE_SOURCE_NAME,
            description=(
                "Approved NovaSteel maintenance procedures. Every answer drawn from "
                "this source must cite the procedure id it came from."
            ),
            search_index_parameters=SearchIndexKnowledgeSourceParameters(
                search_index_name=self._config.index_name,
                source_data_select=(
                    "chunk_id,procedure_id,procedure_title,section,text"
                ),
            ),
        )
        client.create_or_update_knowledge_source(knowledge_source=source)
        return PROCEDURE_SOURCE_NAME

    def _create_web_source(self, client: Any) -> str:
        from azure.search.documents.indexes.models import (
            WebKnowledgeSource,
            WebKnowledgeSourceDomainConfiguration,
            WebKnowledgeSourceParameters,
        )

        source = WebKnowledgeSource(
            name=WEB_SOURCE_NAME,
            description=(
                "Public standards and regulatory context. NOT plant knowledge — "
                "answers grounded here must never be presented as approved procedure."
            ),
            web_parameters=WebKnowledgeSourceParameters(
                domains=WebKnowledgeSourceDomainConfiguration(
                    allowed_domains=list(self._config.allowed_domains)
                )
            ),
        )
        client.create_or_update_knowledge_source(knowledge_source=source)
        logger.warning(
            "Web knowledge source '%s' enabled (domains: %s). Queries sent to it leave "
            "the Azure compliance and geographic boundary and are not covered by the "
            "Microsoft DPA.",
            WEB_SOURCE_NAME,
            ", ".join(self._config.allowed_domains),
        )
        return WEB_SOURCE_NAME

    def provision(self) -> KnowledgeBaseProvisionResult:
        """Create/update the knowledge sources and the knowledge base over them."""
        from azure.search.documents.indexes.models import (
            KnowledgeBase,
            KnowledgeSourceReference,
        )

        result = KnowledgeBaseProvisionResult(
            knowledge_base_name=self._config.knowledge_base_name
        )
        client = self._index_client()
        try:
            source_names = [self._create_procedure_source(client)]
            if self._config.include_web_source:
                source_names.append(self._create_web_source(client))
                result.web_source_enabled = True

            knowledge_base = KnowledgeBase(
                name=self._config.knowledge_base_name,
                description=(
                    "NovaSteel procedure knowledge. Answers are grounded in approved "
                    "procedures and always carry citations."
                ),
                knowledge_sources=[
                    KnowledgeSourceReference(name=name) for name in source_names
                ],
                completion_model=self._completion_model(),
            )
            client.create_or_update_knowledge_base(knowledge_base=knowledge_base)

            result.sources = source_names
            result.provisioned = True
            logger.info(
                "Foundry IQ knowledge base '%s' ready over sources: %s",
                self._config.knowledge_base_name,
                ", ".join(source_names),
            )
        finally:
            client.close()

        return result


def provision_knowledge_base(
    config: Optional[KnowledgeBaseConfig] = None,
) -> KnowledgeBaseProvisionResult:
    """Provision the knowledge base if configured, degrading gracefully otherwise.

    Like every other Azure path in this service, an unavailable SDK or an unreachable
    Search service is a degraded mode with a logged reason, not a startup failure —
    the orchestrator falls back to querying the procedure store directly.
    """
    config = config or knowledge_base_config_from_env()
    if config is None:
        return KnowledgeBaseProvisionResult(
            knowledge_base_name=DEFAULT_KNOWLEDGE_BASE,
            reason="AI Search is not configured",
        )
    if not config.foundry_endpoint or not config.chat_deployment:
        return KnowledgeBaseProvisionResult(
            knowledge_base_name=config.knowledge_base_name,
            reason=(
                "knowledge base needs a chat deployment for query planning and answer "
                "synthesis; FOUNDRY_ENDPOINT/FOUNDRY_CHAT_DEPLOYMENT are not set"
            ),
        )

    try:
        return FoundryIQProvisioner(config).provision()
    except ImportError as exc:
        logger.warning(
            "azure-search-documents not available (%s) — Foundry IQ knowledge base not "
            "provisioned; the procedure agent will fall back to direct retrieval.",
            exc,
        )
        return KnowledgeBaseProvisionResult(
            knowledge_base_name=config.knowledge_base_name,
            reason=f"SDK unavailable: {exc}",
        )
    except Exception as exc:
        logger.warning(
            "Failed to provision the Foundry IQ knowledge base (%s) — the procedure "
            "agent will fall back to direct retrieval.",
            exc,
        )
        return KnowledgeBaseProvisionResult(
            knowledge_base_name=config.knowledge_base_name,
            reason=str(exc),
        )
