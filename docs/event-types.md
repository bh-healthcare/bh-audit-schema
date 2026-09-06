# Event Types and Conventions

This document provides guidance on how to structure audit events for common scenarios.

---

## Action Type Mapping

### CRUD Operations

| Operation                | `action.type` | Notes                                      |
|--------------------------|---------------|--------------------------------------------|
| Get single resource      | `READ`        | Include `resource.id`                      |
| List/search resources    | `READ`        | `resource.id` may be omitted               |
| Create new resource      | `CREATE`      | Include `resource.id` of created resource  |
| Update existing resource | `UPDATE`      | Include `resource.id`                      |
| Delete resource          | `DELETE`      | Include `resource.id`                      |

### Non-CRUD Operations

| Operation               | `action.type` | Notes                                           |
|-------------------------|---------------|-------------------------------------------------|
| User login              | `LOGIN`       | `resource.type` = `Session`                     |
| User logout             | `LOGOUT`      | `resource.type` = `Session`                     |
| Export data             | `EXPORT`      | Set `phi_touched: true` if exporting PHI        |
| Print record            | `PRINT`       | Set `phi_touched: true` if printing PHI         |
| Custom business action  | `OTHER`       | Use `action.name` for specifics                 |

---

## Resource Type Naming

Use PascalCase singular nouns for `resource.type`:

| Resource          | `resource.type`  |
|-------------------|------------------|
| Patient record    | `Patient`        |
| Clinical note     | `Note`           |
| Encounter         | `Encounter`      |
| Appointment       | `Appointment`    |
| Treatment program | `Program`        |
| User session      | `Session`        |
| Export job        | `PatientRecord`  |
| Consent form      | `Consent`        |
| Assessment        | `Assessment`     |
| Medication        | `Medication`     |

**Guidance:**
- Be consistent across services.
- Match your domain model terminology.
- Avoid abbreviations.

---

## When to Set `patient_id`

Include `resource.patient_id` when:

| Scenario                                          | Include `patient_id`? |
|---------------------------------------------------|----------------------|
| Reading/writing a patient record                  | ✅ Yes               |
| Reading/writing a note for a patient              | ✅ Yes               |
| Reading/writing an encounter                      | ✅ Yes               |
| Searching across multiple patients                | ❌ No                |
| User login/logout                                 | ❌ No                |
| System configuration changes                      | ❌ No                |
| Exporting a specific patient's data               | ✅ Yes               |
| Bulk export (multiple patients)                   | ❌ No (use metadata) |

**Guidance:** If the action is patient-specific and `phi_touched: true`, include `patient_id`.

---

## When to Include `correlation`

### Always Include

- **`request_id`**: For all HTTP-triggered events. Enables request-level correlation.

### Include When Available

- **`trace_id`**: When using distributed tracing (OpenTelemetry, Jaeger, etc.).
- **`session_id`**: For user session correlation across multiple requests.

### Generating IDs

```
request_id: req_01HT7X9KQZV8N3M2P1R4S5T6U7
trace_id:   trace_9c2f8a3b1d4e5f6a7b8c9d0e
session_id: sess_abc123def456
```

Use prefixes to make IDs self-describing.

---

## When to Include `http`

Include the `http` object when:

| Scenario                              | Include `http`? |
|---------------------------------------|-----------------|
| REST API request                      | ✅ Yes          |
| GraphQL request                       | ✅ Yes          |
| Background job (no HTTP context)      | ❌ No           |
| Event-driven processing               | ❌ No           |
| CLI tool invocation                   | ❌ No           |

### Required Fields

When including `http`, always provide:
- `method`
- `route_template`
- `status_code`

Optional fields (`client_ip`, `user_agent`) are useful for security investigations.

---

## Common Event Patterns

### Patient Record Access

```json
{
  "action": { "type": "READ", "phi_touched": true, "data_classification": "PHI" },
  "resource": { "type": "Patient", "id": "pat_123", "patient_id": "pat_123" }
}
```

### Creating a Clinical Note

```json
{
  "action": { "type": "CREATE", "phi_touched": true, "data_classification": "PHI" },
  "resource": { "type": "Note", "id": "note_456", "patient_id": "pat_123" }
}
```

### User Authentication

```json
{
  "action": { "type": "LOGIN", "phi_touched": false, "data_classification": "NONE" },
  "resource": { "type": "Session", "id": "sess_789" }
}
```

### Data Export

```json
{
  "action": { 
    "type": "EXPORT", 
    "name": "export_patient_record",
    "phi_touched": true, 
    "data_classification": "PHI" 
  },
  "resource": { "type": "PatientRecord", "id": "export_001", "patient_id": "pat_123" },
  "metadata": { "export_format": "pdf", "reason": "continuity_of_care" }
}
```

### Service-to-Service Call

```json
{
  "actor": { "subject_id": "svc_billing", "subject_type": "service" },
  "action": { "type": "READ", "phi_touched": false, "data_classification": "PII" },
  "resource": { "type": "InsuranceEligibility", "id": "elig_123" }
}
```

### Denied Access Attempt

When the system correctly refuses access, use `DENIED` (not `FAILURE`). `DENIED` means the authorization system worked as intended. `FAILURE` means an operational error occurred.

```json
{
  "action": { "type": "READ", "phi_touched": false, "data_classification": "PHI" },
  "resource": { "type": "Note", "id": "note_456", "patient_id": "pat_123" },
  "outcome": { "status": "DENIED", "error_type": "RoleDenied" }
}
```

`error_type` is required on DENIED events so compliance and SOC teams can distinguish denial categories (role-based, cross-org, consent, session expiry, etc.). `error_message` is optional -- the category alone is often sufficient.

> **`phi_touched` on DENIED events:** Set to `false` because PHI was not actually accessed -- the request was blocked. `data_classification` still reflects what the *resource contains*, not what the actor saw. This distinction matters for compliance reporting: the resource is PHI, but no PHI was disclosed.

### Agent Action With No Nameable Authorizing Human (v2.1)

An agent presented credentials and no authorizing human could be resolved. v2.0 could not express this event: an agent actor required a `delegation` block, and the block required a human authorizer. v2.1 records it with `attribution.level: "unattributed"` and no `delegation` block. The `actor` still names the agent credential, so the event is not anonymous. The agent descriptor (`interface`, `vendor`, `model_family`) lives inside `delegation.acting.agent` and is therefore not available on these events.

**Enforced-tier denial.** The enforcing layer refused the call because attribution could not be established.

```json
{
  "actor": { "subject_id": "agent_cred_031", "subject_type": "agent" },
  "attribution": { "level": "unattributed", "method": "no_token_no_binding" },
  "action": { "type": "READ", "phi_touched": false, "data_classification": "PHI" },
  "resource": { "type": "Patient", "id": "pat_456", "patient_id": "pat_456" },
  "outcome": { "status": "DENIED", "error_type": "AttributionRequired" }
}
```

**Fail-open success.** The call proceeded without resolvable attribution because the deployment was configured to fail open. This is a successful agent tool call with no authorizing human, and it is the record an incident review needs.

```json
{
  "actor": { "subject_id": "agent_cred_031", "subject_type": "agent" },
  "attribution": { "level": "unattributed", "method": "fail_open" },
  "action": { "type": "READ", "phi_touched": true, "data_classification": "PHI" },
  "resource": { "type": "Patient", "id": "pat_456", "patient_id": "pat_456" },
  "outcome": { "status": "SUCCESS" }
}
```

Both shapes are valid only with the `attribution` block. An agent actor carrying neither `delegation` nor `attribution` is rejected, as it was in v2.0.

### Agent Action With a Delegation Block (v2.1)

Every event that carries `delegation` also carries `attribution`, with `level` set from the resolution path that produced the delegation block. Do not default it to `verified`.

```json
{
  "actor": { "subject_id": "agent_cred_009", "subject_type": "agent" },
  "attribution": { "level": "verified", "method": "id_jag" },
  "delegation": {
    "acting": { "subject_id": "agent_inst_4471", "subject_type": "agent", "agent": { "interface": "mcp" } },
    "authorizing": { "subject_id": "user_123", "subject_type": "human" },
    "delegation_type": "supervised",
    "agent_session_id": "agsess_01J9X0001"
  },
  "action": { "type": "READ", "phi_touched": true, "data_classification": "PHI" },
  "resource": { "type": "Patient", "id": "pat_456", "patient_id": "pat_456" },
  "outcome": { "status": "SUCCESS" }
}
```

---

## Anti-Patterns to Avoid

### ❌ Raw Paths in `route_template`

```json
// Bad
{ "route_template": "/patients/pat_123/notes/note_456" }

// Good
{ "route_template": "/patients/{patient_id}/notes/{note_id}" }
```

### ❌ PHI in Error Messages

```json
// Bad
{ "error_message": "Patient John Smith (DOB: 1990-01-15) not found." }

// Good
{ "error_message": "Patient not found." }
```

### ❌ Missing `patient_id` for PHI Actions

```json
// Bad - phi_touched is true but no patient_id
{
  "action": { "type": "READ", "phi_touched": true },
  "resource": { "type": "Note", "id": "note_456" }
}

// Good
{
  "action": { "type": "READ", "phi_touched": true },
  "resource": { "type": "Note", "id": "note_456", "patient_id": "pat_123" }
}
```

### ❌ Inconsistent Resource Types

```json
// Bad - inconsistent naming
{ "resource": { "type": "patient" } }      // lowercase
{ "resource": { "type": "PATIENT" } }      // uppercase
{ "resource": { "type": "Patients" } }     // plural

// Good - consistent PascalCase singular
{ "resource": { "type": "Patient" } }
```

