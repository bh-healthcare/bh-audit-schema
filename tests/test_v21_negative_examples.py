"""Every file in examples/2.1/negative/*.json must FAIL v2.1 validation.

Files 01 to 13 are the v2.0 negative corpus carried forward, so a regression
to laxer enforcement of the RFC 0001 rules surfaces here as well as in the
v2.0 suite. Files 14 to 21 are the RFC 0003 §11.1 boundary probes for R1 to
R4 and the OVERRIDE amendment.
"""

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "versions" / "2.1" / "audit_event.schema.json").read_text()
)
NEGATIVE_DIR = REPO_ROOT / "examples" / "2.1" / "negative"
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
    """RFC 0003 §11.1 specifies 21 negative cases: 13 inherited plus 8 new."""
    assert len(NEGATIVES) == 21, [p.name for p in NEGATIVES]


def test_inherited_negatives_carried_forward():
    """The v2.0 negative corpus is present under v2.1 file for file."""
    v20 = {p.name for p in (REPO_ROOT / "examples" / "2.0" / "negative").glob("*.json")}
    v21 = {p.name for p in NEGATIVES}
    assert v20 <= v21, sorted(v20 - v21)
