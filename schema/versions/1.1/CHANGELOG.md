# Changelog -- Schema v1.1

All notable changes to the v1.1 schema line are documented in this file.

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) conventions.

---

## [1.1.0] -- 2026-03-11

### Added

- `event_id`: enforced `format: "uuid"` with exact 36-character length constraint.
- `http.method`: enum constraint `["GET","HEAD","POST","PUT","PATCH","DELETE","OPTIONS"]`.
- `http.status_code`: range constraint `minimum: 100, maximum: 599`.
- `http.client_ip`: accepts both IPv4 (`format: "ipv4"`) and IPv6 (`format: "ipv6"`) via `anyOf`.
- `http.user_agent`: `maxLength: 512`.
- `http.route_template`: `maxLength: 512`.
- `actor.owner_org_id`: new field for cross-organization access detection.
- `outcome.status`: added `"DENIED"` to enum (distinguishes authorization denial from operational failure).
- `outcome.error_message`: `maxLength: 500`.
- `outcome.error_type`: `minLength: 1, maxLength: 128`.
- `integrity.hash_alg`: constrained to enum `["sha256","sha384","sha512"]`.
- `integrity`: `dependentRequired` -- `event_hash` requires `hash_alg`; `prev_event_hash` requires both `hash_alg` and `event_hash`.
- `metadata`: scalar-only values enforced via `additionalProperties` type constraint. `maxProperties: 20`.
- `correlation`: `minProperties: 1` (empty `{}` no longer valid).
- `roles`: `maxItems: 25`, items require `minLength: 1, maxLength: 64`.
- `minLength: 1` added to all ID and correlation string fields to prevent empty strings.
- `maxLength` bounds added to all previously unbounded string fields.
- Conditional validation: when `outcome.status == "FAILURE"`, `error_type` and `error_message` are required.
- Conditional validation: when `outcome.status == "DENIED"`, `error_type` is required (enables compliance teams to distinguish denial categories for HIPAA access review).

See [docs/controls-mapping.md](../../docs/controls-mapping.md) for detailed HIPAA Security Rule, SOC 2, and 42 CFR Part 2 alignment.

### Changed

- `schema_version` bumped from `"1.0"` to `"1.1"`.
- `$id` updated to `https://bh-healthcare.github.io/bh-audit-schema/1.1/audit_event.schema.json`.

### Migration from v1.0

- Events using `outcome.status: "FAILURE"` must now include `error_type` and `error_message`.
- Events using `outcome.status: "DENIED"` must now include `error_type`.
- `metadata` values must be scalars (no nested objects or arrays).
- `correlation` objects must contain at least one key if present.
- `event_id` must be a valid UUID (36 chars, formatted `8-4-4-4-12`).
- String fields now have `minLength` and `maxLength` constraints; empty strings are rejected.
- `integrity.event_hash` now requires `integrity.hash_alg` to be present.
- All other v1.0 events remain valid under v1.1 after updating `schema_version`.
