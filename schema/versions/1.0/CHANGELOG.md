# Changelog – Schema v1.0

All notable changes to the v1.0 schema line are documented in this file.

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) conventions.

---

## [1.0.0] – 2026-01-06

### Added

- Initial release of the BH Audit Event schema.
- Required fields: `schema_version`, `event_id`, `timestamp`, `service`, `actor`, `action`, `resource`, `outcome`.
- Optional objects: `correlation`, `http`, `integrity`, `metadata`.
- Action types: `READ`, `CREATE`, `UPDATE`, `DELETE`, `EXPORT`, `LOGIN`, `LOGOUT`, `PRINT`, `OTHER`.
- Data classification enum: `PHI`, `PII`, `NONE`, `UNKNOWN`.
- Actor types: `human`, `service`.
- Outcome statuses: `SUCCESS`, `FAILURE`.
- `additionalProperties: false` enforced at all levels except `metadata`.

### Design Decisions

- Schema uses JSON Schema Draft 2020-12.
- `route_template` preferred over raw paths to avoid PHI leakage.
- `error_message` explicitly documented as requiring sanitization.
- `metadata` allows additional properties for extensibility, but must not contain PHI.

