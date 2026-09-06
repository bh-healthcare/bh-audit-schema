# FHIR R5 AuditEvent Alignment

bh-audit-schema v2.0 and v2.1 ship with first-class FHIR R5 AuditEvent expression. The
JSON Schema contract serves producers that need strict machine validation
without FHIR infrastructure; the profile + translator serve the FHIR ecosystem.

## Documents

- **[Gap analysis and proposed profile](fhir-r5-gap-analysis-and-profile.md)** --
  enumerates nine gaps (G1-G9) in stock R5 AuditEvent that block AI-agent
  attribution and shows how the proposed profile closes them via three
  attribution-typed agent slices, profile invariants (G8 PHI-minimization,
  G9 attribution-completeness), and a bounded extension set covering only
  G4-G6. v2.1 adds G10 (attribution assurance), the `attribution-level` and
  `attribution-method` extensions, an `unattributed` agent slice, and a
  recorded divergence from the two-events-and-Task pattern for sub-agent
  chains, which this project proposed on the open ticket FHIR-58715
  (section 8). Includes a per-element mapping with a documented loss
  register.

## Tooling

- **[`scripts/translate_to_fhir.py`](../../scripts/translate_to_fhir.py)** --
  reference translator: bh-audit-schema v2.0 or v2.1 event → R5 AuditEvent
  resource. Three attribution-typed agent slices (`authenticating-identity`,
  `acting-identity`, `authorizing-identity`) for delegated events; a single
  `direct` agent for collapse and override cases; a single `unattributed`
  agent, with `requestor` false, for a v2.1 event whose authorizing human
  could not be named. Optional R5 structural validation via `fhir.resources`
  (`pip install "fhir.resources>=8.0.0"`). Each resource claims the profile
  canonical for its own schema version, `.../fhir/2.0/...` or
  `.../fhir/2.1/...`; the two profiles differ and are not interchangeable.

  Run on every v2.0 and v2.1 positive example:

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
- **`attribution.*`** (v2.1) rides on extensions because R5 AuditEvent has no
  native concept of attribution assurance. A consumer that ignores the
  extension sees an authenticating agent and no assurance statement.

## Why a profile, not a competing standard

A solo schema does not out-standard HL7 and should not try. The profile is the
same model expressed in HL7's terms so that FHIR-native systems, HIEs, and
EMR-adjacent infrastructure can consume attribution events without adopting
anything outside the FHIR ecosystem. Contract for producers, profile +
translator as the bridge.
