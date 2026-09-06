# Schema Versioning

This document explains how the BH Audit Event schema is versioned and how changes are managed.

---

## Version Numbering

The schema follows semantic versioning principles:

| Version | Meaning                                                    |
|---------|------------------------------------------------------------|
| `1.x`   | Backward-compatible additions to the v1 schema             |
| `2.0`   | Breaking changes that require migration                    |
| `2.x`   | Backward-compatible additions to the v2 schema             |

### What Constitutes a Breaking Change?

**Breaking changes (require major version bump):**
- Removing a required field
- Adding a field that is **unconditionally required at the root**
- Changing a field's type
- Removing an enum value
- Changing field semantics in incompatible ways

**Non-breaking changes (minor version bump):**
- Adding optional fields or sub-fields
- Adding a field that is required **only when an existing optional object is present**
- Adding new enum values (e.g., new outcome statuses)
- Adding format, minLength, maxLength, or range constraints to previously unconstrained fields
- Adding conditional validation requirements (e.g., FAILURE requires error fields)
- Restricting metadata value types (e.g., scalar-only)
- Relaxing validation constraints
- Clarifying documentation

> **Note:** Adding constraints to previously unconstrained areas (e.g., requiring `format: "uuid"` on `event_id` that previously only required `minLength: 16`) is considered non-breaking because well-formed producers already satisfy the new constraints. The migration notes in each version's CHANGELOG document what changes may require producer updates.

> **Note on required fields.** The distinction above is deliberate and narrow. A field required unconditionally at the root invalidates every event a producer has ever emitted the moment it adopts the new version, including events describing situations the field has nothing to say about. A field required only inside an already-optional object is scoped to producers that were already emitting that object, and it is unreachable for everyone else.
>
> Neither case reinterprets a stored record, because `schema_version` is a `const` per version and a v2.0 event is never validated against a v2.1 schema. What a conditionally required field does break is a producer that updates its version string without adding the field, and that producer gets a hard validation failure at the point of emission, which is where the problem should surface. See [RFC 0003 section 12](rfc/RFC-0003-attribution-assurance.md#12-decisions-and-open-items) for the case that motivated this clarification.

---

## Directory Structure

```
schema/
├── audit_event.schema.json      # Latest stable (pointer)
└── versions/
    ├── 1.0/
    │   ├── audit_event.schema.json
    │   └── CHANGELOG.md
    ├── 1.1/
    │   ├── audit_event.schema.json
    │   └── CHANGELOG.md
    ├── 2.0/
    │   └── audit_event.schema.json
    └── 2.1/
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
  "schema_version": "1.1",
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

The previous major version should be supported for at least 6 months after a new major version release.

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

| Version | Release Date | Status       | Notes                                                        |
|---------|--------------|--------------|--------------------------------------------------------------|
| 2.1     | 2026-09-06   | Current      | Attribution assurance: `attribution` object and the `unattributed` agent case (RFC 0003) |
| 2.0     | 2026-07-02   | Supported    | AI agent attribution and the human-agent delegation chain (RFC 0001) |
| 1.1.2   | 2026-05-12   | Supported    | Enum `$defs` refactor (structural, no value changes)         |
| 1.1     | 2026-03-11   | Supported    | Hardening: UUID enforcement, DENIED status, metadata scalars |
| 1.0     | 2026-01-06   | Supported    | Initial release                                              |

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

