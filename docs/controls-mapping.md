# Controls Mapping

This document maps the BH Audit Event schema to common compliance control objectives. It is intended as an **engineering reference**, not legal advice.

> **Disclaimer:** This document provides engineering mappings only. It does not constitute legal advice, compliance certification, or guarantee of regulatory compliance. Organizations must conduct their own compliance assessments with qualified professionals.

---

## Overview

The BH Audit Event schema is designed to support the following control objectives:

| Objective                | Schema Support | Implementer Responsibility          |
|--------------------------|----------------|-------------------------------------|
| Auditability             | ✅ Full        | Emit events, store durably          |
| Traceability             | ✅ Full        | Populate correlation fields         |
| Access Review            | ✅ Full        | Query by actor, resource, time      |
| Integrity                | ⚡ Optional    | Implement hash chaining             |
| Retention                | 🔶 Partial     | Configure sink retention policies   |
| Incident Investigation   | ✅ Full        | Ensure correlation IDs are populated|

---

## Auditability / Traceability

**Objective:** Maintain a complete, queryable record of access to sensitive data.

### What the Schema Enables

| Field                  | Purpose                                               |
|------------------------|-------------------------------------------------------|
| `event_id`             | Unique identifier for each audit event                |
| `timestamp`            | When the action occurred                              |
| `actor.subject_id`     | Who performed the action                              |
| `action.type`          | What type of action was performed                     |
| `resource.type`        | What type of resource was accessed                    |
| `resource.id`          | Which specific resource was accessed                  |
| `resource.patient_id`  | Which patient's data was involved                     |
| `outcome.status`       | Whether the action succeeded or failed                |

### Implementer Responsibilities

- [ ] Emit audit events for all PHI-touching operations
- [ ] Store audit events in a durable, queryable sink
- [ ] Ensure events are written before returning success to the client (or use reliable async delivery)
- [ ] Protect audit logs from unauthorized modification

---

## Access Review

**Objective:** Enable periodic review of who accessed what data and when.

### What the Schema Enables

| Field                  | Enables Query                                         |
|------------------------|-------------------------------------------------------|
| `actor.subject_id`     | "What did user X access?"                             |
| `actor.roles`          | "What actions did role Y perform?"                    |
| `resource.patient_id`  | "Who accessed patient Z's data?"                      |
| `timestamp`            | "What happened in time range T?"                      |
| `action.phi_touched`   | "Show all PHI access events"                          |
| `outcome.status`       | "Show all failed access attempts"                     |

### Implementer Responsibilities

- [ ] Populate `actor.roles` at time of access (not just at authentication)
- [ ] Populate `resource.patient_id` for all patient-specific actions
- [ ] Build or adopt tooling for access review queries
- [ ] Establish access review cadence (e.g., quarterly)

---

## Integrity / Tamper Evidence

**Objective:** Detect unauthorized modification of audit records.

### What the Schema Enables

| Field                   | Purpose                                              |
|-------------------------|------------------------------------------------------|
| `integrity.event_hash`  | Hash of the event content                            |
| `integrity.prev_event_hash` | Hash of the previous event (chaining)            |
| `integrity.hash_alg`    | Algorithm used for hashing                           |

### Implementer Responsibilities

- [ ] Implement hash computation at event emission time
- [ ] Store hashes in a tamper-evident manner (separate from event content)
- [ ] Build verification tooling to detect chain breaks
- [ ] Consider external anchoring (e.g., timestamping services) for high-assurance needs

> **Note:** The `integrity` object is optional. Many organizations rely on infrastructure-level protections (immutable storage, write-once logs) rather than application-level chaining.

---

## Retention

**Objective:** Retain audit records for required periods, then dispose appropriately.

### What the Schema Enables

| Field              | Purpose                                                   |
|--------------------|-----------------------------------------------------------|
| `timestamp`        | Determines event age for retention calculations           |
| `action.type`      | May influence retention rules (e.g., exports retained longer) |
| `schema_version`   | Enables version-aware retention policies                  |

### Implementer Responsibilities

- [ ] Configure retention policies in your audit sink (not in this schema)
- [ ] Implement retention rules based on regulatory requirements
- [ ] Ensure retention applies to all copies (primary, backups, replicas)
- [ ] Document retention periods and deletion procedures

> **Note:** Retention periods are organization-specific and regulatory-dependent. This schema does not prescribe retention periods.

---

## Incident Investigation / Correlation

**Objective:** Enable rapid investigation of security incidents and anomalies.

### What the Schema Enables

| Field                    | Purpose                                              |
|--------------------------|------------------------------------------------------|
| `correlation.request_id` | Correlate events within a single request             |
| `correlation.trace_id`   | Correlate events across distributed services         |
| `correlation.session_id` | Correlate events within a user session               |
| `http.client_ip`         | Identify source of requests                          |
| `http.user_agent`        | Identify client software                             |
| `outcome.error_type`     | Categorize failures for pattern detection            |

### Implementer Responsibilities

- [ ] Populate correlation fields in all events
- [ ] Integrate with distributed tracing infrastructure
- [ ] Build alerting on suspicious patterns (e.g., high failure rates, unusual access patterns)
- [ ] Establish incident response procedures that leverage audit data

---

## Regulatory Context

This schema is designed to support (but does not guarantee compliance with):

| Regulation          | Relevant Schema Features                                     |
|---------------------|--------------------------------------------------------------|
| HIPAA Security Rule | Access logging, audit controls, integrity controls           |
| 42 CFR Part 2       | Substance use disorder record access tracking                |
| State BH Laws       | Behavioral health-specific access logging                    |
| SOC 2               | Access logging, change tracking, incident response support   |

### Important Limitations

This schema:
- **Does not** guarantee compliance with any regulation
- **Does not** replace a compliance program
- **Does not** provide legal advice
- **Does** provide engineering primitives that support compliance objectives

---

## Checklist for Implementers

### Minimum Viable Audit Implementation

- [ ] Emit events for all PHI-touching operations
- [ ] Populate all required fields
- [ ] Store events in durable, queryable storage
- [ ] Protect audit logs from unauthorized access
- [ ] Implement basic access review queries

### Enhanced Implementation

- [ ] Populate all optional fields where applicable
- [ ] Implement correlation across services
- [ ] Build automated alerting on suspicious patterns
- [ ] Implement integrity chaining
- [ ] Establish retention automation
- [ ] Conduct regular access reviews

