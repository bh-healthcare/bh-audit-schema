# BH Audit Schema

A canonical, versioned audit event standard for behavioral health systems.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

This repository defines a standardized schema for audit events in behavioral health systems. It provides:

- **Versioned JSON Schema** for audit event validation
- **Examples** demonstrating compliant audit events
- **Documentation** covering field semantics, privacy design, and implementation guidance
- **Controls mapping** linking schema features to compliance objectives

## Who Should Use This

- **Healthcare software developers** building systems that handle behavioral health data
- **Security engineers** designing audit infrastructure
- **Compliance teams** evaluating audit logging capabilities
- **Organizations** seeking a standard audit format across multiple systems

## Quick Start

### Schema Location

| Path | Description |
|------|-------------|
| [`schema/audit_event.schema.json`](schema/audit_event.schema.json) | Latest stable schema |
| [`schema/versions/1.0/`](schema/versions/1.0/) | Immutable v1.0 schema |

### Example Event

```json
{
  "schema_version": "1.0",
  "event_id": "6d3f0f6b-0c1a-4b9f-9d6f-9f6f7f5b2b0a",
  "timestamp": "2026-01-06T18:40:12Z",
  "service": { "name": "bh-intake-api", "environment": "prod" },
  "actor": { "subject_id": "user_123", "subject_type": "human", "roles": ["care_coordinator"] },
  "action": { "type": "READ", "phi_touched": true, "data_classification": "PHI" },
  "resource": { "type": "Patient", "id": "pat_456", "patient_id": "pat_456" },
  "outcome": { "status": "SUCCESS" }
}
```

See [`examples/1.0/`](examples/1.0/) for more examples.

## Documentation

| Document | Description |
|----------|-------------|
| [Field Definitions](docs/field-definitions.md) | Semantics for each schema field |
| [Event Types](docs/event-types.md) | Recommended patterns for common events |
| [Privacy Model](docs/privacy-model.md) | PHI-safe design principles |
| [Controls Mapping](docs/controls-mapping.md) | Engineering mapping to compliance objectives |
| [Versioning](docs/versioning.md) | Schema evolution and version management |
| [Rationale](docs/rationale.md) | Why this standard exists |

## Schema Design Principles

### PHI Safety by Default

Audit events capture **what happened**, not **the content** of what was accessed. The schema is designed so audit logs are useful without containing raw Protected Health Information.

### Strict Validation

The schema uses `additionalProperties: false` at all levels (except `metadata`) to ensure events conform exactly to the specification.

### Implementation Flexibility

The schema defines **what** to log, not **how**. Use any language, framework, or storage backend.

## Related Projects

| Project | Description |
|---------|-------------|
| [bh-fastapi-audit](https://github.com/bh-healthcare/bh-fastapi-audit) | FastAPI middleware emitting events conforming to this schema |
| [bh-data-lake-reference](https://github.com/bh-healthcare/bh-data-lake-reference) | Reference architectures for audit event storage |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

Schema changes require discussion before implementation. Open a [schema change request](https://github.com/bh-healthcare/bh-audit-schema/issues/new?template=schema_change_request.md) to propose modifications.

## Governance

See [GOVERNANCE.md](GOVERNANCE.md) for project governance model.

## Versioning

The schema follows semantic versioning:
- **1.x**: Backward-compatible additions
- **2.0**: Breaking changes

See [docs/versioning.md](docs/versioning.md) for details.

## Disclaimer

> **This repository provides an engineering standard for audit event structure. It does not constitute legal advice, compliance certification, or guarantee of regulatory compliance.**
>
> Organizations must conduct their own compliance assessments with qualified professionals. The schema supports common audit control objectives but does not replace a comprehensive compliance program.

## License

Apache License 2.0. See [LICENSE](LICENSE).
