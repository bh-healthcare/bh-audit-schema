# Changelog -- Schema v2.1

All notable changes to the v2.1 schema line are documented in this file.

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) conventions.

---

## [2.1.0] -- 2026-09-06

Minor version implementing [RFC 0003: Attribution Assurance and the Unattributed Agent](../../docs/rfc/RFC-0003-attribution-assurance.md). Additive with respect to v2.0 for producers that do not emit `delegation`: their events become valid v2.1 events by updating `schema_version`.

### Added

- `attribution`: new optional top-level object stating how the event's attribution was established.
  - `level` (required within the object): closed enum `verified`, `bound`, `asserted`, `unattributed`, defined in `$defs/AttributionLevel` and referenced via `$ref`.
  - `method` (optional): open-vocabulary string, `minLength: 1, maxLength: 64`.
  - `additionalProperties: false`.
- Conditional validation R1: when `delegation` is present, `attribution` is required and `level` must be one of `verified`, `bound`, `asserted`.
- Conditional validation R2: when `attribution.level` is `unattributed`, `delegation` is forbidden.
- Conditional validation R3: when `attribution.level` is `verified`, `bound`, or `asserted`, `delegation` is required.

### Changed

- `schema_version` bumped from `"2.0"` to `"2.1"`.
- `$id` updated to `https://bh-healthcare.github.io/bh-audit-schema/2.1/audit_event.schema.json`.
- Conditional validation R4, relaxed from the v2.0 rule that `actor.subject_type == "agent"` requires `delegation`: an agent actor now requires either `delegation` or `attribution.level: "unattributed"`. The one shape that is valid in v2.1 and was not in v2.0 is an agent actor carrying `attribution.level: "unattributed"` and no `delegation` block. An agent actor carrying neither block remains invalid.
- The `OVERRIDE` rule now also forbids `attribution`, in addition to forbidding `delegation` and requiring a human actor.
- The `delegation` description states that its absence asserts direct action unless `attribution.level` is `unattributed`, and requires an `attribution` block when present. Descriptions on `actor.subject_type` and `delegation.acting.subject_type` no longer name v2.0. No constraint on those fields changed.
- The FHIR profile canonical written to `meta.profile` now carries the schema version: `.../fhir/2.1/StructureDefinition/bh-audit-event` for v2.1 events and `.../fhir/2.0/StructureDefinition/bh-audit-event` for v2.0 events, in place of the unversioned canonical v2.0.0 emitted. The 2.1 profile adds inv-6, inv-7, the `unattributed` slice, and the attribution extensions, which a v2.0 resource does not satisfy, so the two versions cannot share one canonical.

### Fixed

- The FHIR R5 translator (`scripts/translate_to_fhir.py`) emitted a single `direct` agent slice with `requestor: true` for every event without a `delegation` block. For a v2.1 `unattributed` event that output asserted the agent acted directly as the requestor. The translator now emits an `unattributed` slice with `requestor: false` for those events, and emits the `attribution-level` and `attribution-method` extensions whether or not a delegation block exists.

### Notes

- The four levels are totally ordered, weakest to strongest: `unattributed` < `asserted` < `bound` < `verified` (RFC 0003 section 4.4). The order is normative and is not serialized; an event carries `level` as a string and nothing about its rank. Compare on position in the sequence, never on the string.
- Validators report R2, R4, and the `OVERRIDE` amendment by echoing the whole instance, because those rules use `not` and `anyOf`. Producers should validate the rules themselves and raise their own message (RFC 0003 section 11.2).

### Migration from v2.0

- Producers that do not emit `delegation`: update `schema_version` to `"2.1"`. Nothing else changes.
- Producers that emit `delegation`: add `attribution` to every such event, with `level` determined from the resolution path actually used. Do not default it to `verified`; a producer that cannot tell which path produced an attribution is describing `asserted`.
- Enforcing layers: emit `attribution.level: "unattributed"` with no `delegation` block on the denial and fail-open paths.
- Consumers: queries of the form "all agent actions with a named authorizing human" continue to work unchanged. Add a health query on `attribution.level = 'unattributed'` and a posture query on the distribution of `level`. Express any threshold on `level` as set membership or a rank join, never as a string comparison.
