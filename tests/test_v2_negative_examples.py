"""Every file in examples/2.0/negative/*.json must FAIL v2.0 validation.

Negative cases are filename-prefixed with their RFC §6 rule number so that
regressions to laxer enforcement surface as test-name failures.
"""

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "versions" / "2.0" / "audit_event.schema.json").read_text()
)
NEGATIVE_DIR = REPO_ROOT / "examples" / "2.0" / "negative"
NEGATIVES = sorted(NEGATIVE_DIR.glob("*.json"))


@pytest.mark.parametrize("path", NEGATIVES, ids=lambda p: p.name)
def test_negative_example_fails(path):
    event = json.loads(path.read_text())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            instance=event,
            schema=SCHEMA,
            format_checker=jsonschema.FormatChecker(),
        )


def test_negative_corpus_count():
    """RFC §15 specifies 13 negative cases."""
    assert len(NEGATIVES) == 13, [p.name for p in NEGATIVES]
