"""The Fabric capacity SKU allow-list is declared in four independent places, in three
different languages. If they drift, the portal offers an operator a SKU that Azure Policy
will deny at the ARM boundary — a failure that only surfaces in cloud mode, during a demo.

This test pins them together:

* ``infra/policy/definitions/restrict-fabric-capacity-sku.json`` — the ``allowedSkus``
  parameter default, which is what the deny policy actually enforces.
* ``infra/bicep/main.bicep`` — the ``@allowed`` decorator on ``fabricSkuName``.
* ``services/bff-api/src/bff_api/capacity.py`` — ``SCALABLE_SKUS``, which the BFF
  validates every ``POST /v1/platform/capacity/sku-requests`` body against.
* ``apps/portal-shell/Services/CapacityState.cs`` — ``DefaultSkuOptions``, the fallback
  the Blazor capacity dialog renders when the BFF status payload omits ``skuOptions``.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from conftest import BICEP_DIR, REPO_ROOT, load_json, read_text

EXPECTED_SKUS = ["F2", "F4", "F8"]


def _policy_allowed_skus() -> list[str]:
    definition = load_json(
        REPO_ROOT / "infra" / "policy" / "definitions" / "restrict-fabric-capacity-sku.json"
    )
    return list(definition["properties"]["parameters"]["allowedSkus"]["defaultValue"])


def _bicep_allowed_skus() -> list[str]:
    text = read_text(BICEP_DIR / "main.bicep")
    match = re.search(r"@allowed\(\s*\[([^\]]*)\]\s*\)\s*param fabricSkuName\b", text)
    assert match, "could not find the @allowed decorator on param fabricSkuName in main.bicep"
    return re.findall(r"'([^']+)'", match.group(1))


def _bff_scalable_skus() -> list[str]:
    source = read_text(
        REPO_ROOT / "services" / "bff-api" / "src" / "bff_api" / "capacity.py"
    )
    module = ast.parse(source)
    for node in module.body:
        targets = getattr(node, "targets", []) or ([node.target] if hasattr(node, "target") else [])
        for target in targets:
            if isinstance(target, ast.Name) and target.id == "SCALABLE_SKUS":
                return list(ast.literal_eval(node.value))
    raise AssertionError("SCALABLE_SKUS is not defined in bff_api/capacity.py")


def _shell_default_sku_options() -> list[str]:
    text = read_text(
        REPO_ROOT / "apps" / "portal-shell" / "Services" / "CapacityState.cs"
    )
    match = re.search(r"DefaultSkuOptions\s*=\s*(?:new[^\[]*)?\[([^\]]*)\]", text)
    assert match, "could not find DefaultSkuOptions in CapacityState.cs"
    return re.findall(r'"([^"]+)"', match.group(1))


def test_policy_allows_exactly_the_documented_demo_skus() -> None:
    assert _policy_allowed_skus() == EXPECTED_SKUS


def test_every_layer_agrees_on_the_capacity_sku_allow_list() -> None:
    layers = {
        "policy restrict-fabric-capacity-sku.json allowedSkus": _policy_allowed_skus(),
        "main.bicep @allowed fabricSkuName": _bicep_allowed_skus(),
        "bff_api.capacity.SCALABLE_SKUS": _bff_scalable_skus(),
        "portal-shell CapacityState.DefaultSkuOptions": _shell_default_sku_options(),
    }

    mismatched = {
        name: skus for name, skus in layers.items() if sorted(skus) != sorted(EXPECTED_SKUS)
    }
    assert not mismatched, (
        "the Fabric capacity SKU allow-list has drifted between layers; the portal would "
        f"offer a SKU that Azure Policy denies. Expected {EXPECTED_SKUS}, got: {mismatched}"
    )
