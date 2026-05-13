"""Verify v1.1 schema publishes enums as named $defs referenced via $ref."""

import json
from pathlib import Path

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schema"
    / "versions"
    / "1.1"
    / "audit_event.schema.json"
)
ROOT_PATH = (
    Path(__file__).resolve().parent.parent / "schema" / "audit_event.schema.json"
)


def _load():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


class TestDefsExist:
    def test_defs_key_present(self):
        assert "$defs" in _load()

    def test_action_type_def(self):
        defn = _load()["$defs"]["ActionType"]
        assert defn["type"] == "string"
        assert set(defn["enum"]) == {
            "READ",
            "CREATE",
            "UPDATE",
            "DELETE",
            "EXPORT",
            "LOGIN",
            "LOGOUT",
            "PRINT",
            "OTHER",
        }

    def test_outcome_status_def(self):
        defn = _load()["$defs"]["OutcomeStatus"]
        assert defn["type"] == "string"
        assert set(defn["enum"]) == {"SUCCESS", "FAILURE", "DENIED"}

    def test_data_classification_def(self):
        defn = _load()["$defs"]["DataClassification"]
        assert defn["type"] == "string"
        assert set(defn["enum"]) == {"PHI", "PII", "NONE", "UNKNOWN"}


class TestRefsUsed:
    def test_action_type_ref(self):
        prop = _load()["properties"]["action"]["properties"]["type"]
        assert prop.get("$ref") == "#/$defs/ActionType"

    def test_outcome_status_ref(self):
        prop = _load()["properties"]["outcome"]["properties"]["status"]
        assert prop.get("$ref") == "#/$defs/OutcomeStatus"

    def test_data_classification_ref(self):
        prop = _load()["properties"]["action"]["properties"]["data_classification"]
        assert prop.get("$ref") == "#/$defs/DataClassification"


class TestFileSync:
    def test_root_matches_versioned(self):
        with open(ROOT_PATH) as f:
            root = f.read()
        with open(SCHEMA_PATH) as f:
            versioned = f.read()
        assert root == versioned, (
            "Root schema must be byte-for-byte copy of latest versioned schema"
        )
