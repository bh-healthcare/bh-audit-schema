# Field Definitions

This document defines the semantics for each field in the BH Audit Event schema.

---

## Top-Level Fields

### `schema_version`

- **Type:** `string` (const `"1.0"`)
- **Required:** Yes
- **Purpose:** Declares which version of the audit schema this event conforms to. Enables consumers to route events to version-appropriate processors.

### `event_id`

- **Type:** `string` (min 16 characters)
- **Required:** Yes
- **Purpose:** Globally unique identifier for this audit event. UUIDv4 is recommended.
- **Guidance:** Generate at event creation time. Do not reuse across retries.

### `timestamp`

- **Type:** `string` (ISO 8601 date-time)
- **Required:** Yes
- **Purpose:** UTC timestamp when the audited action occurred.
- **Guidance:** Use server-side timestamps, not client-provided values.

---

## `service` Object

Describes the service that generated the audit event.

| Field         | Type   | Required | Description                                      |
|---------------|--------|----------|--------------------------------------------------|
| `name`        | string | Yes      | Canonical service name (e.g., `bh-intake-api`)   |
| `environment` | string | No       | Deployment environment (`prod`, `staging`, `dev`)|
| `version`     | string | No       | Service version or build identifier              |

**Guidance:** Use consistent service names across your organization. The `name` field should match what appears in your service registry.

---

## `correlation` Object

Identifiers for correlating events across services and requests.

| Field        | Type   | Required | Description                                           |
|--------------|--------|----------|-------------------------------------------------------|
| `request_id` | string | No       | Unique identifier for the originating HTTP request    |
| `trace_id`   | string | No       | Distributed tracing identifier (e.g., OpenTelemetry)  |
| `session_id` | string | No       | User session identifier                               |

**Guidance:** Include `request_id` for HTTP-triggered events. Include `trace_id` if your infrastructure supports distributed tracing.

---

## `actor` Object

Describes who or what performed the action.

| Field          | Type     | Required | Description                                                  |
|----------------|----------|----------|--------------------------------------------------------------|
| `subject_id`   | string   | Yes      | Unique identifier for the actor                              |
| `subject_type` | string   | Yes      | `human` or `service`                                         |
| `org_id`       | string   | No       | Organization/tenant identifier                               |
| `roles`        | string[] | No       | Roles held by the actor at time of access                    |

### `subject_type` Values

- **`human`**: A human user authenticated via your identity system.
- **`service`**: A service principal, background job, or machine-to-machine actor.

**Guidance:**
- Use internal user IDs, not email addresses or names.
- Capture `roles` at time of access to support access review audits.
- Include `org_id` for multi-tenant systems.

---

## `action` Object

Describes what action was performed.

| Field                | Type    | Required | Description                                                      |
|----------------------|---------|----------|------------------------------------------------------------------|
| `type`               | string  | Yes      | Action category (see enum below)                                 |
| `name`               | string  | No       | Specific action name (e.g., `sign_bps`, `verify_insurance`)      |
| `phi_touched`        | boolean | No       | Whether the action touched regulated PHI                         |
| `data_classification`| string  | No       | Data classification: `PHI`, `PII`, `NONE`, `UNKNOWN`             |

### `action.type` Enum

| Value    | Use Case                                              |
|----------|-------------------------------------------------------|
| `READ`   | Retrieving or viewing data                            |
| `CREATE` | Creating new records                                  |
| `UPDATE` | Modifying existing records                            |
| `DELETE` | Removing records (hard or soft delete)                |
| `EXPORT` | Exporting data outside the system                     |
| `LOGIN`  | User authentication                                   |
| `LOGOUT` | User session termination                              |
| `PRINT`  | Printing records (physical or PDF generation)         |
| `OTHER`  | Actions not covered by the above categories           |

### `phi_touched` and `data_classification`

- **`phi_touched`**: Boolean flag indicating whether the action accessed or modified Protected Health Information under HIPAA/42 CFR Part 2.
- **`data_classification`**: More granular classification. Use `PHI` for behavioral health data, `PII` for identifiable but non-health data, `NONE` for non-sensitive data.

**Guidance:**
- Set `phi_touched: true` for any action that reads, writes, or transmits patient clinical data.
- Default to `data_classification: "UNKNOWN"` if classification cannot be determined.

---

## `resource` Object

Describes the resource being acted upon.

| Field        | Type   | Required | Description                                                   |
|--------------|--------|----------|---------------------------------------------------------------|
| `type`       | string | Yes      | Resource type (e.g., `Patient`, `Note`, `Encounter`)          |
| `id`         | string | No       | Resource identifier                                           |
| `patient_id` | string | No       | Patient identifier, if applicable                             |

### `patient_id` Usage

Include `patient_id` when:
- The action touches patient-specific data
- `phi_touched` is `true`
- The resource is a child of a patient record (notes, encounters, appointments)

**Guidance:**
- Use consistent resource type names across services.
- Do not include patient names or other PHI in resource fields.

---

## `http` Object

HTTP request context for web-triggered events.

| Field            | Type    | Required | Description                                                   |
|------------------|---------|----------|---------------------------------------------------------------|
| `method`         | string  | No       | HTTP method (`GET`, `POST`, `PATCH`, `DELETE`, etc.)          |
| `route_template` | string  | No       | URL template, not raw path                                    |
| `status_code`    | integer | No       | HTTP response status code                                     |
| `client_ip`      | string  | No       | Client IP address                                             |
| `user_agent`     | string  | No       | User-Agent header value                                       |

### `route_template` vs Raw Path

**Always use route templates, not raw paths.**

- ✅ `/patients/{patient_id}/notes/{note_id}`
- ❌ `/patients/pat_456/notes/note_999`

Raw paths may contain PHI or enable inference attacks.

---

## `outcome` Object

Describes the result of the action.

| Field           | Type   | Required | Description                                       |
|-----------------|--------|----------|---------------------------------------------------|
| `status`        | string | Yes      | `SUCCESS` or `FAILURE`                            |
| `error_type`    | string | No       | Error category (e.g., `Forbidden`, `NotFound`)    |
| `error_message` | string | No       | Sanitized error message                           |

### Error Message Sanitization

**`error_message` must not contain PHI.**

- ✅ `"Access denied."`
- ✅ `"Resource not found."`
- ❌ `"Patient John Smith not found."`
- ❌ `"Cannot update note containing diagnosis: depression"`

---

## `integrity` Object

Optional fields for tamper-evident audit chaining.

| Field            | Type   | Required | Description                                           |
|------------------|--------|----------|-------------------------------------------------------|
| `event_hash`     | string | No       | Hash of this event's content                          |
| `prev_event_hash`| string | No       | Hash of the previous event in the chain               |
| `hash_alg`       | string | No       | Hash algorithm used (e.g., `sha256`)                  |

**Guidance:** Integrity chaining is optional and implementation-dependent. Useful for high-assurance environments requiring tamper evidence.

---

## `metadata` Object

Flexible container for additional safe context.

- **Type:** Object with `additionalProperties: true`
- **Required:** No

### Rules

1. **Must not contain PHI.**
2. Use for operational context: export format, business reason codes, feature flags.
3. Keep keys consistent across services.

**Examples:**
```json
{
  "export_format": "pdf",
  "reason": "continuity_of_care"
}
```

```json
{
  "feature_flag": "new_intake_flow",
  "client_version": "2.1.0"
}
```

