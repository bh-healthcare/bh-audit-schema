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
| [`schema/audit_event.schema.json`](schema/audit_event.schema.json) | Latest stable schema (currently **v2.0.0**) -- byte-for-byte copy of `schema/versions/2.0/audit_event.schema.json` |
| [`schema/versions/2.0/`](schema/versions/2.0/) | **v2.0** -- AI agent attribution and human-agent delegation chain (default). See [RFC 0001](docs/rfc/RFC-0001-agent-attribution-github.md) |
| [`schema/versions/1.1/`](schema/versions/1.1/) | Immutable v1.1.x schema (latest: 1.1.2). v1.1 producers should validate against this path, not the root |
| [`schema/versions/1.0/`](schema/versions/1.0/) | Immutable v1.0 schema |

> Validating an event against `schema/audit_event.schema.json` now applies v2.0 actor semantics. Producers on v1.1 or v1.0 must validate against their `schema/versions/<version>/` file directly.

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

## v2.0: AI Agent Attribution

v2.0 extends the schema with a multi-actor attribution model so that AI agents operating under delegated human authority can be audited truthfully. The single `actor` field of v1.x carried three implicit meanings -- *authenticating identity*, *acting identity*, *authorizing identity* -- that always collapsed into one person until agents began operating software. v2.0 splits them via a new optional top-level `delegation` object, extends `actor.subject_type` to include `"agent"`, adds an `OVERRIDE` action for human interruption of agent sessions, and rejects unattributed agent actions by construction.

Producers in agent-free environments adopt v2.0 by updating `schema_version` to `"2.0"`; nothing else changes. Producers in agent-exposed environments must emit attribution via an Enforced or Instrumented path (see RFC §11) to claim v2.0 attribution semantics.

- **RFC**: [`docs/rfc/RFC-0001-agent-attribution-github.md`](docs/rfc/RFC-0001-agent-attribution-github.md)
- **FHIR R5 alignment**: [`docs/fhir/fhir-r5-gap-analysis-and-profile.md`](docs/fhir/fhir-r5-gap-analysis-and-profile.md) (gap analysis G1-G9, prior-art positioning vs HL7's `AuditEvent.agent.onBehalfOf` extension and IHE Basic Audit Log Patterns) plus the [`scripts/translate_to_fhir.py`](scripts/translate_to_fhir.py) translator (R5-validated against `fhir.resources` in CI)
- **Examples**: [`examples/2.0/`](examples/2.0/) (7 positive -- 5 core attribution scenarios plus 2 session-lifecycle convention examples -- and 13 negative)
- **Controls mapping deltas**: [`docs/controls-mapping.md`](docs/controls-mapping.md#v20-deltas----ai-agent-attribution) -- HIPAA §164.312(b)/(d), 42 CFR Part 2 §2.13/§2.16, SOC 2 CC6.1/CC7.2, NIST AI RMF, ISO/IEC 42001 §8.3

## Documentation

| Document | Description |
|----------|-------------|
| [Field Definitions](docs/field-definitions.md) | Semantics for each schema field |
| [Event Types](docs/event-types.md) | Recommended patterns for common events |
| [Privacy Model](docs/privacy-model.md) | PHI-safe design principles |
| [Controls Mapping](docs/controls-mapping.md) | Engineering mapping to compliance objectives |
| [Query Examples](docs/query-examples.md) | Representative audit queries supported by the schema |
| [Versioning](docs/versioning.md) | Schema evolution and version management |
| [Rationale](docs/rationale.md) | Why this standard exists |

## Schema Design Principles

### PHI Safety by Default

Audit events capture **what happened**, not **the content** of what was accessed. The schema is designed so audit logs are useful without containing raw Protected Health Information.

### Strict Validation

The schema uses `additionalProperties: false` at all levels (except `metadata`) to ensure events conform exactly to the specification.

### Single Source of Truth for Enums

As of **v1.1.2**, the canonical enum types — `ActionType`, `OutcomeStatus`, and
`DataClassification` — live as named definitions under `$defs` and are referenced
via `$ref` from `action.type`, `outcome.status`, and `action.data_classification`.
The accepted values are unchanged. This lets downstream consumers
(`bh-fastapi-audit`, `bh-audit-logger`, custom validators) derive their allowlists
from a single, machine-readable source instead of duplicating the enum arrays.

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

**Exception:** the [`papers/`](papers/) directory contains research writing licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) rather than Apache 2.0. See [`papers/README.md`](papers/README.md) for details.
