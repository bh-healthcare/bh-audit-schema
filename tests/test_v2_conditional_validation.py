"""Direct unit tests for the conditional rules in RFC §6.

Distinct from the negative-corpus tests: these construct minimal events in
code and assert the specific rule that fires, including the §6.1
'agent-initiated OVERRIDE' interaction.
"""

import copy
import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "versions" / "2.0" / "audit_event.schema.json").read_text()
)


def _human_read():
    return {
        "schema_version": "2.0",
        "event_id": "00000000-0000-4000-8000-000000000001",
        "timestamp": "2026-06-12T14:02:11Z",
        "service": {"name": "svc"},
        "actor": {"subject_id": "user_1", "subject_type": "human"},
        "action": {"type": "READ"},
        "resource": {"type": "Patient", "id": "pat_1"},
        "outcome": {"status": "SUCCESS"},
    }


def _agent_event():
    return {
        "schema_version": "2.0",
        "event_id": "00000000-0000-4000-8000-000000000002",
        "timestamp": "2026-06-12T14:02:11Z",
        "service": {"name": "svc"},
        "actor": {"subject_id": "agent_cred", "subject_type": "agent"},
        "delegation": {
            "acting": {
                "subject_id": "agent_inst",
                "subject_type": "agent",
                "agent": {"interface": "mcp"},
            },
            "authorizing": {"subject_id": "user_1", "subject_type": "human"},
            "delegation_type": "supervised",
            "agent_session_id": "agsess_1",
        },
        "action": {"type": "READ"},
        "resource": {"type": "Patient", "id": "pat_1"},
        "outcome": {"status": "SUCCESS"},
    }


def _override_event():
    return {
        "schema_version": "2.0",
        "event_id": "00000000-0000-4000-8000-000000000003",
        "timestamp": "2026-06-12T14:02:11Z",
        "service": {"name": "svc"},
        "actor": {"subject_id": "user_1", "subject_type": "human"},
        "action": {"type": "OVERRIDE", "name": "cancel"},
        "resource": {"type": "AgentSession", "id": "agsess_1"},
        "outcome": {"status": "SUCCESS"},
    }


def _validate(event):
    jsonschema.validate(
        instance=event, schema=SCHEMA,
        format_checker=jsonschema.FormatChecker(),
    )


class TestRule1AgentRequiresDelegation:
    def test_human_actor_without_delegation_ok(self):
        _validate(_human_read())

    def test_agent_actor_with_delegation_ok(self):
        _validate(_agent_event())

    def test_agent_actor_without_delegation_fails(self):
        event = _agent_event()
        del event["delegation"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)


class TestRule2ChainDepthPairing:
    def test_depth_1_no_parent_ok(self):
        event = _agent_event()
        event["delegation"]["chain_depth"] = 1
        _validate(event)

    def test_depth_2_with_parent_ok(self):
        event = _agent_event()
        event["delegation"]["chain_depth"] = 2
        event["delegation"]["parent_agent_session_id"] = "agsess_parent"
        _validate(event)

    def test_depth_2_without_parent_fails(self):
        event = _agent_event()
        event["delegation"]["chain_depth"] = 2
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)

    def test_parent_with_depth_1_fails(self):
        event = _agent_event()
        event["delegation"]["chain_depth"] = 1
        event["delegation"]["parent_agent_session_id"] = "agsess_parent"
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)

    def test_parent_without_chain_depth_fails(self):
        event = _agent_event()
        event["delegation"]["parent_agent_session_id"] = "agsess_parent"
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)


class TestRule3Override:
    def test_human_override_of_agent_session_ok(self):
        _validate(_override_event())

    def test_override_by_agent_fails(self):
        event = _override_event()
        event["actor"]["subject_type"] = "agent"
        event["delegation"] = _agent_event()["delegation"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)

    def test_override_with_delegation_present_fails(self):
        event = _override_event()
        event["delegation"] = _agent_event()["delegation"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)

    def test_override_wrong_resource_type_fails(self):
        event = _override_event()
        event["resource"]["type"] = "Patient"
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)

    def test_override_missing_resource_id_fails(self):
        event = _override_event()
        del event["resource"]["id"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)


class TestSection61AgentOverrideUnsatisfiable:
    """RFC §6.1: agent actor + OVERRIDE triggers both rules 1 and 3.
    Whichever fires first is fine; the combined effect is correct (unsatisfiable)."""

    def test_agent_override_fails(self):
        event = _override_event()
        event["actor"]["subject_type"] = "agent"
        # no delegation -> rule 1 fires; OVERRIDE by agent -> rule 3 fires
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)
