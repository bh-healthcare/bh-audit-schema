# Schema Versioning

This document explains how the BH Audit Event schema is versioned and how changes are managed.

---

## Version Numbering

The schema follows semantic versioning principles:

| Version | Meaning                                                    |
|---------|------------------------------------------------------------|
| `1.x`   | Backward-compatible additions to the v1 schema             |
| `2.0`   | Breaking changes that require migration                    |

### What Constitutes a Breaking Change?

**Breaking changes (require major version bump):**
- Removing a required field
- Changing a field's type
- Removing an enum value
- Changing field semantics in incompatible ways
- Tightening validation constraints on required fields

**Non-breaking changes (minor version bump):**
- Adding optional fields
- Adding new enum values
- Relaxing validation constraints
- Clarifying documentation

---

## Directory Structure

```
schema/
├── audit_event.schema.json      # Latest stable (pointer)
└── versions/
    ├── 1.0/
    │   ├── audit_event.schema.json
    │   └── CHANGELOG.md
    └── 1.1/                     # Future
        ├── audit_event.schema.json
        └── CHANGELOG.md
```

### `schema/audit_event.schema.json`

This is the **latest stable pointer**. It always contains a copy of the most recent stable schema version.

**Use this for:**
- New implementations
- Default validation
- Documentation references

### `schema/versions/<ver>/`

Versioned directories are **immutable**. Once a version is released, its schema is never modified (except for documentation typos).

**Use versioned schemas for:**
- Validating events tagged with a specific `schema_version`
- Historical reference
- Migration tooling

---

## The `schema_version` Field

Every audit event must include a `schema_version` field:

```json
{
  "schema_version": "1.0",
  ...
}
```

This field:
- Is required
- Is validated as a const in each schema version
- Enables consumers to route events to appropriate validators
- Supports gradual migration across schema versions

---

## Consuming Events with Multiple Versions

Organizations may have events from multiple schema versions in their audit logs. Recommended approach:

1. **Route by `schema_version`**: Parse the field before full validation.
2. **Validate against the matching schema**: Use `schema/versions/<ver>/audit_event.schema.json`.
3. **Normalize if needed**: Transform older events to the latest format for querying.

Example routing logic:

```python
def get_schema_path(event: dict) -> str:
    version = event.get("schema_version", "1.0")
    return f"schema/versions/{version}/audit_event.schema.json"
```

---

## Migration Between Versions

When a new schema version is released:

1. **Review the CHANGELOG** for the new version.
2. **Update event producers** to emit the new `schema_version`.
3. **Update event consumers** to handle both old and new versions during transition.
4. **Set a deprecation timeline** for the old version.

### Transition Period

We recommend supporting the previous major version for at least 6 months after a new major version release.

---

## Release Process

Schema changes follow this process:

1. **Proposal**: Open a schema change request issue.
2. **Review**: Maintainers assess backward compatibility and impact.
3. **RFC period**: Community feedback for significant changes.
4. **Implementation**: Create new version directory with schema and changelog.
5. **Release**: Update `schema/audit_event.schema.json` to point to new version.
6. **Announcement**: Document migration path in changelog.

---

## Version History

| Version | Release Date | Status       | Notes                    |
|---------|--------------|--------------|--------------------------|
| 1.0     | 2026-01-06   | Current      | Initial release          |

---

## Referencing Schemas

### In Documentation

Link to the GitHub Pages URL:

```
https://bh-healthcare.github.io/bh-audit-schema/1.0/audit_event.schema.json
```

### In Code

Reference the schema `$id`:

```json
{
  "$schema": "https://bh-healthcare.github.io/bh-audit-schema/1.0/audit_event.schema.json"
}
```

### For Validation

Clone the repository and reference local paths:

```
./schema/versions/1.0/audit_event.schema.json
```

Or reference the latest stable:

```
./schema/audit_event.schema.json
```

