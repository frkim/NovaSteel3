"""Azure AI Content Safety adapter (production).

Authenticates with ``DefaultAzureCredential`` (managed identity in Azure,
developer identity locally) following the same pattern as ``azure_foundry.py``
and ``azure_speech.py``: no API keys in source, scope
``https://cognitiveservices.azure.com/.default``, endpoint from an environment
variable.

Calls:
  * ``POST {endpoint}/contentsafety/text:analyze`` — hate/selfharm/sexual/violence
  * ``POST {endpoint}/contentsafety/text:shieldPrompt`` — jailbreak / prompt injection

Failure modes (all fall back to ``LocalHeuristicContentSafety``):
  * Missing ``AZURE_CONTENT_SAFETY_ENDPOINT`` environment variable
  * Auth / token-acquisition failure
  * Network error or non-2xx HTTP response
  * Unparseable / missing JSON body → **fail closed** (return max severity 7 for
    all categories so ambiguity always blocks rather than passes)

HTTP transport: ``urllib.request`` from the standard library (consistent with the
spec requirement; no additional HTTP package needed beyond what is already present).
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional

from ..content_safety import (
    DEFAULT_BLOCK_THRESHOLD,
    LocalHeuristicContentSafety,
    SafetyCategory,
)

logger = logging.getLogger(__name__)

# Azure AI Content Safety REST API version (pinned for stability).
CONTENT_SAFETY_API_VERSION: str = "2024-09-01"

# Entra token scope for Azure Cognitive Services (shared with azure_speech.py).
CONTENT_SAFETY_SCOPE: str = "https://cognitiveservices.azure.com/.default"

# Environment variable for the Content Safety endpoint.
ENV_CONTENT_SAFETY_ENDPOINT: str = "AZURE_CONTENT_SAFETY_ENDPOINT"

# Sentinel severity returned when a response cannot be parsed (fail-closed).
_FAIL_CLOSED_SEVERITY: int = 7

# Map from Azure category strings to SafetyCategory values.
_AZURE_CATEGORY_MAP: dict[str, str] = {
    "Hate": "hate",
    "SelfHarm": "selfharm",
    "Sexual": "sexual",
    "Violence": "violence",
}


class AzureContentSafetyProvider:
    """Production adapter: Azure AI Content Safety + Prompt Shield for jailbreak.

    ``name`` is a mutable instance attribute that reflects which backend was
    actually used for the most recent ``analyze()`` call, allowing the
    :class:`SafetyVerdict` ``providerUsed`` field to be accurate when the
    provider falls back to local heuristics.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_version: str = CONTENT_SAFETY_API_VERSION,
        credential=None,
        fallback: Optional[LocalHeuristicContentSafety] = None,
    ) -> None:
        self._endpoint = (
            endpoint or os.environ.get(ENV_CONTENT_SAFETY_ENDPOINT, "")
        ).rstrip("/")
        self._api_version = api_version
        self._credential = credential
        self._fallback = fallback or LocalHeuristicContentSafety()
        # Mutable: updated on each analyze() call to reflect actual provider used.
        self.name: str = "AzureContentSafetyProvider"

    def _get_token(self) -> str:  # pragma: no cover — requires azure-identity
        credential = self._credential or _default_credential()
        return credential.get_token(CONTENT_SAFETY_SCOPE).token

    def analyze(self, text: str) -> dict[str, int]:
        """Return severity scores (0–7) per category.

        Calls the Azure AI Content Safety API when the endpoint is configured;
        falls back to :class:`LocalHeuristicContentSafety` on any failure.
        On an unparseable body the method fails closed (all categories → 7).
        """
        if not self._endpoint:
            logger.warning(
                "%s not set; falling back to LocalHeuristicContentSafety",
                ENV_CONTENT_SAFETY_ENDPOINT,
            )
            self.name = f"AzureContentSafetyProvider[fallback:{self._fallback.name}]"
            return self._fallback.analyze(text)

        try:
            result = self._azure_analyze(text)
            self.name = "AzureContentSafetyProvider"
            return result
        except Exception as exc:
            logger.warning(
                "Azure Content Safety call failed (%s); falling back to local heuristics",
                exc,
            )
            self.name = f"AzureContentSafetyProvider[fallback:{self._fallback.name}]"
            return self._fallback.analyze(text)

    def _azure_analyze(self, text: str) -> dict[str, int]:
        """Call analyzeText + shieldPrompt and merge the results."""
        token = self._get_token()
        scores: dict[str, int] = {cat.value: 0 for cat in SafetyCategory}

        # --- analyzeText (hate / selfharm / sexual / violence) ---------------
        analyze_url = (
            f"{self._endpoint}/contentsafety/text:analyze"
            f"?api-version={self._api_version}"
        )
        analyze_body = json.dumps(
            {
                "text": text,
                "categories": ["Hate", "SelfHarm", "Sexual", "Violence"],
                "outputType": "FourSeverityLevels",
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            analyze_url,
            data=analyze_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
        except urllib.error.URLError as err:
            raise RuntimeError(f"analyzeText network error: {err}") from err

        try:
            result = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "Azure Content Safety returned unparseable body; failing closed"
            )
            # Fail closed: ambiguity → treat as blocked at maximum severity.
            return {cat.value: _FAIL_CLOSED_SEVERITY for cat in SafetyCategory}

        for item in result.get("categoriesAnalysis", []):
            cat = _AZURE_CATEGORY_MAP.get(item.get("category", ""))
            if cat is not None:
                scores[cat] = max(scores.get(cat, 0), int(item.get("severity", 0)))

        # --- shieldPrompt (jailbreak / prompt injection) ----------------------
        shield_url = (
            f"{self._endpoint}/contentsafety/text:shieldPrompt"
            f"?api-version={self._api_version}"
        )
        shield_body = json.dumps(
            {"userPrompt": text, "documents": []}
        ).encode("utf-8")

        shield_req = urllib.request.Request(
            shield_url,
            data=shield_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(shield_req, timeout=15) as shield_resp:
                shield_raw = shield_resp.read()
            shield_result = json.loads(shield_raw)
            if shield_result.get("userPromptAnalysis", {}).get("attackDetected", False):
                scores["jailbreak"] = _FAIL_CLOSED_SEVERITY - 1  # 6 = severe
                scores["prompt_injection"] = _FAIL_CLOSED_SEVERITY - 1
        except (urllib.error.URLError, json.JSONDecodeError, ValueError) as shield_err:
            logger.warning(
                "shieldPrompt call failed (%s); supplementing with local jailbreak check",
                shield_err,
            )
            # Fall back to local heuristics for jailbreak only; don't discard analyzeText.
            local_scores = self._fallback.analyze(text)
            scores["jailbreak"] = max(
                scores.get("jailbreak", 0), local_scores.get("jailbreak", 0)
            )
            scores["prompt_injection"] = max(
                scores.get("prompt_injection", 0),
                local_scores.get("prompt_injection", 0),
            )

        return scores


def _default_credential():  # pragma: no cover — requires azure-identity
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()
