# Controls Mapping

This document maps the BH Audit Event schema (v1.1) to HIPAA Security Rule, SOC 2, and 42 CFR Part 2 control objectives. It is intended as an **engineering reference**, not legal advice.

> **Disclaimer:** This document provides engineering mappings only. It does not constitute legal advice, compliance certification, or guarantee of regulatory compliance. Organizations must conduct their own compliance assessments with qualified professionals.

---

## HIPAA Security Rule Mapping

### §164.312(b) -- Audit Controls

*"Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use ePHI."*

| Schema Field | How It Supports This Control |
|---|---|
| `event_id` (v1.1: UUID enforced) | Uniquely identifies every auditable action |
| `timestamp` (format: date-time) | Records when each action occurred |
| `actor.subject_id` | Records who performed the action |
| `action.type` (enum) | Categorizes what action was performed |
| `resource.type`, `resource.id` | Identifies what resource was acted upon |
| `resource.patient_id` | Links actions to specific patient records |
| `outcome.status` (v1.1: SUCCESS/FAILURE/DENIED) | Records whether the action succeeded, failed, or was denied |
| `action.phi_touched` | Flags actions that touched protected health information |
| `action.data_classification` | Classifies sensitivity level of the data involved |

**v1.1 additions:** UUID enforcement ensures event uniqueness across systems. DENIED status distinguishes authorization denials from operational failures, enabling accurate access audit reports.

### §164.312(a)(1) -- Access Control

*"Implement technical policies and procedures for electronic information systems that maintain ePHI to allow access only to those persons or software programs that have been granted access rights."*

| Schema Field | How It Supports This Control |
|---|---|
| `outcome.status: "DENIED"` (v1.1) | Records when access control policies blocked a request |
| `outcome.error_type` (v1.1: required on DENIED) | Categorizes the denial reason (RoleDenied, CrossOrgAccessDenied, ConsentRequired) |
| `actor.roles` | Records role context at time of access |
| `actor.org_id` | Records which organization the actor belongs to |
| `actor.owner_org_id` (v1.1) | Records which organization owns the resource -- enables cross-org access detection |

**v1.1 additions:** `DENIED` with required `error_type` gives compliance teams queryable denial categories. `owner_org_id` enables detection of cross-organization access attempts in multi-tenant environments.

### §164.312(a)(2)(i) -- Unique User Identification

*"Assign a unique name and/or number for identifying and tracking user identity."*

| Schema Field | How It Supports This Control |
|---|---|
| `actor.subject_id` (minLength: 1) | Unique actor identifier -- every event is attributable |
| `actor.subject_type` (enum: human/service) | Distinguishes human users from service principals |

**v1.1 additions:** `minLength: 1` prevents empty actor IDs that would make events unattributable.

### §164.308(a)(1)(ii)(D) -- Information System Activity Review

*"Implement procedures to regularly review records of information system activity, such as audit logs, access reports, and security incident tracking reports."*

| Schema Field | How It Supports This Control |
|---|---|
| `correlation.request_id`, `trace_id`, `session_id` | Enables correlation across distributed systems for activity review |
| `http.method`, `http.route_template`, `http.status_code` | Provides HTTP-level context for web-triggered actions |
| `metadata` (v1.1: scalar-only, maxProperties: 20) | Safe operational context without PHI leakage risk |

**v1.1 additions:** Correlation fields now require `minLength: 1` (no empty strings). Metadata restricted to scalar values prevents nested PHI from entering audit logs. `maxProperties: 20` bounds event size.

### §164.308(a)(5)(ii)(C) -- Log-in Monitoring

*"Procedures for monitoring log-in attempts and reporting discrepancies."*

| Schema Field | How It Supports This Control |
|---|---|
| `action.type: "LOGIN"` | Dedicated action type for authentication events |
| `outcome.status` | Records login success, failure, or denial |
| `outcome.error_type` (v1.1: required on FAILURE) | Categorizes why the login failed |
| `http.client_ip` (v1.1: IPv4 + IPv6) | Source IP for failed login correlation |
| `actor.subject_id` | Which account was targeted |

**v1.1 additions:** FAILURE requires `error_type` so login failure reasons are always recorded. `client_ip` supports both IPv4 and IPv6.

### §164.312(c)(1) -- Integrity

*"Implement policies and procedures to protect ePHI from improper alteration or destruction."*

| Schema Field | How It Supports This Control |
|---|---|
| `integrity.event_hash` | Hash of event content for tamper detection |
| `integrity.prev_event_hash` | Links to previous event for chain verification |
| `integrity.hash_alg` (v1.1: enum sha256/sha384/sha512) | Specifies the hash algorithm used |

**v1.1 additions:** `hash_alg` constrained to strong algorithms only. `dependentRequired` ensures `event_hash` always has a corresponding `hash_alg`, and `prev_event_hash` requires a complete chain context.

---

## SOC 2 Trust Services Criteria Mapping

### CC6.1 -- Logical and Physical Access Controls

*"The entity implements logical access security software, infrastructure, and architectures over protected information assets."*

| Schema Support | Fields |
|---|---|
| Access logging | `actor`, `action`, `resource`, `outcome` |
| Denial tracking (v1.1) | `outcome.status: "DENIED"`, `outcome.error_type` |
| Cross-org detection (v1.1) | `actor.org_id` vs `actor.owner_org_id` |

### CC6.3 -- Role-Based Access

*"The entity authorizes, modifies, or removes access to data based on roles and responsibilities."*

| Schema Support | Fields |
|---|---|
| Role capture | `actor.roles` (v1.1: bounded, non-empty items) |
| Role-based denial tracking | `outcome.error_type: "RoleDenied"` |
| Access review queries | `actor.subject_id` + `actor.roles` + `resource.patient_id` |

### CC7.2 -- System Monitoring

*"The entity monitors system components and the operation of those components for anomalies that are indicative of malicious acts, natural disasters, and errors."*

| Schema Support | Fields |
|---|---|
| Failure pattern detection | `outcome.status: "FAILURE"` + `outcome.error_type` |
| Denial pattern detection (v1.1) | `outcome.status: "DENIED"` + `outcome.error_type` |
| Distributed tracing | `correlation.trace_id`, `correlation.request_id` |
| Client identification | `http.client_ip`, `http.user_agent` |

### CC7.3 -- Security Event Evaluation

*"The entity evaluates detected security events and determines whether they could reasonably be expected to impact the entity's ability to achieve its objectives."*

| Schema Support | Fields |
|---|---|
| Event categorization | `action.type`, `outcome.status`, `outcome.error_type` |
| PHI impact assessment | `action.phi_touched`, `action.data_classification` |
| Patient scope | `resource.patient_id` |
| Incident correlation | `correlation.*` fields |

---

## 42 CFR Part 2 Context

42 CFR Part 2 governs confidentiality of substance use disorder (SUD) patient records. It imposes stricter requirements than general HIPAA for behavioral health data.

### §2.16 -- Security for Records

*"Programs must have formal policies and procedures to protect the security of SUD records."*

| Schema Field | How It Supports This |
|---|---|
| `action.data_classification: "PHI"` | Identifies events touching regulated data |
| `action.phi_touched: true` | Flags SUD record access explicitly |
| `resource.patient_id` | Tracks which patient's SUD records were accessed |
| `outcome.status: "DENIED"` (v1.1) | Records when SUD record access was blocked |
| `outcome.error_type: "ConsentRequired"` (v1.1) | Indicates consent-based denial (Part 2 specific) |
| `actor.owner_org_id` (v1.1) | Detects cross-organization SUD record access attempts |
| `metadata` (v1.1: scalar-only) | Prevents raw SUD clinical content from entering audit logs |

### §2.13(a) -- Patient Consent

*"Disclosures of SUD records require documented patient consent."*

The schema provides the audit trail for consent-gated access but does not model consent itself. Consent tracking (consent_id, consent_purpose, break-the-glass) is planned for a future schema version. For now, producers should use `outcome.error_type: "ConsentRequired"` when access is denied due to missing consent.

---

## What the Schema Does NOT Do

| Concern | Status |
|---|---|
| Guarantee regulatory compliance | Not in scope -- this is an engineering tool |
| Replace a compliance program | Not in scope |
| Model consent documents | Planned for future version |
| Enforce retention periods | Implementer responsibility (see sink configuration) |
| Provide legal advice | Not in scope |
| Detect PHI in free-text fields | Not in scope -- relies on producer discipline and allowlists |

---

## Implementer Checklist

### Minimum Viable Audit Implementation

- [ ] Emit events for all PHI-touching operations
- [ ] Populate all required fields (schema_version, event_id, timestamp, service, actor, action, resource, outcome)
- [ ] Set `action.phi_touched` and `action.data_classification` accurately
- [ ] Include `resource.patient_id` on patient-specific actions
- [ ] Populate `actor.roles` at time of access
- [ ] Record DENIED outcomes with descriptive `error_type`
- [ ] Store events in a durable, queryable sink
- [ ] Protect audit logs from unauthorized modification

### Enhanced Implementation

- [ ] Populate `actor.owner_org_id` for multi-tenant/cross-org scenarios
- [ ] Implement correlation across services (`trace_id`, `request_id`)
- [ ] Build automated alerting on DENIED and FAILURE patterns
- [ ] Implement integrity chaining (event_hash, prev_event_hash, hash_alg)
- [ ] Establish retention policies (HIPAA: minimum 6 years recommended)
- [ ] Conduct regular access reviews (quarterly recommended)
- [ ] Validate emitted events against the v1.1 schema in CI


---

## v2.0 deltas -- AI agent attribution

The v2.0 schema (RFC 0001) introduces a multi-actor attribution model. The deltas below are additive to the v1.1 mappings above; they describe new evidence available *only* when the producer emits v2.0 events with a populated `delegation` object.

### HIPAA §164.312(d) -- Person or Entity Authentication

The strongest new hook. The provision requires verifying that a person or entity seeking access is who they claim to be. Agent-mediated access under human credentials is precisely the scenario where the authenticated identity and the acting entity diverge. The pair (`actor`, `delegation.acting`) is the record of that divergence -- `actor` documents which credential was presented, `delegation.acting` documents which entity actually exercised the authenticated access.

### HIPAA §164.312(b) -- Audit Controls

Extended: the recorded activity now distinguishes the performing entity from the credentialed identity. `delegation.delegation_type` records the supervision state at the time of each action (`supervised` / `autonomous` / `scheduled`), making oversight a queryable property rather than implicit context.

### 42 CFR Part 2 §2.13 / §2.16

Agent access to SUD records inherits all existing protections. Additionally, `delegation.authorizing` makes consent accountability attach to a *human* even when an agent performed the access. `delegation.acting.agent.interface == "ui_driving"` flags the access pattern with the weakest technical controls and merits heightened review.

### SOC 2 CC6.1 / CC7.2

Agent session monitoring, override-rate analysis, and autonomous-action volume become queryable monitoring dimensions. Lifecycle events (`CREATE` / `UPDATE` of `AgentSession`) bound every agent action to a reviewable session; the `OVERRIDE` action records human interventions for compliance review.

### NIST AI RMF (GOVERN, MAP) and ISO/IEC 42001 §8.3

The delegation record is the operational evidence layer for AI governance claims: who authorized which agent to do what, under what supervision mode, with what override history. The mapping document states this as *supporting evidence*, not certification.

### Implementer checklist additions for v2.0

- [ ] Route agent traffic through an Enforced or Instrumented emission path (RFC §11) before claiming v2.0 attribution
- [ ] Emit `AgentSession` lifecycle events at session start (`CREATE`) and end (`UPDATE`, `action.name: agent_session_end`)
- [ ] Record `delegation.delegation_type` accurately for every agent action; treat unknown supervision state as `autonomous`
- [ ] For sub-agents, populate both `chain_depth >= 2` and `parent_agent_session_id`
- [ ] For human overrides, emit `OVERRIDE` with `resource.type: AgentSession` and `resource.id` set to the session being overridden
- [ ] Never place prompt content, model outputs, screenshots, or reasoning traces in events; store such artifacts separately and reference them by opaque ID in `metadata`
- [ ] Review queries of the form "all actions by user Y" -- where the intent is "performed personally by Y," extend with `delegation IS NULL` or the store equivalent

---

## v2.1 deltas -- attribution assurance

The v2.1 schema (RFC 0003) adds an `attribution` object stating how an event's attribution was established, and makes the case of an agent with no nameable authorizing human expressible. The deltas below are additive to the v2.0 mappings above. They are stated conservatively: `attribution.level` records the mechanism that produced an attribution. It does not verify anything itself, and it does not set a floor. Where the floor sits is a deployment policy decision.

### HIPAA §164.312(d) -- Person or Entity Authentication

v2.0 recorded which identity authenticated and which human authorized. v2.1 records how the authorizing identity became known: from a token whose issuer asserted it (`verified`), from operator configuration (`bound`), or from the agent's own claim (`asserted`). A reviewer evaluating whether an agent-mediated access was tied to an authenticated person can now distinguish an issuer-asserted binding from an honor-system one. Under v2.0 the two produced identical records.

### HIPAA §164.312(b) -- Audit Controls

Two events that previously left no valid record now do. An enforcing layer's denial of an agent call it could not attribute, and a call that proceeded under a fail-open setting without resolvable attribution, are both recordable as `attribution.level: "unattributed"`. The denial rate of an enforcing layer becomes measurable, which is the main signal that the layer is misconfigured or that an agent is reaching a tool without credentials.

### HIPAA §164.308(a)(1)(ii)(D) -- Information System Activity Review

The distribution of `attribution.level` across a service answers whether a deployment claiming token-based attribution is resolving identities from tokens. A review that reads only the delegation block cannot distinguish the two. See [query examples](query-examples.md#attribution-assurance-v21).

### 42 CFR Part 2 §2.13 / §2.16

Consent accountability for an agent-mediated SUD record access attaches to `delegation.authorizing` as before. v2.1 adds the strength of that attachment. An access to Part 2 records recorded at `asserted` names a human on the agent's word alone, and an access recorded as `unattributed` names none. Both are review items under a program's security policies. The schema records the state and does not judge it.

### SOC 2 CC6.1 / CC7.2

`attribution.level` is a monitoring dimension. An `unattributed` event on a controlled path, or a rising share of `asserted` events on a path claimed to be token-resolved, is an anomaly a monitoring control can alert on.

### Implementer checklist additions for v2.1

- [ ] Emit `attribution` on every event that carries `delegation`, with `level` determined from the resolution path actually used; never default it to `verified`
- [ ] On the denial and fail-open paths of an enforcing layer, emit `attribution.level: "unattributed"` with no `delegation` block
- [ ] Where a threshold on `attribution.level` is enforced or queried, compare on the RFC 0003 section 4.4 rank, never on the string value
- [ ] Alert on `attribution.level = 'unattributed'` for paths that are expected to be fully attributed
- [ ] Validate R1 to R4 in the producer and surface a producer-side error message; a JSON Schema validator reports the `not` and `anyOf` rules by echoing the whole instance
