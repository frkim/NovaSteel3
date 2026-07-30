"""Addressing the Foundry data plane under the *new project model*.

Microsoft Foundry has two generations of resource shape, and they are addressed
differently:

* **Classic** — an Azure OpenAI / Cognitive Services account reached on
  ``https://<name>.openai.azure.com`` or ``https://<name>.cognitiveservices.azure.com``,
  with inference under ``/openai/deployments/<deployment>/…`` and a mandatory dated
  ``api-version`` query parameter that has to be bumped every time a feature ships.
  Hub-based ("classic") projects sit on ``Microsoft.MachineLearningServices/workspaces``
  and are reached through a connection string.
* **New project model** — a Foundry resource
  (``Microsoft.CognitiveServices/accounts`` of kind ``AIServices`` with
  ``allowProjectManagement``) hosting ``accounts/projects`` children. Everything is
  served from ``https://<name>.services.ai.azure.com``: the project endpoint
  (``/api/projects/<project>``, used by ``AIProjectClient`` in
  :mod:`knowledge_orchestrator.agent_service`) and the versionless OpenAI **v1**
  inference route (``/openai/v1/…``).

NovaSteel is on the new model end to end — see ``infra/bicep/modules/foundry-speech.bicep``
and ``modules/foundry-agents.bicep``. This module is the single place that encodes
what that means for outbound HTTP, so the raw-``requests`` call sites
(:mod:`~knowledge_orchestrator.adapters.azure_foundry`,
:mod:`~knowledge_orchestrator.retrieval`,
:mod:`~knowledge_orchestrator.copilot.agents`) cannot drift back to the classic
route one file at a time.

Two things it normalises:

``normalize_endpoint``
    Rewrites a classic host to its Foundry equivalent. Deployments, developer
    ``.env`` files and older parameter sets still carry
    ``https://<name>.cognitiveservices.azure.com``; silently accepting that value
    and then calling ``/openai/v1`` against it would fail at runtime, and refusing
    it would break every existing configuration. Rewriting is the only option that
    does neither.

``token_scope``
    The Foundry audience is ``https://ai.azure.com/.default``, not the classic
    ``https://cognitiveservices.azure.com/.default``. This is the same scope
    ``AIProjectClient`` acquires, so a single managed identity token audience
    covers agents *and* inference. Role assignments are unchanged: data-plane
    access is still granted by *Cognitive Services OpenAI User* on the account
    (``infra/bicep/main.bicep``).

Speech and Content Safety are separate Cognitive Services accounts, not Foundry
resources, so they keep the classic scope and are deliberately out of scope here.
"""

from __future__ import annotations

import logging
import os
from urllib.parse import urlsplit, urlunsplit

logger = logging.getLogger(__name__)

ENV_TOKEN_SCOPE = "FOUNDRY_TOKEN_SCOPE"

#: Entra audience for the Foundry data plane (project endpoint and OpenAI v1 route).
FOUNDRY_SCOPE = "https://ai.azure.com/.default"

#: Audience of the classic Azure OpenAI / Cognitive Services data plane.
LEGACY_COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"

#: Host suffix the Foundry project model is served from.
FOUNDRY_HOST_SUFFIX = ".services.ai.azure.com"

#: Host suffixes that identify a classic endpoint for the same underlying account.
LEGACY_HOST_SUFFIXES = (".openai.azure.com", ".cognitiveservices.azure.com")

#: Versionless OpenAI-compatible inference route of the Foundry project model.
OPENAI_V1_PREFIX = "openai/v1"


def normalize_endpoint(endpoint: str) -> str:
    """Return *endpoint* as a Foundry-model account endpoint, without a trailing slash.

    A classic host for the same account (``<name>.openai.azure.com`` or
    ``<name>.cognitiveservices.azure.com``) is rewritten to
    ``<name>.services.ai.azure.com``. Anything else — including an empty string, a
    project endpoint, or a private/sovereign host we do not recognise — is returned
    unchanged apart from trailing-slash trimming, because guessing at an unknown
    host is worse than passing it through.
    """
    cleaned = (endpoint or "").strip().rstrip("/")
    if not cleaned:
        return ""

    parts = urlsplit(cleaned)
    if not parts.netloc:
        return cleaned

    host = parts.netloc
    for suffix in LEGACY_HOST_SUFFIXES:
        if host.lower().endswith(suffix):
            account = host[: -len(suffix)]
            rewritten = urlunsplit(
                (parts.scheme, f"{account}{FOUNDRY_HOST_SUFFIX}", parts.path, "", "")
            ).rstrip("/")
            logger.info(
                "Rewrote classic Foundry endpoint %s to the project-model endpoint %s",
                cleaned,
                rewritten,
            )
            return rewritten

    return cleaned


def openai_v1_url(endpoint: str, path: str) -> str:
    """Build a Foundry OpenAI **v1** URL, e.g. ``.../openai/v1/chat/completions``.

    No ``api-version``: the v1 route is versionless by design, which is the whole
    point of moving off the classic ``?api-version=<date>`` deployments route.
    """
    base = normalize_endpoint(endpoint)
    if not base:
        raise ValueError("A Foundry endpoint is required to build an inference URL")
    return f"{base}/{OPENAI_V1_PREFIX}/{path.lstrip('/')}"


def token_scope() -> str:
    """Entra scope for Foundry data-plane calls.

    Overridable through ``FOUNDRY_TOKEN_SCOPE`` for sovereign clouds, where the
    audience differs from the public-cloud ``https://ai.azure.com/.default``.
    """
    return os.environ.get(ENV_TOKEN_SCOPE, "").strip() or FOUNDRY_SCOPE
