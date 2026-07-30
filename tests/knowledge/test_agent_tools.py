"""Tests for the tool schema catalogue and the per-request tool registry.

The registry is a security boundary: it decides whether a name the model emitted
becomes a call into a NovaSteel calculation. These tests pin the deny-by-default
behaviour and the strict-schema shape that Foundry validates against.
"""

from __future__ import annotations

import json

import pytest

from knowledge_orchestrator.agent_tools import (
    MAX_TOOL_ARGUMENTS_CHARS,
    TOOL_CATALOGUE,
    ToolError,
    ToolRegistry,
    ToolSpec,
    UnknownToolError,
    tool_spec,
)

# The rest of this suite is deliberately runnable with nothing but the standard
# library and pytest (see the service README), which is how CI runs it. Only the
# handful of assertions that build a real SDK object need the optional `azure`
# extra, so they skip rather than fail where it is absent.
#
# This is a guarded import rather than `importlib.util.find_spec`, because
# find_spec imports the parent package and so raises ModuleNotFoundError -- at
# collection time, failing the whole module -- when `azure.ai` is missing.
try:  # pragma: no cover - depends on which extras are installed
    from azure.ai.projects.models import FunctionTool as _FunctionTool
except Exception:  # pragma: no cover
    _FunctionTool = None

requires_sdk = pytest.mark.skipif(
    _FunctionTool is None,
    reason="azure-ai-projects is an optional extra; the SDK object cannot be built without it",
)


def test_catalogue_is_keyed_by_tool_name():
    for name, spec in TOOL_CATALOGUE.items():
        assert spec.name == name


def test_every_schema_is_strict_compatible():
    """Foundry rejects a strict function tool whose schema is not closed.

    ``strict=True`` requires ``additionalProperties: false`` and every property
    listed as required. Getting this wrong fails at agent-creation time in Azure,
    which is a slow and confusing place to find out.
    """
    for spec in TOOL_CATALOGUE.values():
        schema = spec.parameters
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"]), (
            f"{spec.name}: strict schemas cannot have optional properties"
        )


def test_every_tool_documents_itself():
    """The description is the only thing telling the model when to call a tool."""
    for spec in TOOL_CATALOGUE.values():
        assert len(spec.description) > 40
        for prop in spec.parameters["properties"].values():
            assert prop.get("description")


def test_tool_spec_lookup_rejects_unknown_names():
    with pytest.raises(UnknownToolError):
        tool_spec("not_a_tool")


def test_registry_denies_unregistered_tools():
    """Deny by default: an empty registry answers nothing, it does not fall through."""
    registry = ToolRegistry()
    with pytest.raises(UnknownToolError):
        registry.execute("simulate_energy_dispatch", "{}")


def test_registry_denies_a_catalogued_tool_it_was_not_given():
    """Being in the catalogue is not the same as being available to this agent.

    The maintenance advisor's registry must not answer an energy dispatch call just
    because the schema exists somewhere in the codebase.
    """
    registry = ToolRegistry().register("lining_rul_forecast", lambda args: {"ok": True})
    with pytest.raises(UnknownToolError):
        registry.execute("simulate_energy_dispatch", "{}")


def test_registry_executes_a_registered_tool_with_parsed_arguments():
    seen = {}

    def _impl(arguments):
        seen.update(arguments)
        return {"answer": 42}

    registry = ToolRegistry().register("lining_rul_forecast", _impl)
    result = registry.execute("lining_rul_forecast", json.dumps({"assetId": "A-1"}))
    assert result == {"answer": 42}
    assert seen == {"assetId": "A-1"}


def test_registry_accepts_arguments_already_parsed():
    registry = ToolRegistry().register("lining_rul_forecast", lambda args: dict(args))
    assert registry.execute("lining_rul_forecast", {"assetId": "A-2"}) == {
        "assetId": "A-2"
    }


def test_registry_refuses_oversized_arguments():
    """Tool arguments are model output, and model output can be driven."""
    registry = ToolRegistry().register("lining_rul_forecast", lambda args: {})
    oversized = json.dumps({"assetId": "x" * (MAX_TOOL_ARGUMENTS_CHARS + 10)})
    with pytest.raises(ToolError):
        registry.execute("lining_rul_forecast", oversized)


def test_registry_refuses_malformed_json():
    registry = ToolRegistry().register("lining_rul_forecast", lambda args: {})
    with pytest.raises(ToolError):
        registry.execute("lining_rul_forecast", "{not json")


def test_registry_refuses_non_object_arguments():
    """A JSON array parses fine but is not a set of named arguments."""
    registry = ToolRegistry().register("lining_rul_forecast", lambda args: {})
    with pytest.raises(ToolError):
        registry.execute("lining_rul_forecast", "[1, 2, 3]")


def test_specs_reflect_only_registered_tools():
    registry = ToolRegistry().register("lining_rul_forecast", lambda args: {})
    assert [spec.name for spec in registry.specs] == ["lining_rul_forecast"]


def test_registering_an_uncatalogued_name_fails_fast():
    """A tool with no schema could never be offered to an agent, so registering one
    is a programming error worth surfacing at wiring time."""
    with pytest.raises(UnknownToolError):
        ToolRegistry().register("invented_tool", lambda args: {})


@requires_sdk
def test_to_sdk_tool_is_strict():
    spec = ToolSpec(
        name="lining_rul_forecast",
        description=TOOL_CATALOGUE["lining_rul_forecast"].description,
        parameters=TOOL_CATALOGUE["lining_rul_forecast"].parameters,
    )
    sdk_tool = spec.to_sdk_tool()
    payload = getattr(sdk_tool, "function", sdk_tool)
    assert getattr(payload, "strict", None) is True or (
        isinstance(payload, dict) and payload.get("strict") is True
    )
