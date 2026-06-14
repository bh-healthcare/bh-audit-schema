# FHIR R5 AuditEvent for AI Agent Attribution: Gap Analysis and Proposed Profile

**Status:** Working draft, companion to RFC 0001
**Scope:** Expressing the bh-audit-schema v2.0 agent attribution model as a profile of FHIR R5 AuditEvent
**Date:** June 2026

---

## 1. Thesis

FHIR R5 AuditEvent has the structural bones for multi-participant audit events but lacks the semantics, vocabulary, and constraints needed to attribute AI-agent-mediated actions. The gap is precise and narrow, which is what makes it closeable by profile rather than by a competing standard.

The sharpest expression of the gap comes from FHIR itself. The specification divides responsibilities: Provenance covers *generation* of entities, AuditEvent covers *usage*. FHIR's delegation primitive, `Provenance.agent.onBehalfOf`, lives on the generation side. `AuditEvent.agent` has no equivalent element. AI agent access auditing is a usage problem -- who touched this record, under whose credentials, on whose behalf -- so the delegation primitive is absent exactly where agentic healthcare deployments need it.

This document does two things: identifies what R5 AuditEvent cannot express for agent attribution (Section 2), and closes each gap with a profile that constrains existing elements where they suffice and adds extensions only where no element exists (Sections 3-5). The source contract is bh-audit-schema v2.0; the profile is its FHIR interoperability expression. A working translator demonstrates the mapping end-to-end (Section 6).

## 2. Gap analysis: what R5 AuditEvent cannot express

| # | Gap | Detail | Closeable by |
|---|---|---|---|
| G1 | No attribution-role semantics | `agent` is 1..* and `agent.type` describes "how agent participated," but no standard vocabulary distinguishes the authenticating identity (whose credentials were presented), the acting identity (what performed the action), and the authorizing identity (whose intent it represents) | Profile: required `agent.type` codes + slicing |
| G2 | `requestor` cannot carry the split | A single boolean per agent marks the initiator. When a human authorized work and an agent performed it under that human's credentials, "the requestor" is ambiguous by construction; the element predates delegated non-human actors | Profile: fixed `requestor` values per attribution slice |
| G3 | No delegation element | `Provenance.agent.onBehalfOf` expresses delegation for resource generation; `AuditEvent.agent` has no counterpart for usage auditing | Profile slicing makes the relationship explicit via paired agent slices; no new element needed once G1 is closed |
| G4 | No supervision state | Nothing expresses whether a human was actively observing (supervised), absent (autonomous), or never present (scheduled) at the time of the action -- the first question a compliance reviewer asks about an agent action | Extension: `delegation-type` |
| G5 | No agent session or chain linkage | No convention ties an agent's actions to a reviewable session, and nothing models sub-agent chains (an agent spawning agents) | Extensions: `agent-session-id`, `chain-depth`, `parent-agent-session-id` |
| G6 | No agent descriptor constraints | `agent.who` can reference a Device, so an AI agent is *representable*, but nothing requires recording which model, version, harness, or interaction surface acted. An attribution record that cannot say which agent acted is weak evidence | Complex extension: `agent-descriptor` (interface required) |
| G7 | No authorization-denial outcome | `outcome.code` values grade success and failure severity. "The system correctly refused access" -- the DENIED semantic critical for HIPAA access reports and 42 CFR Part 2 consent denials -- has no code; mapping it to a failure grade conflates correct authorization behavior with operational error | Profile: required `outcome.detail` coding when DENIED |
| G8 | No PHI-minimization discipline for agentic content | `entity.query`, `outcome` text, and `entity.detail` values can carry arbitrary content. Nothing prohibits prompts, model outputs, screenshots, or reasoning traces -- the agentic equivalents of request bodies -- from entering the audit record | Profile invariants: prohibited content classes, scalar-only detail values |
| G9 | No validation requiring attribution completeness | Nothing makes an agent-performed event invalid when the authorizing human is missing | Profile invariant: acting slice present implies authorizing slice present |

What is deliberately *not* claimed as a gap: multi-agent structure (exists), AI actors as references (Device works), patient linkage (R5 added a first-class `patient` element, which this profile uses), or purpose-of-use (R5 `authorization` covers it). The profile builds on these rather than duplicating them.

## 3. The profile in one view

Three agent slices, discriminated on `agent.type` from a new `attribution-role` CodeSystem:

| Slice | `agent.type` code | `agent.who` | `requestor` | Cardinality |
|---|---|---|---|---|
| authenticating | `authenticating-identity` | the identity whose credentials were presented | `false` | 0..1 (required for agentic events) |
| acting | `acting-identity` | the agent instance (Device or opaque identifier reference), carries `agent-descriptor` extension | `false` | 0..1 (presence asserts agent-mediated) |
| authorizing | `authorizing-identity` | the human whose intent the action represents | `true` | 0..1 (required when acting present) |
| direct | `direct` | the human or service that acted directly | `true` | the collapse case: 1..1 when no acting slice |

The collapse property carries over from the source schema: a direct human action is a single `direct` agent and the resource looks like any conventional AuditEvent. The attribution machinery appears only when attribution actually split.

**Design note on `requestor`:** the authorizing identity carries `requestor = true`; authenticating and acting carry `false`. `requestor` historically marks the initiator, and in a delegated action it is the human's intent that initiates -- the agent executes. This assignment also means legacy consumers querying `requestor = true` surface the accountable human rather than the agent, which is the correct default for access review. The alternative (acting as requestor) was considered and rejected for that reason.

**Invariants (the profile's enforcement layer):**

- inv-1: if an `acting-identity` slice is present, an `authorizing-identity` slice is present (no agent action without an identifiable authorizing human)
- inv-2: if an `acting-identity` slice is present, an `authenticating-identity` slice is present
- inv-3: `parent-agent-session-id` present implies `chain-depth` >= 2, and `chain-depth` >= 2 implies `parent-agent-session-id` present
- inv-4: when `outcome` represents an authorization denial, `outcome.detail` contains the `denied` coding and an error-type coding
- inv-5: `entity.detail` values are scalar; no element carries prompt content, model output, rendered screen context, or reasoning traces (enforced as profile documentation plus reviewable constraint; FHIRPath cannot detect semantics, which is stated honestly as a producer obligation, mirroring the source schema's position)

## 4. Extension set

All canonical URLs under the bh-healthcare profile namespace. Extensions are added only for G4-G6, where no R5 element exists:

| Extension | Context | Type | Values |
|---|---|---|---|
| `delegation-type` | AuditEvent | code | `supervised`, `autonomous`, `scheduled` |
| `agent-session-id` | AuditEvent | string | opaque session identifier |
| `chain-depth` | AuditEvent | positiveInt | 1..32 |
| `parent-agent-session-id` | AuditEvent | string | opaque parent session identifier |
| `agent-descriptor` | AuditEvent.agent (acting slice) | complex | sub-extensions: `interface` (code, required: `ui_driving`, `api`, `mcp`, `cli`, `sdk`), `vendor`, `model-family`, `model-version`, `harness`, `harness-version` (strings) |

Everything else maps to native elements. That ratio -- five extensions, the rest native -- is the design goal: maximum reuse of HL7's structure, additions only at genuine gaps.

## 5. Element mapping (bh-audit-schema v2.0 -> R5 AuditEvent)

| bh-audit-schema field | R5 AuditEvent element | Notes |
|---|---|---|
| `event_id` | `id` | UUID preserved |
| `timestamp` | `recorded` | |
| `schema_version` | `meta.profile` | profile canonical carries version |
| `service.name` | `source.observer` (identifier reference) | `source.site`/`source.type` available for environment |
| `actor` (authenticating) | `agent` [authenticating slice] | `actor.roles` -> `agent.role` |
| `delegation.acting` | `agent` [acting slice] | descriptor via `agent-descriptor` extension |
| `delegation.authorizing` | `agent` [authorizing slice] | `requestor = true` |
| `delegation.delegation_type` | extension `delegation-type` | G4 |
| `delegation.agent_session_id` | extension `agent-session-id` | G5 |
| `delegation.chain_depth` / `parent_agent_session_id` | extensions | G5, paired by inv-3 |
| `action.type` | `action` (C/R/U/D/E) | OVERRIDE/LOGIN/LOGOUT/PRINT/EXPORT -> `E` with discriminating `code` |
| `action.name` | `code` | coding from action-name CodeSystem |
| `action.data_classification` | `entity.securityLabel` | v3-Confidentiality codes |
| `resource.type` / `resource.id` | `entity.role` / `entity.what` | identifier references, opaque IDs only |
| `resource.patient_id` | `patient` | R5 first-class element; major win over R4 |
| `outcome.status` | `outcome.code` | SUCCESS -> 0; FAILURE -> 8; DENIED -> 8 **plus required `denied` detail coding** (G7; lossy without the profile, stated plainly) |
| `outcome.error_type` | `outcome.detail` coding | |
| `http.method` / `route_template` / `status_code` | `entity` [transaction] `detail` pairs | scalar type/value pairs |
| `http.client_ip` | `agent.network[x]` | on the relevant agent slice |
| `correlation.*` | extensions (planned) | no native trace home; candidate for alignment with existing tracing extensions before inventing one |
| `metadata` | `entity` [metadata] `detail` pairs | scalar-only constraint maps cleanly onto type/value pairs |
| `integrity.*` | not mapped | FHIR-native alternative is a paired Provenance with `signature`; documented as out of profile scope |

**Mapping-loss register (honesty section):** DENIED collapses into failure-grade 8 for consumers that ignore the profile's detail coding. `integrity` chaining has no AuditEvent home and is intentionally not forced into one. `correlation` trace IDs await alignment with existing tracing conventions rather than a premature extension. Each loss is documented with its mitigation rather than hidden.

## 6. Working translator

A prototype translator (Python, ~200 lines) converts bh-audit-schema v2.0 events to R5 AuditEvent resources and validates output against the R5 structure definitions. Current status against the v2.0 example corpus:

| Input event | Result | Agents |
|---|---|---|
| Agent MCP patient read (agent's own credentials) | valid R5 | 3 |
| Agent UI-driving note write (human's credentials) | valid R5 | 3 |
| Human override of an agent session | valid R5 | 1 |
| Depth-2 sub-agent export | valid R5 | 3 |
| Direct human read (collapse case) | valid R5 | 1 |

Structural validation only at this stage; terminology binding validation arrives with the published CodeSystems. The full translator (bidirectional where lossless, documented loss where not) is the build deliverable.

## 7. Why a profile and not a new standard

A solo schema does not out-standard HL7, and should not try. The source schema (bh-audit-schema) remains the strict, JSON-Schema-validated production contract -- it exists because behavioral health producers need machine-enforced validation today, in production, without FHIR infrastructure. The profile is the same model expressed in HL7's terms so that FHIR-native systems, HIEs, and EMR-adjacent infrastructure can consume attribution events without adopting anything outside the FHIR ecosystem. Contract for producers, profile for the ecosystem, translator as the bridge. The intended trajectory is contribution: this profile is the kind of artifact the HL7 community can take up, reshape, and standardize properly, and it is offered in that spirit.
