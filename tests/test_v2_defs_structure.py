"""Verify v2.0 schema publishes named $defs and the v2 deltas vs v1.1."""

import json
from pathlib import Path

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schema" / "versions" / "2.0" / "audit_event.schema.json"
)


def _load():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


class TestDefs:
    def test_action_type_includes_override(self):
        defn = _load()["$defs"]["ActionType"]
        assert "OVERRIDE" in defn["enum"]
        assert set(defn["enum"]) == {
            "READ", "CREATE", "UPDATE", "DELETE", "EXPORT",
            "LOGIN", "LOGOUT", "PRINT", "OVERRIDE", "OTHER",
        }

    def test_subject_type_includes_agent(self):
        defn = _load()["$defs"]["SubjectType"]
        assert set(defn["enum"]) == {"human", "service", "agent"}

    def test_delegation_type_enum(self):
        defn = _load()["$defs"]["DelegationType"]
        assert set(defn["enum"]) == {"supervised", "autonomous", "scheduled"}

    def test_agent_interface_enum(self):
        defn = _load()["$defs"]["AgentInterface"]
        assert set(defn["enum"]) == {"ui_driving", "api", "mcp", "cli", "sdk"}


class TestRefsUsed:
    def test_actor_subject_type_refs_subject_type(self):
        prop = _load()["properties"]["actor"]["properties"]["subject_type"]
        assert prop.get("$ref") == "#/$defs/SubjectType"

    def test_delegation_type_refs_delegation_type(self):
        prop = _load()["properties"]["delegation"]["properties"]["delegation_type"]
        assert prop.get("$ref") == "#/$defs/DelegationType"

    def test_agent_interface_refs_agent_interface(self):
        prop = (_load()["properties"]["delegation"]["properties"]
                ["acting"]["properties"]["agent"]["properties"]["interface"])
        assert prop.get("$ref") == "#/$defs/AgentInterface"


class TestSchemaVersion:
    def test_schema_version_const(self):
        assert _load()["properties"]["schema_version"]["const"] == "2.0"

    def test_id_is_v2(self):
        assert _load()["$id"].endswith("/2.0/audit_event.schema.json")


class TestDelegationStructure:
    def test_delegation_required_fields(self):
        deleg = _load()["properties"]["delegation"]
        assert set(deleg["required"]) == {
            "acting", "authorizing", "delegation_type", "agent_session_id",
        }

    def test_acting_subject_type_const_agent(self):
        acting = _load()["properties"]["delegation"]["properties"]["acting"]
        assert acting["properties"]["subject_type"]["const"] == "agent"

    def test_authorizing_subject_type_const_human(self):
        auth = _load()["properties"]["delegation"]["properties"]["authorizing"]
        assert auth["properties"]["subject_type"]["const"] == "human"

    def test_delegation_additional_properties_false(self):
        assert _load()["properties"]["delegation"]["additionalProperties"] is False

    def test_chain_depth_bounds(self):
        prop = _load()["properties"]["delegation"]["properties"]["chain_depth"]
        assert prop["type"] == "integer"
        assert prop["minimum"] == 1
        assert prop["maximum"] == 32
