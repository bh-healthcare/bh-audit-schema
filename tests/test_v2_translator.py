"""Translator smoke + structural tests for scripts/translate_to_fhir.py.

R5 validation against fhir.resources is opt-in: the test is skipped if the
dependency is not installed, so CI without it still benefits from the
structural assertions on the translator's output dict.
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

POSITIVES = sorted((REPO_ROOT / "examples" / "2.0").glob("*.json"))


@pytest.mark.parametrize("path", POSITIVES, ids=lambda p: p.name)
def test_translator_produces_auditevent(path):
    event = json.loads(path.read_text())
    ae = translate(event)

    assert ae["resourceType"] == "AuditEvent"
    assert ae["id"] == event["event_id"]
    assert ae["recorded"] == event["timestamp"]
    assert ae["agent"], "AuditEvent must have at least one agent"

    if event.get("delegation"):
        roles = [
            a["type"]["coding"][0]["code"] for a in ae["agent"]
        ]
        assert roles == [
            "authenticating-identity",
            "acting-identity",
            "authorizing-identity",
        ], roles
        assert len(ae["agent"]) == 3
    else:
        roles = [a["type"]["coding"][0]["code"] for a in ae["agent"]]
        assert roles == ["direct"]
        assert len(ae["agent"]) == 1


def test_override_event_has_single_direct_agent():
    path = REPO_ROOT / "examples" / "2.0" / "human_override_agent_session.json"
    ae = translate(json.loads(path.read_text()))
    assert len(ae["agent"]) == 1
    assert ae["agent"][0]["type"]["coding"][0]["code"] == "direct"


def test_client_ip_maps_to_agent_network_string():
    """FHIR companion §5: http.client_ip -> agent.network[x] on the
    relevant slice (authenticating identity for delegated events)."""
    path = REPO_ROOT / "examples" / "2.0" / "agent_ui_driving_note_write.json"
    ae = translate(json.loads(path.read_text()))
    auth = ae["agent"][0]
    assert auth["type"]["coding"][0]["code"] == "authenticating-identity"
    assert auth["networkString"] == "203.0.113.42"


def test_depth_2_event_carries_chain_extensions():
    path = REPO_ROOT / "examples" / "2.0" / "sub_agent_depth2_export.json"
    ae = translate(json.loads(path.read_text()))
    urls = [e["url"].rsplit("/", 1)[-1] for e in ae["extension"]]
    assert "chain-depth" in urls
    assert "parent-agent-session-id" in urls
    assert "delegation-type" in urls
    assert "agent-session-id" in urls


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
