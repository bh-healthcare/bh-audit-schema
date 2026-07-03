"""RFC §13: every valid v1.1 event becomes a valid v2.0 event by updating
schema_version. Also verifies that the v1.1 subject_types (human, service)
remain valid in v2.0 without delegation.
"""

import copy
import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
V2_SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "versions" / "2.0" / "audit_event.schema.json").read_text()
)
V1_EXAMPLES = sorted((REPO_ROOT / "examples" / "1.1").glob("*.json"))


@pytest.mark.parametrize("path", V1_EXAMPLES, ids=lambda p: p.name)
def test_v1_1_event_validates_under_v2_after_version_bump(path):
    """Migrate a v1.1 fixture by mutating schema_version only; v2.0 must
    accept it. This guards the RFC §13 additive-migration claim."""
    event = json.loads(path.read_text())
    event["schema_version"] = "2.0"
    jsonschema.validate(
        instance=event, schema=V2_SCHEMA,
        format_checker=jsonschema.FormatChecker(),
    )


def test_service_actor_without_delegation_validates():
    """RFC §4.1: services are deterministic and do not require delegation.
    The agent->delegation conditional must not fire for subject_type=service."""
    event = {
        "schema_version": "2.0",
        "event_id": "00000000-0000-4000-8000-00000000a001",
        "timestamp": "2026-06-12T14:02:11Z",
        "service": {"name": "bh-nightly-export"},
        "actor": {
            "subject_id": "svc_nightly_export",
            "subject_type": "service",
        },
        "action": {"type": "EXPORT", "phi_touched": True,
                   "data_classification": "PHI"},
        "resource": {"type": "PatientRecord", "id": "export_001",
                     "patient_id": "pat_456"},
        "outcome": {"status": "SUCCESS"},
    }
    jsonschema.validate(
        instance=event, schema=V2_SCHEMA,
        format_checker=jsonschema.FormatChecker(),
    )


def test_service_actor_with_delegation_validates():
    """A service may still optionally emit delegation if a deployment
    chooses to; the rule fires only as 'agent implies delegation', not
    the reverse."""
    event = {
        "schema_version": "2.0",
        "event_id": "00000000-0000-4000-8000-00000000a002",
        "timestamp": "2026-06-12T14:02:11Z",
        "service": {"name": "bh-export"},
        "actor": {"subject_id": "svc", "subject_type": "service"},
        "delegation": {
            "acting": {
                "subject_id": "agent_inst",
                "subject_type": "agent",
                "agent": {"interface": "api"},
            },
            "authorizing": {"subject_id": "user_1", "subject_type": "human"},
            "delegation_type": "scheduled",
            "agent_session_id": "agsess_svc_001",
        },
        "action": {"type": "READ"},
        "resource": {"type": "Patient", "id": "pat_1"},
        "outcome": {"status": "SUCCESS"},
    }
    jsonschema.validate(
        instance=event, schema=V2_SCHEMA,
        format_checker=jsonschema.FormatChecker(),
    )
