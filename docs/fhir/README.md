# FHIR R5 AuditEvent Alignment

bh-audit-schema v2.0 ships with first-class FHIR R5 AuditEvent expression. The
JSON Schema contract serves producers that need strict machine validation
without FHIR infrastructure; the profile + translator serve the FHIR ecosystem.

## Documents

- **[Gap analysis and proposed profile](fhir-r5-gap-analysis-and-profile.md)** --
  enumerates nine gaps (G1-G9) in stock R5 AuditEvent that block AI-agent
  attribution and shows how the proposed profile closes them via three
  attribution-typed agent slices, profile invariants (G8 PHI-minimization,
  G9 attribution-completeness), and a bounded extension set covering only
  G4-G6. Includes a per-element mapping with a documented loss register.

## Tooling

- **[`scripts/translate_to_fhir.py`](../../scripts/translate_to_fhir.py)** --
  reference translator: bh-audit-schema v2.0 event → R5 AuditEvent resource.
  Three attribution-typed agent slices (`authenticating-identity`,
  `acting-identity`, `authorizing-identity`) for delegated events; a single
  `direct` agent for collapse and override cases. Optional R5 structural
  validation via `fhir.resources` (`pip install "fhir.resources>=8.0.0"`).

  Run on every v2.0 positive example:

  ```bash
  python scripts/translate_to_fhir.py
  # or, without R5 validation (no fhir.resources required):
  python scripts/translate_to_fhir.py --no-validate
  ```

## Mapping loss register (summary)

Every loss the translator incurs is documented rather than hidden. The
authoritative table lives in the gap-analysis document; in short:

- **DENIED** collapses into R5 outcome code `8` ("Serious failure") for
  consumers that ignore the profile; the distinction is preserved in
  `outcome.detail` via the profile's `denied` coding.
- **`integrity.*`** (event_hash chaining) has no AuditEvent home and is not
  forced into one. A FHIR-native alternative is a paired Provenance with a
  `signature`.
- **`correlation.*`** (request_id / trace_id / session_id) awaits alignment
  with existing FHIR tracing conventions rather than a premature extension.

## Why a profile, not a competing standard

A solo schema does not out-standard HL7 and should not try. The profile is the
same model expressed in HL7's terms so that FHIR-native systems, HIEs, and
EMR-adjacent infrastructure can consume attribution events without adopting
anything outside the FHIR ecosystem. Contract for producers, profile +
translator as the bridge.
