"""RFC 0003 §10.1 and §11: migration of the v2.0 corpus to v2.1.

An agent-free v2.0 event migrates by updating `schema_version` alone. An
event that carries a delegation block must also add an attribution block
(R1). Every v2.0 negative example re-marked to 2.1 without further change
is still rejected, so v2.1 legalizes nothing v2.0 forbade.
"""

import copy
import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
V20_SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "versions" / "2.0" / "audit_event.schema.json").read_text()
)
V21_SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "versions" / "2.1" / "audit_event.schema.json").read_text()
)
V20_POSITIVES = sorted((REPO_ROOT / "examples" / "2.0").glob("*.json"))
V20_NEGATIVES = sorted((REPO_ROOT / "examples" / "2.0" / "negative").glob("*.json"))


def _validate(event, schema):
    jsonschema.validate(
        instance=event, schema=schema,
        format_checker=jsonschema.FormatChecker(),
    )


def _re_marked(path):
    event = json.loads(path.read_text())
    event["schema_version"] = "2.1"
    return event


@pytest.mark.parametrize("path", V20_POSITIVES, ids=lambda p: p.name)
def test_v2_0_positive_re_marked_without_attribution(path):
    """R1 bites where a delegation block exists and nowhere else."""
    event = _re_marked(path)
    if "delegation" in event:
        with pytest.raises(jsonschema.ValidationError,
                           match="'attribution' is a required property"):
            _validate(event, V21_SCHEMA)
    else:
        _validate(event, V21_SCHEMA)


def test_r1_rejects_exactly_the_delegation_bearing_events():
    """The released v2.0 corpus carries a delegation block on five of its
    seven positives, so a bare version bump is rejected on five and accepted
    on two."""
    rejected = []
    for path in V20_POSITIVES:
        try:
            _validate(_re_marked(path), V21_SCHEMA)
        except jsonschema.ValidationError:
            rejected.append(path.name)
    with_delegation = [
        p.name for p in V20_POSITIVES
        if "delegation" in json.loads(p.read_text())
    ]
    assert rejected == with_delegation
    assert len(rejected) == 5


@pytest.mark.parametrize("path", V20_POSITIVES, ids=lambda p: p.name)
def test_v2_0_positive_migrates_once_attribution_is_added(path):
    event = _re_marked(path)
    if "delegation" in event:
        event["attribution"] = {"level": "asserted"}
    _validate(event, V21_SCHEMA)


@pytest.mark.parametrize("path", V20_NEGATIVES, ids=lambda p: p.name)
def test_v2_0_negative_re_marked_is_still_rejected(path):
    with pytest.raises(jsonschema.ValidationError):
        _validate(_re_marked(path), V21_SCHEMA)


def test_verified_and_asserted_are_byte_identical_as_v2_0():
    """RFC 0003 §3.1: with `attribution` stripped and the version re-marked,
    the strongest and the weakest binding serialize to the same v2.0 event."""
    asserted = json.loads(
        (REPO_ROOT / "examples" / "2.1" / "agent_asserted_call.json").read_text()
    )
    verified = copy.deepcopy(asserted)
    verified["attribution"] = {"level": "verified", "method": "id_jag"}
    serialized = []
    for event in (verified, asserted):
        _validate(event, V21_SCHEMA)
        downgraded = copy.deepcopy(event)
        downgraded["schema_version"] = "2.0"
        del downgraded["attribution"]
        _validate(downgraded, V20_SCHEMA)
        serialized.append(json.dumps(downgraded, sort_keys=True))
    assert serialized[0] == serialized[1]
