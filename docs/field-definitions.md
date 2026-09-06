# Field Definitions

This document defines the semantics for each field in the BH Audit Event schema (v2.1). Fields introduced by a later version are marked with that version; unmarked fields date from v1.0.

---

## Top-Level Fields

### `schema_version`

- **Type:** `string` (const `"2.1"`)
- **Required:** Yes
- **Purpose:** Declares which version of the audit schema this event conforms to. Enables consumers to route events to version-appropriate processors.

### `event_id`

- **Type:** `string` (format: `uuid`, exactly 36 characters)
- **Required:** Yes
- **Purpose:** Globally unique UUID identifier for this audit event.
- **Guidance:** Generate a UUIDv4 at event creation time. Do not reuse across retries.

### `timestamp`

- **Type:** `string` (ISO 8601 date-time)
- **Required:** Yes
- **Purpose:** UTC timestamp when the audited action occurred.
- **Guidance:** Use server-side timestamps, not client-provided values.

---

## `service` Object

Describes the service that generated the audit event.

| Field         | Type   | Required | Constraints       | Description                                      |
|---------------|--------|----------|-------------------|--------------------------------------------------|
| `name`        | string | Yes      | minLength: 1, maxLength: 128 | Canonical service name (e.g., `bh-intake-api`) |
| `environment` | string | No       | maxLength: 64     | Deployment environment (`prod`, `staging`, `dev`)|
| `version`     | string | No       | maxLength: 64     | Service version or build identifier              |

**Guidance:** Use consistent service names across your organization. The `name` field should match what appears in your service registry.

---

## `correlation` Object

Identifiers for correlating events across services and requests.

| Field        | Type   | Required | Constraints           | Description                                           |
|--------------|--------|----------|-----------------------|-------------------------------------------------------|
| `request_id` | string | No       | minLength: 1, maxLength: 256 | Unique identifier for the originating HTTP request |
| `trace_id`   | string | No       | minLength: 1, maxLength: 256 | Distributed tracing identifier (e.g., OpenTelemetry) |
| `session_id` | string | No       | minLength: 1, maxLength: 256 | User session identifier                              |

**Constraints:** When present, the correlation object must contain at least one property (`minProperties: 1`). Empty `{}` is not valid.

**Guidance:** Include `request_id` for HTTP-triggered events. Include `trace_id` if your infrastructure supports distributed tracing.

---

## `actor` Object

Describes who or what performed the action.

| Field          | Type     | Required | Constraints           | Description                                                  |
|----------------|----------|----------|-----------------------|--------------------------------------------------------------|
| `subject_id`   | string   | Yes      | minLength: 1, maxLength: 256 | Unique identifier for the actor                        |
| `subject_type` | string   | Yes      | enum: `human`, `service`, `agent` | Identity class of the authenticating identity (v2.0: `agent`) |
| `org_id`       | string   | No       | minLength: 1, maxLength: 128 | Organization/tenant identifier of the actor             |
| `owner_org_id` | string   | No       | minLength: 1, maxLength: 128 | Organization that owns the resource being accessed      |
| `roles`        | string[] | No       | maxItems: 25, items minLength: 1, maxLength: 64 | Roles held by the actor at time of access |

### `subject_type` Values

- **`human`**: A human user authenticated via your identity system.
- **`service`**: A service principal, background job, or machine-to-machine actor.
- **`agent`** (v2.0): A non-deterministic AI actor presenting its own credentials. An agent actor must carry a `delegation` block or, from v2.1, `attribution.level: "unattributed"`.

Since v2.0, `actor` is defined precisely as the *authenticating* identity: the identity whose credentials were presented to the target system. When an agent acts under a human's credentials, `actor` names the human and `delegation` names the agent.

### `owner_org_id` (v1.1)

Used for cross-organization access detection. When `actor.org_id != actor.owner_org_id`, the actor is accessing resources owned by a different organization. This is critical for multi-tenant behavioral health systems and HIPAA compliance queries.

**Guidance:**
- Use internal user IDs, not email addresses or names.
- Capture `roles` at time of access to support access review audits.
- Include `org_id` for multi-tenant systems.
- Include `owner_org_id` when the resource belongs to a different org than the actor.

---

## `delegation` Object (v2.0)

Records that the action was agent-mediated and who authorized it. Defined by [RFC 0001](rfc/RFC-0001-agent-attribution-github.md); its section 5 carries the full semantics. Its presence asserts the action was agent-mediated. Its absence asserts a direct, non-delegated action unless `attribution.level` is `unattributed`.

| Field                     | Type    | Required    | Constraints                  | Description |
|---------------------------|---------|-------------|------------------------------|-------------|
| `acting`                  | object  | Yes         | `subject_id`, `subject_type` (const `agent`), `agent` descriptor with required `interface` | The agent that performed the action |
| `authorizing`             | object  | Yes         | `subject_id`, `subject_type` (const `human`), optional `org_id` | The human whose intent the action represents. For sub-agent chains, always the root human |
| `delegation_type`         | string  | Yes         | enum: `supervised`, `autonomous`, `scheduled` | Human-oversight state at the time of the action |
| `agent_session_id`        | string  | Yes         | minLength: 1, maxLength: 256 | Correlates every action to its session lifecycle events |
| `chain_depth`             | integer | No          | minimum: 1, maximum: 32      | Depth 1 is an agent delegated directly by the authorizing human; depth 2 is a sub-agent |
| `parent_agent_session_id` | string  | Conditional | minLength: 1, maxLength: 256 | Session of the parent agent. Present if and only if `chain_depth >= 2` |

From v2.1, every event that carries `delegation` also carries `attribution`.

---

## `attribution` Object (v2.1)

States how this event's attribution was established. Defined by [RFC 0003](rfc/RFC-0003-attribution-assurance.md).

| Field    | Type   | Required | Constraints                 | Description |
|----------|--------|----------|-----------------------------|-------------|
| `level`  | string | Yes      | enum (see below)            | How strongly the attribution is known. Consumers reason over this field |
| `method` | string | No       | minLength: 1, maxLength: 64 | Forensic detail on the mechanism behind the level. Open vocabulary |

### `level` Values

Defined in `$defs/AttributionLevel` and referenced via `$ref: "#/$defs/AttributionLevel"`.

| Level | Meaning | Forgeable by the agent |
|---|---|---|
| `verified` | Derived from a token whose issuer asserted the identities | No |
| `bound` | Operator configuration maps a credential or session to an authorizing identity | No, but it is the operator's assertion and not proof of a human's involvement in this call |
| `asserted` | Supplied by the agent in the call itself | Yes |
| `unattributed` | An agent was involved and no authorizing human could be named. No `delegation` block is present | n/a |

There is no `unknown` level. A producer that cannot determine how it established an attribution accepted an identity it cannot vouch for, which is `asserted`. `unattributed` is a positive finding: resolution ran and produced no authorizing human.

### Ordering

The levels form a total order, weakest to strongest:

`unattributed` < `asserted` < `bound` < `verified`

Compare on position in this sequence, never on the serialized string. Lexical order of the four values is `asserted` < `bound` < `unattributed` < `verified`, which places the weakest level above `bound`, so a string comparison against a `bound` threshold admits the one value the threshold exists to exclude. The rank is a property of the specification and is not serialized. In SQL, express a threshold as set membership or a join against a rank table (see [query examples](query-examples.md#attribution-assurance-v21)).

### One level per event, reporting the weakest binding

A delegation block holds identities that may have been established by different mechanisms. `level` describes the block as a whole and reports the weakest mechanism that contributed to it.

### Conditional Rules (v2.1)

| Rule | Condition | Requirement |
|---|---|---|
| R1 | `delegation` present | `attribution` required, with `level` one of `verified`, `bound`, `asserted` |
| R2 | `level` is `unattributed` | `delegation` forbidden |
| R3 | `level` is `verified`, `bound`, or `asserted` | `delegation` required |
| R4 | `actor.subject_type` is `agent` | either `delegation` present or `level` is `unattributed` |
| OVERRIDE | `action.type` is `OVERRIDE` | `attribution` forbidden, in addition to the v2.0 prohibition on `delegation` |

### What presence and absence assert

| `delegation` | `attribution` | The event asserts |
|---|---|---|
| absent | absent | No agent was involved |
| absent | `level: unattributed` | An agent was involved and could not be attributed |
| present | `level: verified` / `bound` / `asserted` | An agent was involved, who authorized it, and how strongly that is known |
| present | absent | Invalid |
| absent | `level` other than `unattributed` | Invalid |

### `method` Values

Examples, not an enum. Producers should use names meaningful to their own resolution paths.

| `method` value | Typical level | Meaning |
|---|---|---|
| `id_jag` | `verified` | Identities carried by an ID-JAG token |
| `bearer_act_claim` | `verified` | Identities carried by a bearer token with a nested `act` claim |
| `operator_config` | `bound` | Operator configuration mapped the credential or session to the authorizing human |
| `call_metadata` | `asserted` | The agent supplied the attribution in the call |
| `no_token_no_binding` | `unattributed` | No token and no configured binding resolved an authorizing human |
| `fail_open` | `unattributed` | The call proceeded without resolvable attribution under a fail-open setting |

**Guidance:**
- Determine `level` from the resolution path actually used. Do not default it to `verified`.
- Emit `unattributed` on the denial and fail-open paths of an enforcing layer, which v2.0 could not represent.
- Validate R1 to R4 in the producer and raise a producer-side message. A JSON Schema validator reports the `not` and `anyOf` rules by echoing the whole instance.

---

## `action` Object

Describes what action was performed.

| Field                | Type    | Required | Constraints              | Description                                                      |
|----------------------|---------|----------|--------------------------|------------------------------------------------------------------|
| `type`               | string  | Yes      | enum (see below)         | Action category                                                  |
| `name`               | string  | No       | maxLength: 128           | Specific action name (e.g., `sign_bps`, `verify_insurance`)      |
| `phi_touched`        | boolean | No       |                          | Whether the action touched regulated PHI                         |
| `data_classification`| string  | No       | enum (see below)         | Data classification: `PHI`, `PII`, `NONE`, `UNKNOWN`             |

### `action.type` Enum

Defined in `$defs/ActionType` and referenced via `$ref: "#/$defs/ActionType"`.
Downstream consumers can derive type-safe allowlists from the single source of
truth in `$defs`.

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
| `OVERRIDE` | A human interrupting, cancelling, or reversing an agent action or session (v2.0) |
| `OTHER`  | Actions not covered by the above categories           |

### `phi_touched` and `data_classification`

- **`phi_touched`**: Boolean flag indicating whether the action actually accessed or modified Protected Health Information under HIPAA/42 CFR Part 2.
- **`data_classification`**: Classification of what the *resource contains*, regardless of whether it was actually accessed. Defined in `$defs/DataClassification` and referenced via `$ref: "#/$defs/DataClassification"`.

**On DENIED events:** Set `phi_touched: false` because PHI was not actually accessed (the request was blocked). Set `data_classification` to reflect what the resource contains (e.g., `"PHI"`), not what the actor saw. This distinction matters for compliance: the resource is PHI, but no PHI was disclosed.

**Guidance:**
- Set `phi_touched: true` for any action that reads, writes, or transmits patient clinical data.
- Default to `data_classification: "UNKNOWN"` if classification cannot be determined.

---

## `resource` Object

Describes the resource being acted upon.

| Field        | Type   | Required | Constraints           | Description                                                   |
|--------------|--------|----------|-----------------------|---------------------------------------------------------------|
| `type`       | string | Yes      | minLength: 1, maxLength: 128 | Resource type (e.g., `Patient`, `Note`, `Encounter`)    |
| `id`         | string | No       | minLength: 1, maxLength: 256 | Resource identifier                                     |
| `patient_id` | string | No       | minLength: 1, maxLength: 256 | Patient identifier, if applicable                       |

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

| Field            | Type    | Required | Constraints                       | Description                                    |
|------------------|---------|----------|-----------------------------------|------------------------------------------------|
| `method`         | string  | No       | enum: `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS` | HTTP method |
| `route_template` | string  | No       | maxLength: 512                    | URL template, not raw path                     |
| `status_code`    | integer | No       | minimum: 100, maximum: 599       | HTTP response status code                      |
| `client_ip`      | string  | No       | format: ipv4 or ipv6             | Client IP address (IPv4 or IPv6)               |
| `user_agent`     | string  | No       | maxLength: 512                    | User-Agent header value                        |

### `route_template` vs Raw Path

**Always use route templates, not raw paths.**

- `/patients/{patient_id}/notes/{note_id}`
- `/patients/pat_456/notes/note_999`

Raw paths may contain PHI or enable inference attacks.

---

## `outcome` Object

Describes the result of the action.

| Field           | Type   | Required | Constraints              | Description                                       |
|-----------------|--------|----------|--------------------------|---------------------------------------------------|
| `status`        | string | Yes      | enum: `SUCCESS`, `FAILURE`, `DENIED` | Result of the action                   |
| `error_type`    | string | Conditional | minLength: 1, maxLength: 128 | Error category (e.g., `Forbidden`, `NotFound`) |
| `error_message` | string | Conditional | maxLength: 500           | Sanitized error message                           |

### Status Values (v1.1)

`outcome.status` is defined in `$defs/OutcomeStatus` and referenced via
`$ref: "#/$defs/OutcomeStatus"`.

| Status    | Meaning                                        | `error_type`    | `error_message` |
|-----------|------------------------------------------------|-----------------|-----------------|
| `SUCCESS` | Action completed successfully                  | Not required    | Not required    |
| `FAILURE` | An operational error occurred                  | **Required**    | **Required**    |
| `DENIED`  | System correctly refused access (authz worked) | **Required**    | Optional        |

**`DENIED` design rationale:** A DENIED outcome means the authorization system worked as intended. Unlike FAILURE, it's not an error -- it's correct behavior. However, `error_type` is required because compliance officers and SOC analysts need to distinguish *why* access was denied:

| `error_type` value      | Meaning                                                  |
|--------------------------|----------------------------------------------------------|
| `RoleDenied`            | User lacks the required role                             |
| `CrossOrgAccessDenied`  | User from a different org attempted access               |
| `ConsentRequired`       | 42 CFR Part 2 consent not on file                        |
| `SessionExpired`        | Session/token no longer valid                            |
| `Forbidden`             | Generic authorization denial                             |

These are examples, not an enum -- producers should use descriptive names that are meaningful to their compliance and security teams. `error_message` is optional on DENIED because the category alone is often sufficient.

### Error Message Sanitization

**`error_message` must not contain PHI.**

- `"Access denied."`
- `"Resource not found."`
- ~~`"Patient John Smith not found."`~~
- ~~`"Cannot update note containing diagnosis: depression"`~~

---

## `integrity` Object

Optional fields for tamper-evident audit chaining.

| Field            | Type   | Required    | Constraints                  | Description                                           |
|------------------|--------|-------------|------------------------------|-------------------------------------------------------|
| `event_hash`     | string | No          | minLength: 1, maxLength: 256 | Hash of this event's content                          |
| `prev_event_hash`| string | No          | minLength: 1, maxLength: 256 | Hash of the previous event in the chain               |
| `hash_alg`       | string | Conditional | enum: `sha256`, `sha384`, `sha512` | Hash algorithm used                             |

### Dependency Rules (v1.1)

- If `event_hash` is present, `hash_alg` is required.
- If `prev_event_hash` is present, both `hash_alg` and `event_hash` are required.

**Guidance:** Integrity chaining is optional and implementation-dependent. Useful for high-assurance environments requiring tamper evidence.

---

## `metadata` Object

Flexible container for additional safe context.

- **Type:** Object with scalar values only (string, integer, number, boolean, null)
- **Required:** No
- **Constraints:** maxProperties: 20. No nested objects or arrays.

### Rules

1. **Must not contain PHI.**
2. **Values must be scalar** -- strings, integers, numbers, booleans, or null. Nested objects and arrays are rejected by the schema.
3. Use for operational context: export format, business reason codes, feature flags.
4. Keep keys consistent across services.

**Examples:**
```json
{
  "export_format": "pdf",
  "reason": "continuity_of_care",
  "record_count": 42
}
```

```json
{
  "feature_flag": "new_intake_flow",
  "client_version": "2.1.0"
}
```
