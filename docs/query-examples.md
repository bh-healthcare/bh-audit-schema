# Representative Audit Queries Supported by the Schema

This document demonstrates that the BH Audit Schema supports the most common compliance and operational audit queries out of the box. Each query maps directly to required or recommended fields in the schema.

## Core Compliance Queries

These queries represent the essential audit capabilities required for HIPAA compliance and operational security monitoring.

| Query | Schema Field(s) | Example Filter |
|-------|-----------------|----------------|
| Show all access to patient X in the last 90 days | `resource.patient_id` + `timestamp` | `WHERE resource.patient_id = 'X' AND timestamp >= NOW() - INTERVAL 90 DAY` |
| Show all actions by user Y in the last 30 days | `actor.subject_id` + `timestamp` | `WHERE actor.subject_id = 'Y' AND timestamp >= NOW() - INTERVAL 30 DAY` |
| Show all EXPORT actions | `action.type` | `WHERE action.type = 'EXPORT'` |
| Show all FAILED access attempts | `outcome.status` | `WHERE outcome.status = 'FAILURE'` |
| Show all access to Notes resources | `resource.type` | `WHERE resource.type = 'Note'` |

## Schema Field Coverage

The schema provides first-class support for the following query dimensions:

| Field | Purpose | Query Use Case |
|-------|---------|----------------|
| `resource.patient_id` | Patient-centric queries | HIPAA access reports, patient data audits |
| `actor.subject_id` | User activity audits | Insider threat detection, user access reviews |
| `action.type` | Action filtering | Export monitoring, login analysis |
| `outcome.status` | Success/failure filtering | Security incident detection |
| `resource.type` | Resource-type filtering | PHI category audits |
| `timestamp` | Time-range queries | Compliance reporting windows |

## Extended Query Examples

Beyond the core compliance queries, the schema supports sophisticated audit scenarios:

### PHI Access Monitoring

```sql
-- All PHI-touching actions in the last 24 hours
SELECT * FROM audit_events
WHERE action.phi_touched = true
  AND timestamp >= NOW() - INTERVAL 1 DAY;

-- All PHI exports by data classification
SELECT * FROM audit_events
WHERE action.type = 'EXPORT'
  AND action.data_classification = 'PHI';
```

### Actor Analysis

```sql
-- All actions by service accounts (non-human)
SELECT * FROM audit_events
WHERE actor.subject_type = 'service';

-- All actions by users with a specific role
SELECT * FROM audit_events
WHERE 'physician' = ANY(actor.roles);

-- Cross-organization access attempts
SELECT * FROM audit_events
WHERE actor.org_id != resource.owner_org_id;  -- if owner tracked
```

### Security Incident Detection

```sql
-- Failed login attempts by IP
SELECT http.client_ip, COUNT(*) as attempts
FROM audit_events
WHERE action.type = 'LOGIN'
  AND outcome.status = 'FAILURE'
GROUP BY http.client_ip
HAVING COUNT(*) > 5;

-- Failed exports of PHI (high-priority alert)
SELECT * FROM audit_events
WHERE action.type = 'EXPORT'
  AND outcome.status = 'FAILURE'
  AND action.phi_touched = true;
```

### Correlation and Tracing

```sql
-- All events for a specific request (distributed tracing)
SELECT * FROM audit_events
WHERE correlation.trace_id = 'abc123'
ORDER BY timestamp;

-- Session activity timeline
SELECT * FROM audit_events
WHERE correlation.session_id = 'session-xyz'
ORDER BY timestamp;
```

### Resource-Specific Audits

```sql
-- All access to a specific patient record
SELECT * FROM audit_events
WHERE resource.patient_id = 'patient-123'
ORDER BY timestamp DESC;

-- All modifications to clinical notes
SELECT * FROM audit_events
WHERE resource.type = 'Note'
  AND action.type IN ('CREATE', 'UPDATE', 'DELETE');
```

## Indexing Recommendations

For optimal query performance, consider indexing these fields in your data store:

| Priority | Field | Rationale |
|----------|-------|-----------|
| High | `timestamp` | All time-range queries |
| High | `resource.patient_id` | Patient-centric compliance reports |
| High | `actor.subject_id` | User activity audits |
| Medium | `action.type` | Action filtering |
| Medium | `outcome.status` | Failure detection |
| Medium | `resource.type` | Resource category reports |
| Low | `correlation.trace_id` | Distributed tracing lookups |

## Design Principles

This schema intentionally:

1. **Avoids payload logging** — No raw request/response bodies that might contain PHI
2. **Uses structured fields** — Enables SQL/NoSQL queries without regex parsing
3. **Separates identity from content** — `patient_id` is logged, but patient data is not
4. **Supports both human and machine actors** — `actor.subject_type` distinguishes users from services
5. **Enables tamper detection** — Optional `integrity` block for hash chaining

## Compliance Alignment

These query capabilities directly support:

- **HIPAA § 164.312(b)** — Audit controls for information system activity
- **HIPAA § 164.308(a)(1)(ii)(D)** — Information system activity review
- **42 CFR Part 2** — Substance use disorder record access tracking
- **SOC 2 CC6.1** — Logical access security audit trails

---

*This document serves as evidence that the BH Audit Schema is operationally complete and queryable for real-world compliance scenarios.*

