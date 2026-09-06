"""Verify the v2.1 schema publishes the `AttributionLevel` $def and the
`attribution` object shape from RFC 0003 §4, and carries the v2.0 $defs
forward unchanged."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema" / "versions" / "2.1" / "audit_event.schema.json"
V20_SCHEMA_PATH = REPO_ROOT / "schema" / "versions" / "2.0" / "audit_event.schema.json"


def _load():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


class TestAttributionLevelDef:
    def test_enum_is_the_four_rfc_levels(self):
        defn = _load()["$defs"]["AttributionLevel"]
        assert defn["type"] == "string"
        assert set(defn["enum"]) == {"verified", "bound", "asserted", "unattributed"}

    def test_no_unknown_level(self):
        """RFC 0003 §4.2: a producer that cannot say how it established an
        attribution is describing `asserted`; there is no `unknown`."""
        assert "unknown" not in _load()["$defs"]["AttributionLevel"]["enum"]


class TestAttributionObject:
    def test_level_required_method_optional(self):
        attr = _load()["properties"]["attribution"]
        assert attr["required"] == ["level"]
        assert set(attr["properties"]) == {"level", "method"}

    def test_level_refs_attribution_level(self):
        prop = _load()["properties"]["attribution"]["properties"]["level"]
        assert prop.get("$ref") == "#/$defs/AttributionLevel"

    def test_method_is_bounded_open_string(self):
        prop = _load()["properties"]["attribution"]["properties"]["method"]
        assert prop["type"] == "string"
        assert prop["minLength"] == 1
        assert prop["maxLength"] == 64
        assert "enum" not in prop

    def test_additional_properties_false(self):
        assert _load()["properties"]["attribution"]["additionalProperties"] is False

    def test_attribution_is_not_a_root_required_field(self):
        """RFC 0003 §12.1: `attribution` is required only when `delegation`
        is present, which keeps the release a minor bump."""
        assert "attribution" not in _load()["required"]


class TestSchemaVersion:
    def test_schema_version_const(self):
        assert _load()["properties"]["schema_version"]["const"] == "2.1"

    def test_id_is_v21(self):
        assert _load()["$id"].endswith("/2.1/audit_event.schema.json")


class TestInheritedDefsUnchanged:
    def test_v2_0_defs_carried_forward_verbatim(self):
        with open(V20_SCHEMA_PATH) as f:
            v20_defs = json.load(f)["$defs"]
        v21_defs = _load()["$defs"]
        for name, defn in v20_defs.items():
            assert v21_defs[name] == defn, name
