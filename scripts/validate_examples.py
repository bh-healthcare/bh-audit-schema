#!/usr/bin/env python3
"""
Validate all example JSON files against their corresponding schema version.

Top-level files under examples/<version>/ must VALIDATE.
Files under examples/<version>/negative/ must FAIL validation (each one is
the minimal counter-example for a specific schema rule).

Usage:
    pip install jsonschema
    python scripts/validate_examples.py
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema is required. Install with: pip install jsonschema")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "schema" / "versions"
EXAMPLES_DIR = REPO_ROOT / "examples"


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def main() -> int:
    passed = 0
    failed = 0
    errors: list[str] = []

    for version_dir in sorted(EXAMPLES_DIR.iterdir()):
        if not version_dir.is_dir():
            continue
        version = version_dir.name

        schema_path = SCHEMA_DIR / version / "audit_event.schema.json"
        if not schema_path.exists():
            errors.append(f"Schema not found for version {version}: {schema_path}")
            failed += 1
            continue

        schema = load_json(schema_path)

        for example_path in sorted(version_dir.glob("*.json")):
            example = load_json(example_path)
            try:
                jsonschema.validate(
                    instance=example,
                    schema=schema,
                    format_checker=jsonschema.FormatChecker(),
                )
                passed += 1
                print(f"  PASS  {version}/{example_path.name}")
            except jsonschema.ValidationError as exc:
                failed += 1
                errors.append(f"{version}/{example_path.name}: {exc.message}")
                print(f"  FAIL  {version}/{example_path.name}: {exc.message}")

        negative_dir = version_dir / "negative"
        if negative_dir.is_dir():
            for example_path in sorted(negative_dir.glob("*.json")):
                example = load_json(example_path)
                try:
                    jsonschema.validate(
                        instance=example,
                        schema=schema,
                        format_checker=jsonschema.FormatChecker(),
                    )
                    failed += 1
                    msg = (f"{version}/negative/{example_path.name}: "
                           f"expected to fail but validated")
                    errors.append(msg)
                    print(f"  UNEXPECTED-PASS  {version}/negative/{example_path.name}")
                except jsonschema.ValidationError:
                    passed += 1
                    print(f"  REJECTED (as expected)  "
                          f"{version}/negative/{example_path.name}")

    print(f"\n{passed} passed, {failed} failed")
    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
