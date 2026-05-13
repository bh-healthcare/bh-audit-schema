# Changelog

All notable changes to the bh-audit-schema project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2026-05-12

### Changed

- Refactored `ActionType`, `OutcomeStatus`, and `DataClassification` from inline
  `enum` arrays into named `$defs` with `$ref` usage. Enum values are identical.
  Enables downstream consumers to derive allowlists from a single source of truth.
  Closes bh-healthcare/bh-audit-schema#5.

## [1.1.1] - 2026-03-11

### Added

- **HIPAA/SOC 2/42 CFR Part 2 controls mapping** -- `docs/controls-mapping.md` rewritten with
  detailed per-section mappings to HIPAA Security Rule (§164.312(b), §164.312(a), §164.308(a),
  §164.312(c)), SOC 2 Trust Services Criteria (CC6.1, CC6.3, CC7.2, CC7.3), and 42 CFR Part 2
  (§2.16, §2.13). Each mapping references specific schema fields and calls out v1.1 additions.
  Includes implementer checklists for minimum viable and enhanced audit implementations.

## [1.1.0] - 2026-03-11

### Added

- **UUID enforcement** -- `event_id` now requires `format: "uuid"` (36 chars, `8-4-4-4-12`).
- **HTTP method enum** -- `http.method` constrained to `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`.
- **HTTP status bounds** -- `http.status_code` constrained to `100-599`.
- **Client IP format** -- `http.client_ip` accepts both IPv4 and IPv6 via `anyOf` with `format: "ipv4"` / `format: "ipv6"`.
- **User-agent cap** -- `http.user_agent` limited to `maxLength: 512`.
- **`actor.owner_org_id`** -- new field for cross-organization access detection.
- **`DENIED` outcome status** -- distinguishes authorization denials from operational failures (critical for HIPAA access reports). DENIED means the system correctly refused access. `error_type` is required on DENIED to give compliance and SOC teams queryable denial categories (e.g., `RoleDenied`, `CrossOrgAccessDenied`, `ConsentRequired`). `error_message` is optional on DENIED.
- **Error fields required on FAILURE** -- conditional validation: `outcome.status == "FAILURE"` now requires `error_type` and `error_message`.
- **Error type required on DENIED** -- conditional validation: `outcome.status == "DENIED"` now requires `error_type` (but not `error_message`).
- **Metadata scalar constraint** -- values restricted to string, integer, number, boolean, null; nested objects/arrays rejected by schema. `maxProperties: 20`.
- **Correlation non-empty** -- `correlation` requires `minProperties: 1` when present.
- **Hash algorithm enum** -- `integrity.hash_alg` constrained to `sha256`, `sha384`, `sha512`.
- **Integrity dependency rules** -- `event_hash` requires `hash_alg`; `prev_event_hash` requires both `hash_alg` and `event_hash`.
- **Error message length cap** -- `outcome.error_message` limited to `maxLength: 500`.
- **Empty string prevention** -- `minLength: 1` added to all ID, correlation, and identifier string fields.
- **Unbounded string caps** -- `maxLength` added to all previously unbounded string fields (service.name, org_id, resource.id, etc.).
- **Roles array bounds** -- `maxItems: 25` with `minLength: 1` on items.
- New v1.1 examples: `access_denied.json`, `cross_org_access_denied.json`, `service_export_with_integrity.json`.
- CI workflow: GitHub Actions validates all examples against their schema on every push/PR (with `FormatChecker` enabled).
- Validation script: `scripts/validate_examples.py`.

See [docs/controls-mapping.md](docs/controls-mapping.md) for detailed HIPAA Security Rule (§164.312, §164.308), SOC 2 (CC6/CC7), and 42 CFR Part 2 alignment.

### Fixed

- CONTRIBUTING.md incorrectly claimed camelCase naming; corrected to snake_case.
- `docs/query-examples.md` referenced non-existent `resource.owner_org_id`; corrected to `actor.owner_org_id`.
- `docs/field-definitions.md` fully updated for v1.1 (was documenting v1.0 semantics).
- `docs/versioning.md` version history table now includes v1.1; versioning policy clarified.
- `docs/event-types.md` "Failed Access Attempt" pattern updated to use `DENIED` status.

## [1.0.0] - 2026-01-06

### Added

- Initial release of the BH Audit Event schema.
- Required fields: `schema_version`, `event_id`, `timestamp`, `service`, `actor`, `action`, `resource`, `outcome`.
- Optional objects: `correlation`, `http`, `integrity`, `metadata`.
- Action types: `READ`, `CREATE`, `UPDATE`, `DELETE`, `EXPORT`, `LOGIN`, `LOGOUT`, `PRINT`, `OTHER`.
- Data classification enum: `PHI`, `PII`, `NONE`, `UNKNOWN`.
- Actor types: `human`, `service`.
- Outcome statuses: `SUCCESS`, `FAILURE`.
- `additionalProperties: false` enforced at all levels except `metadata`.
- Documentation: field definitions, event types, privacy model, controls mapping, query examples, rationale, versioning.
- Examples: patient read, login, note update failure, patient data export.

[1.1.2]: https://github.com/bh-healthcare/bh-audit-schema/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/bh-healthcare/bh-audit-schema/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/bh-healthcare/bh-audit-schema/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/bh-healthcare/bh-audit-schema/releases/tag/v1.0.0
