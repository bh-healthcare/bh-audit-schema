"""Every file in examples/2.1/*.json must validate against the v2.1 schema."""

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "versions" / "2.1" / "audit_event.schema.json").read_text()
)
POSITIVE_DIR = REPO_ROOT / "examples" / "2.1"

POSITIVES = sorted(POSITIVE_DIR.glob("*.json"))


@pytest.mark.parametrize("path", POSITIVES, ids=lambda p: p.name)
def test_positive_example_validates(path):
    event = json.loads(path.read_text())
    jsonschema.validate(
        instance=event,
        schema=SCHEMA,
        format_checker=jsonschema.FormatChecker(),
    )


def test_positive_corpus_count():
    """RFC 0003 §11.1 specifies 11 positive cases: the 7 carried forward from
    v2.0 plus an enforced-tier denial at `unattributed`, a fail-open success
    at `unattributed`, an `asserted` call, and an attribution block with
    `method` omitted."""
    assert len(POSITIVES) == 11, [p.name for p in POSITIVES]


def test_rfc_0003_additions_present():
    names = {p.name for p in POSITIVES}
    assert "agent_denied_unattributed.json" in names
    assert "agent_fail_open_unattributed.json" in names
    assert "agent_asserted_call.json" in names
    assert "agent_bound_method_omitted.json" in names


def test_corpus_exercises_every_level():
    """RFC 0003 §11.1: at least one inherited agent example sits at `bound`
    so the corpus does not exercise a single level."""
    levels = {
        json.loads(p.read_text()).get("attribution", {}).get("level")
        for p in POSITIVES
    }
    assert {"verified", "bound", "asserted", "unattributed"} <= levels, levels


def test_method_omitted_example_carries_level_only():
    event = json.loads((POSITIVE_DIR / "agent_bound_method_omitted.json").read_text())
    assert event["attribution"] == {"level": "bound"}
