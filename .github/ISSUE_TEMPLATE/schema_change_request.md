---
name: Schema Change Request
about: Propose a change to the audit event schema
title: "[SCHEMA] "
labels: schema-change
assignees: ''
---

## Motivation

Why is this change needed? What problem does it solve?

## Proposed Change

Describe the proposed schema modification in detail.

### Fields to Add/Modify/Remove

```json
// Example of the proposed change
{
  "new_field": {
    "type": "string",
    "description": "..."
  }
}
```

## Backward Compatibility

- [ ] This change is backward compatible (additive only)
- [ ] This change is NOT backward compatible (breaking change)

### If Breaking Change

Explain why a breaking change is necessary and cannot be avoided.

## Migration Notes

How should existing implementations migrate to support this change?

## Examples

Provide example events that demonstrate the change:

```json
{
  "schema_version": "...",
  "event_id": "...",
  // ... example with proposed change
}
```

## Alternatives Considered

What alternative approaches were considered? Why were they rejected?

## Additional Context

Any other context, references to related issues, or links to relevant discussions.

---

**Checklist:**

- [ ] I have reviewed the [versioning policy](../../docs/versioning.md)
- [ ] I have reviewed existing [field definitions](../../docs/field-definitions.md)
- [ ] I have considered the [privacy model](../../docs/privacy-model.md)
- [ ] I have provided example events demonstrating the change

