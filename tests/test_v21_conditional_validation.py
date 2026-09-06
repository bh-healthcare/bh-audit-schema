"""Direct unit tests for the RFC 0003 §5 conditional rules R1 to R4, the
OVERRIDE amendment, and the §6 silence table.

Distinct from the negative-corpus tests: these construct minimal events in
code and assert the specific rule that fires. Where two rules fire on the
same shape by design (R1 and R2 on `unattributed` next to a delegation
block), both are asserted.
"""

import copy
import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "versions" / "2.1" / "audit_event.schema.json").read_text()
)

DELEGATION = {
    "acting": {
        "subject_id": "agent_inst",
        "subject_type": "agent",
        "agent": {"interface": "mcp"},
    },
    "authorizing": {"subject_id": "user_1", "subject_type": "human"},
    "delegation_type": "supervised",
    "agent_session_id": "agsess_1",
}


def _human_read():
    return {
        "schema_version": "2.1",
        "event_id": "00000000-0000-4000-8000-000000000001",
        "timestamp": "2026-09-01T10:00:00Z",
        "service": {"name": "svc"},
        "actor": {"subject_id": "user_1", "subject_type": "human"},
        "action": {"type": "READ"},
        "resource": {"type": "Patient", "id": "pat_1"},
        "outcome": {"status": "SUCCESS"},
    }


def _agent_event():
    return {
        "schema_version": "2.1",
        "event_id": "00000000-0000-4000-8000-000000000002",
        "timestamp": "2026-09-01T10:00:00Z",
        "service": {"name": "svc"},
        "actor": {"subject_id": "agent_cred", "subject_type": "agent"},
        "attribution": {"level": "verified", "method": "id_jag"},
        "delegation": copy.deepcopy(DELEGATION),
        "action": {"type": "READ"},
        "resource": {"type": "Patient", "id": "pat_1"},
        "outcome": {"status": "SUCCESS"},
    }


def _unattributed_denial():
    return {
        "schema_version": "2.1",
        "event_id": "00000000-0000-4000-8000-000000000003",
        "timestamp": "2026-09-01T10:00:00Z",
        "service": {"name": "svc"},
        "actor": {"subject_id": "agent_cred", "subject_type": "agent"},
        "attribution": {"level": "unattributed"},
        "action": {"type": "READ"},
        "resource": {"type": "Patient", "id": "pat_1"},
        "outcome": {"status": "DENIED", "error_type": "AttributionRequired"},
    }


def _override_event():
    return {
        "schema_version": "2.1",
        "event_id": "00000000-0000-4000-8000-000000000004",
        "timestamp": "2026-09-01T10:00:00Z",
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


def _failing_keywords(event):
    """Every JSON Schema keyword that rejects the event, so a test can assert
    which rule fired instead of relying on the validator's choice of which
    error to raise first."""
    validator = jsonschema.Draft202012Validator(
        SCHEMA, format_checker=jsonschema.FormatChecker(),
    )
    return {error.validator for error in validator.iter_errors(event)}


class TestR1DelegationRequiresAttribution:
    @pytest.mark.parametrize("level", ["verified", "bound", "asserted"])
    def test_delegation_with_each_level_ok(self, level):
        event = _agent_event()
        event["attribution"] = {"level": level}
        _validate(event)

    def test_delegation_without_attribution_fails(self):
        event = _agent_event()
        del event["attribution"]
        with pytest.raises(jsonschema.ValidationError,
                           match="'attribution' is a required property"):
            _validate(event)

    def test_human_actor_with_delegation_still_needs_attribution(self):
        """R1 keys on the delegation block, not on the actor type."""
        event = _agent_event()
        event["actor"] = {"subject_id": "user_1", "subject_type": "human"}
        del event["attribution"]
        with pytest.raises(jsonschema.ValidationError,
                           match="'attribution' is a required property"):
            _validate(event)


class TestR2UnattributedForbidsDelegation:
    def test_unattributed_without_delegation_ok(self):
        _validate(_unattributed_denial())

    def test_unattributed_with_delegation_fails_on_r1_and_r2(self):
        event = _agent_event()
        event["attribution"] = {"level": "unattributed"}
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)
        keywords = _failing_keywords(event)
        assert "not" in keywords, keywords
        assert "enum" in keywords, keywords


class TestR3LevelRequiresDelegation:
    @pytest.mark.parametrize("level", ["verified", "bound", "asserted"])
    def test_level_without_delegation_fails(self, level):
        event = _human_read()
        event["attribution"] = {"level": level}
        with pytest.raises(jsonschema.ValidationError,
                           match="'delegation' is a required property"):
            _validate(event)


class TestR4AgentActorMustBeExplained:
    def test_agent_with_delegation_ok(self):
        _validate(_agent_event())

    def test_agent_with_unattributed_ok(self):
        _validate(_unattributed_denial())

    def test_agent_with_neither_block_fails(self):
        """Silence remains invalid: this is the v2.0 negative case
        01_agent_actor_without_delegation re-marked to 2.1."""
        event = _unattributed_denial()
        del event["attribution"]
        with pytest.raises(jsonschema.ValidationError) as exc:
            _validate(event)
        assert exc.value.validator == "anyOf"

    def test_agent_with_verified_but_no_delegation_fails(self):
        """R3 and R4 both fire: the level demands a delegation block, and the
        agent actor is explained by neither block."""
        event = _unattributed_denial()
        event["attribution"] = {"level": "verified"}
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)
        assert {"required", "anyOf"} <= _failing_keywords(event)

    def test_fail_open_success_is_expressible(self):
        """RFC 0003 §3.3: a successful agent call with no authorizing human."""
        event = _unattributed_denial()
        event["outcome"] = {"status": "SUCCESS"}
        event["attribution"] = {"level": "unattributed", "method": "fail_open"}
        _validate(event)


class TestOverrideAmendment:
    def test_human_override_ok(self):
        _validate(_override_event())

    def test_override_with_attribution_fails(self):
        event = _override_event()
        event["attribution"] = {"level": "unattributed"}
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)
        assert _failing_keywords(event) == {"not"}

    def test_override_with_delegation_still_fails(self):
        """The v2.0 prohibition on delegation is carried forward."""
        event = _override_event()
        event["delegation"] = copy.deepcopy(DELEGATION)
        event["attribution"] = {"level": "verified"}
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)


class TestSilenceTable:
    """RFC 0003 §6: what the presence and absence of each block asserts."""

    def test_absent_absent_means_no_agent(self):
        _validate(_human_read())

    def test_absent_unattributed_means_agent_could_not_be_attributed(self):
        _validate(_unattributed_denial())

    def test_present_with_level_means_agent_and_how_strongly_known(self):
        _validate(_agent_event())

    def test_present_absent_is_invalid(self):
        event = _agent_event()
        del event["attribution"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)

    def test_absent_with_non_unattributed_level_is_invalid(self):
        event = _human_read()
        event["attribution"] = {"level": "bound"}
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)


class TestSection112ValidatorMessages:
    """RFC 0003 §11.2: on an agent actor, a level outside the enum trips R4's
    `anyOf` as well as the enum, and the validator may report either. The
    enum violation is still present in the full error set."""

    def test_level_outside_enum_on_agent_actor_is_rejected(self):
        event = _unattributed_denial()
        event["attribution"] = {"level": "probably_fine"}
        with pytest.raises(jsonschema.ValidationError):
            _validate(event)
        assert "enum" in _failing_keywords(event)
