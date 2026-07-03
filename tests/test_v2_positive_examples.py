"""Every file in examples/2.0/*.json must validate against the v2.0 schema."""

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "versions" / "2.0" / "audit_event.schema.json").read_text()
)
POSITIVE_DIR = REPO_ROOT / "examples" / "2.0"

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
    """RFC §15 specifies 5 core positive cases (agent MCP read, UI-driving
    write, human override, depth-2 sub-agent export, human-direct read).
    Two additional RFC §7.2 session-lifecycle conventions (CREATE start,
    UPDATE end) bring the corpus to 7."""
    assert len(POSITIVES) == 7, [p.name for p in POSITIVES]


def test_session_lifecycle_examples_present():
    names = {p.name for p in POSITIVES}
    assert "agent_session_start.json" in names
    assert "agent_session_end.json" in names
