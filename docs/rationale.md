# Rationale

This document explains why the BH Audit Event schema exists and the problems it aims to solve.

---

## Why Behavioral Health Needs Strong Audit Standards

### The Sensitivity Challenge

Behavioral health data is among the most sensitive categories of health information:

- **Therapy notes** containing deeply personal disclosures
- **Substance use records** protected by 42 CFR Part 2
- **Mental health diagnoses** that carry significant stigma
- **Crisis intervention records** with life-safety implications

A breach or unauthorized access to this data can cause profound harm to patients—damage to relationships, employment discrimination, and personal distress that may exacerbate the very conditions being treated.

### The Regulatory Landscape

Organizations handling behavioral health data face a complex regulatory environment:

| Regulation           | Scope                                                      |
|----------------------|------------------------------------------------------------|
| HIPAA Security Rule  | Access controls, audit controls, integrity                 |
| 42 CFR Part 2        | Substance use disorder records (stricter than HIPAA)       |
| State Mental Health Laws | Varies by jurisdiction                                 |
| Payer Requirements   | Contractual audit obligations                              |

These regulations share a common requirement: **organizations must maintain audit trails of who accessed what data and when**.

### The Implementation Gap

Despite clear requirements, many behavioral health organizations struggle with audit logging:

- **Small organizations** lack dedicated security engineering resources
- **Legacy systems** have inconsistent or missing audit capabilities
- **Custom implementations** create fragmented, non-portable audit formats
- **Vendor diversity** means no common audit event structure across tools

The result: organizations either fail to meet audit requirements or invest significant resources reinventing audit logging for each system.

---

## Why Schema-First Standards Help

### The Contract Approach

This schema defines a **contract** that:

1. **Producers** (applications, services) agree to emit
2. **Consumers** (audit sinks, SIEM systems, review tools) agree to accept

With a shared contract:
- Implementations become interchangeable
- Tooling can be reused across organizations
- Validation is straightforward
- Documentation is centralized

### Benefits for Different Stakeholders

| Stakeholder              | Benefit                                                    |
|--------------------------|------------------------------------------------------------|
| **Developers**           | Clear specification to implement against                   |
| **Security Teams**       | Consistent format for analysis and alerting                |
| **Compliance Officers**  | Documented mapping to control objectives                   |
| **Auditors**             | Predictable structure for review                           |
| **Vendors**              | Standard to support rather than custom integrations        |

### Reducing Barriers for Small Organizations

Large healthcare organizations can afford custom audit infrastructure. Small and mid-sized behavioral health providers often cannot.

This schema aims to:
- Provide a production-ready starting point
- Enable adoption of community tooling
- Reduce the expertise required for compliant implementation
- Allow focus on care delivery rather than infrastructure

---

## Design Philosophy

### Engineering Standard, Not Legal Advice

This project provides **engineering primitives** that support compliance objectives. It does not:

- Guarantee compliance with any regulation
- Provide legal interpretation of requirements
- Replace professional compliance guidance

Organizations must still assess their specific regulatory obligations and implement appropriate controls.

### PHI Safety by Default

The schema is designed so that **audit events are useful without containing raw PHI**. This means:

- Audit logs don't become a secondary PHI repository
- Log aggregation and analysis tools don't require PHI access
- Breach scope is reduced if audit systems are compromised

### Implementation Flexibility

The schema defines **what** to log, not **how** to implement logging. Organizations can:

- Use any programming language or framework
- Choose any storage backend (databases, log aggregators, SIEM)
- Implement synchronous or asynchronous logging
- Add organization-specific fields via `metadata`

### Versioned and Evolvable

Healthcare technology evolves. The schema supports evolution through:

- Explicit `schema_version` field in every event
- Semantic versioning for backward compatibility
- Immutable version history for long-term retention
- Clear migration paths between versions

---

## Relationship to Other Projects

### bh-fastapi-audit

[bh-fastapi-audit](https://github.com/bh-healthcare/bh-fastapi-audit) is a reference implementation that emits audit events conforming to this schema. It demonstrates:

- How to integrate audit logging into a FastAPI application
- How to populate schema fields from HTTP context
- How to handle PHI classification at the application layer

### bh-data-lake-reference

[bh-data-lake-reference](https://github.com/bh-healthcare/bh-data-lake-reference) provides reference architectures for storing and querying audit events. It addresses:

- Durable storage patterns
- Retention policy implementation
- Query patterns for access review
- Integration with cloud services

---

## What This Schema Is Not

### Not a Complete Compliance Solution

Audit logging is one component of a compliance program. Organizations also need:

- Access controls
- Encryption
- Training
- Policies and procedures
- Incident response
- Business associate agreements
- Regular risk assessments

### Not Application-Specific

This schema is intentionally generic. It does not include:

- EHR-specific fields
- Billing system structures
- Appointment scheduling details
- Clinical workflow concepts

Application-specific context belongs in:
- `action.name` (specific action identifiers)
- `resource.type` (domain-specific resource types)
- `metadata` (safe additional context)

### Not Prescriptive About Infrastructure

The schema does not require:

- Specific databases or storage systems
- Particular cloud providers
- Specific log aggregation tools
- Real-time vs. batch processing

These are implementation decisions left to adopters.

---

## Getting Started

1. **Review the schema**: [schema/audit_event.schema.json](../schema/audit_event.schema.json)
2. **Study the examples**: [examples/1.0/](../examples/1.0/)
3. **Understand the fields**: [docs/field-definitions.md](./field-definitions.md)
4. **Plan your implementation**: Consider using [bh-fastapi-audit](https://github.com/bh-healthcare/bh-fastapi-audit) as a reference
5. **Contribute**: Issues and pull requests are welcome

---

## Summary

The BH Audit Event schema exists to:

| Goal                                      | Approach                                    |
|-------------------------------------------|---------------------------------------------|
| Reduce implementation burden              | Provide a ready-to-use specification        |
| Enable interoperability                   | Define a common contract                    |
| Support compliance objectives             | Map to audit control requirements           |
| Protect patient privacy                   | Design for PHI safety by default            |
| Serve the behavioral health community     | Open source, vendor-neutral, practical      |

