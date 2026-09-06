"""Translator tests for the RFC 0003 §9 changes to scripts/translate_to_fhir.py.

Two behaviours are pinned. The attribution extensions are emitted whether or
not a delegation block exists, and an `unattributed` event gets its own agent
slice instead of falling through to `direct`, which would assert that the
agent acted directly as the requestor.

R5 validation against fhir.resources is opt-in: the test is skipped if the
dependency is not installed.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _has_fhir_resources():
    try:
        return importlib.util.find_spec("fhir.resources") is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from translate_to_fhir import translate  # noqa: E402

POSITIVE_DIR = REPO_ROOT / "examples" / "2.1"
POSITIVES = sorted(POSITIVE_DIR.glob("*.json"))
V20_POSITIVES = sorted((REPO_ROOT / "examples" / "2.0").glob("*.json"))
UNATTRIBUTED = [
    p for p in POSITIVES
    if json.loads(p.read_text()).get("attribution", {}).get("level") == "unattributed"
]


def _roles(ae):
    return [a["type"]["coding"][0]["code"] for a in ae["agent"]]


def _extensions(ae):
    return {e["url"].rsplit("/", 1)[-1]: e for e in ae.get("extension", [])}


@pytest.mark.parametrize("path", POSITIVES, ids=lambda p: p.name)
def test_translator_produces_auditevent(path):
    event = json.loads(path.read_text())
    ae = translate(event)

    assert ae["resourceType"] == "AuditEvent"
    assert ae["id"] == event["event_id"]
    assert ae["recorded"] == event["timestamp"]
    assert ae["agent"], "AuditEvent must have at least one agent"

    level = event.get("attribution", {}).get("level")
    if event.get("delegation"):
        assert _roles(ae) == [
            "authenticating-identity",
            "acting-identity",
            "authorizing-identity",
        ], _roles(ae)
    elif level == "unattributed":
        assert _roles(ae) == ["unattributed"], _roles(ae)
    else:
        assert _roles(ae) == ["direct"], _roles(ae)


@pytest.mark.parametrize("path", V20_POSITIVES + POSITIVES,
                         ids=lambda p: f"{p.parent.name}/{p.name}")
def test_meta_profile_canonical_carries_the_schema_version(path):
    """The 2.0 and 2.1 profiles differ (inv-6, inv-7, the unattributed slice,
    the G10 extensions), and a v2.0 delegated resource does not satisfy the
    2.1 invariants. Each resource must therefore claim the profile of the
    schema version it came from, and only that one."""
    event = json.loads(path.read_text())
    version = event["schema_version"]
    ae = translate(event)
    assert ae["meta"]["profile"] == [
        f"https://bh-healthcare.github.io/bh-audit-schema/fhir/{version}"
        f"/StructureDefinition/bh-audit-event"
    ]


def test_corpus_has_both_unattributed_shapes():
    assert {p.name for p in UNATTRIBUTED} == {
        "agent_denied_unattributed.json",
        "agent_fail_open_unattributed.json",
    }


@pytest.mark.parametrize("path", UNATTRIBUTED, ids=lambda p: p.name)
def test_unattributed_event_is_not_a_direct_requestor(path):
    """RFC 0003 §9: an unattributed event has no delegation block and must
    not take the `direct` branch."""
    ae = translate(json.loads(path.read_text()))
    assert "direct" not in _roles(ae)
    assert not any(a.get("requestor") is True for a in ae["agent"])


@pytest.mark.parametrize("path", UNATTRIBUTED, ids=lambda p: p.name)
def test_unattributed_slice_names_the_authenticating_credential(path):
    event = json.loads(path.read_text())
    ae = translate(event)
    assert len(ae["agent"]) == 1
    agent = ae["agent"][0]
    assert agent["type"]["coding"][0]["code"] == "unattributed"
    assert agent["who"]["identifier"]["value"] == event["actor"]["subject_id"]
    assert agent["requestor"] is False


@pytest.mark.parametrize("path", UNATTRIBUTED, ids=lambda p: p.name)
def test_unattributed_event_keeps_its_attribution_extension(path):
    """RFC 0003 §9: the extension gate must not depend on a delegation
    block, or the level is silently dropped from the R5 output."""
    ext = _extensions(translate(json.loads(path.read_text())))
    assert ext["attribution-level"]["valueCode"] == "unattributed"


@pytest.mark.parametrize("path", POSITIVES, ids=lambda p: p.name)
def test_attribution_round_trips_through_extensions(path):
    event = json.loads(path.read_text())
    ext = _extensions(translate(event))
    attribution = event.get("attribution")
    if attribution is None:
        assert "attribution-level" not in ext
        assert "attribution-method" not in ext
        return
    assert ext["attribution-level"]["valueCode"] == attribution["level"]
    if "method" in attribution:
        assert ext["attribution-method"]["valueString"] == attribution["method"]
    else:
        assert "attribution-method" not in ext


def test_delegation_extensions_survive_the_widened_gate():
    path = POSITIVE_DIR / "sub_agent_depth2_export.json"
    ext = _extensions(translate(json.loads(path.read_text())))
    assert {"delegation-type", "agent-session-id", "chain-depth",
            "parent-agent-session-id", "attribution-level",
            "attribution-method"} <= set(ext)


def test_event_without_either_block_carries_no_extensions():
    """A direct human action still looks like a conventional AuditEvent."""
    path = POSITIVE_DIR / "human_direct_read.json"
    assert "extension" not in translate(json.loads(path.read_text()))


def test_client_ip_lands_on_the_unattributed_slice():
    """The unattributed slice is the credential that connected, so it is the
    relevant slice for agent.network[x]."""
    event = json.loads((POSITIVE_DIR / "agent_denied_unattributed.json").read_text())
    event["http"] = {"client_ip": "203.0.113.42"}
    ae = translate(event)
    assert ae["agent"][0]["networkString"] == "203.0.113.42"


@pytest.mark.skipif(
    not _has_fhir_resources(),
    reason="fhir.resources not installed; install with: "
           "pip install 'fhir.resources>=8.0.0'",
)
@pytest.mark.parametrize("path", POSITIVES, ids=lambda p: p.name)
def test_translator_output_validates_as_r5_auditevent(path):
    from fhir.resources.auditevent import AuditEvent
    event = json.loads(path.read_text())
    AuditEvent.model_validate(translate(event))
