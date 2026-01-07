# Privacy Model

This document describes the privacy-preserving design principles embedded in the BH Audit Event schema.

---

## Core Principle: PHI Safety by Default

The schema is designed so that **audit events are useful without containing raw PHI**.

Behavioral health data is among the most sensitive categories of protected health information. Audit logs must enable compliance and security objectives without creating a secondary repository of sensitive data.

---

## Design Rules

### 1. No Bodies by Default

Audit events should capture **what happened** and **to what**, not **the content** of what was accessed.

| ✅ Include                         | ❌ Do Not Include                    |
|------------------------------------|--------------------------------------|
| Resource type (`Note`)             | Note content                         |
| Resource ID (`note_456`)           | Clinical text                        |
| Patient ID (`pat_123`)             | Patient name, DOB, SSN               |
| Action type (`UPDATE`)             | Before/after field values            |
| Outcome (`SUCCESS`/`FAILURE`)      | Full request/response bodies         |

### 2. Identifiers Over Identities

Use opaque identifiers, not human-readable names or sensitive attributes.

| ✅ Good                            | ❌ Avoid                             |
|------------------------------------|--------------------------------------|
| `subject_id: "user_123"`           | `subject_name: "Dr. Jane Smith"`     |
| `patient_id: "pat_456"`            | `patient_name: "John Doe"`           |
| `org_id: "org_77"`                 | `org_name: "Springfield BH Clinic"`  |

### 3. Templates Over Raw Paths

Use URL templates that describe the route pattern, not actual paths that may contain PHI.

| ✅ Good                                            | ❌ Avoid                                        |
|----------------------------------------------------|-------------------------------------------------|
| `/patients/{patient_id}/notes/{note_id}`           | `/patients/pat_456/notes/note_999`              |
| `/encounters/{encounter_id}`                       | `/encounters/enc_123?diagnosis=depression`      |

### 4. Sanitized Error Messages

Error messages must not contain PHI, even in failure scenarios.

| ✅ Good                            | ❌ Avoid                                         |
|------------------------------------|--------------------------------------------------|
| `"Access denied."`                 | `"User cannot access patient John Smith's note."`|
| `"Resource not found."`            | `"Note about depression diagnosis not found."`   |
| `"Validation failed."`             | `"Invalid SSN: 123-45-6789"`                     |

### 5. Safe Metadata

The `metadata` object allows extensibility, but must not be used for PHI.

| ✅ Acceptable Metadata             | ❌ Not Acceptable                    |
|------------------------------------|--------------------------------------|
| `export_format: "pdf"`             | `diagnosis_codes: ["F32.1"]`         |
| `reason: "continuity_of_care"`     | `note_preview: "Patient reports..."`|
| `client_version: "2.1.0"`          | `patient_dob: "1990-01-15"`          |

---

## Sensitive Field Guidance

### Fields That Require Care

| Field                    | Guidance                                                   |
|--------------------------|------------------------------------------------------------|
| `actor.subject_id`       | Use internal user IDs, not email addresses                 |
| `resource.patient_id`    | Use internal patient IDs, not MRNs or SSNs                 |
| `http.route_template`    | Use templates, not raw paths with IDs                      |
| `outcome.error_message`  | Sanitize before logging                                    |
| `metadata.*`             | Review all keys for PHI before adding                      |

### Fields That Are Typically Safe

| Field                    | Notes                                                      |
|--------------------------|------------------------------------------------------------|
| `event_id`               | Generated UUID, no PHI                                     |
| `timestamp`              | Time of event, no PHI                                      |
| `service.name`           | Service identifier, no PHI                                 |
| `action.type`            | Enum value, no PHI                                         |
| `resource.type`          | Resource category, no PHI                                  |
| `outcome.status`         | Enum value, no PHI                                         |

---

## PHI Classification Fields

The schema includes explicit fields for PHI classification:

### `action.phi_touched`

Boolean flag indicating whether the action accessed or modified PHI.

**Set to `true` when:**
- Reading patient clinical data
- Writing clinical notes
- Accessing therapy records
- Exporting patient information

**Set to `false` when:**
- User login/logout
- System configuration changes
- Non-clinical administrative actions

### `action.data_classification`

More granular classification:

| Value     | Meaning                                                     |
|-----------|-------------------------------------------------------------|
| `PHI`     | Protected Health Information (clinical, behavioral health)  |
| `PII`     | Personally Identifiable Information (non-clinical)          |
| `NONE`    | Non-sensitive data                                          |
| `UNKNOWN` | Classification could not be determined                      |

---

## Audit Log Access Control

While not part of the schema itself, implementers should consider:

### Who Can Access Audit Logs?

- Audit logs themselves may be sensitive (they reveal access patterns)
- Restrict access to security/compliance personnel
- Log access to audit logs (meta-auditing)

### Audit Log Storage

- Store separately from production PHI databases
- Apply appropriate access controls
- Consider encryption at rest

---

## Behavioral Health-Specific Considerations

Behavioral health data has additional sensitivity:

| Context                          | Implication                                         |
|----------------------------------|-----------------------------------------------------|
| 42 CFR Part 2 (substance use)    | Stricter consent requirements for disclosure        |
| Psychotherapy notes              | Often excluded from standard access                 |
| Sensitive diagnoses              | May require additional access restrictions          |

The schema supports these scenarios by:
- Enabling granular `resource.type` values
- Supporting `data_classification` for risk-based handling
- Capturing `actor.roles` for access review

---

## Summary

| Principle                    | Implementation                                         |
|------------------------------|--------------------------------------------------------|
| No bodies by default         | Capture metadata, not content                          |
| Identifiers over identities  | Use opaque IDs, not names                              |
| Templates over raw paths     | Use `route_template`, not actual URLs                  |
| Sanitized errors             | Strip PHI from `error_message`                         |
| Safe metadata                | Review all custom fields for PHI                       |
| Explicit classification      | Use `phi_touched` and `data_classification`            |

