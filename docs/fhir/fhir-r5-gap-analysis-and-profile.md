# FHIR R5 AuditEvent for AI Agent Attribution: Gap Analysis and Proposed Profile

**Status:** Working draft, companion to RFC 0001 and RFC 0003
**Scope:** Expressing the bh-audit-schema v2.0 agent attribution model and the v2.1 attribution assurance extension as a profile of FHIR R5 AuditEvent
**Date:** June 2026, updated September 2026 for v2.1

---

## 1. Thesis

FHIR R5 AuditEvent has the structural bones for multi-participant audit events but lacks the semantics, vocabulary, and constraints needed to attribute AI-agent-mediated actions. The gap is precise and narrow, which is what makes it closeable by profile rather than by a competing standard.

The sharpest expression of the gap comes from FHIR itself. The specification divides responsibilities: Provenance covers *generation* of entities, AuditEvent covers *usage*. FHIR's delegation primitive, `Provenance.agent.onBehalfOf`, lives on the generation side. `AuditEvent.agent` has no equivalent element. AI agent access auditing is a usage problem -- who touched this record, under whose credentials, on whose behalf -- so the delegation primitive is absent exactly where agentic healthcare deployments need it.

This document does two things: identifies what R5 AuditEvent cannot express for agent attribution (Section 2), and closes each gap with a profile that constrains existing elements where they suffice and adds extensions only where no element exists (Sections 3-5). The source contract is bh-audit-schema v2.0 and v2.1; the profile is its FHIR interoperability expression, versioned with it (Section 3). A working translator demonstrates the mapping end-to-end (Section 6).

## 2. Gap analysis: what R5 AuditEvent cannot express

| # | Gap | Detail | Closeable by |
|---|---|---|---|
| G1 | No attribution-role semantics | `agent` is 1..* and `agent.type` describes "how agent participated," but no standard vocabulary distinguishes the authenticating identity (whose credentials were presented), the acting identity (what performed the action), and the authorizing identity (whose intent it represents) | Profile: required `agent.type` codes + slicing |
| G2 | `requestor` cannot carry the split | A single boolean per agent marks the initiator. When a human authorized work and an agent performed it under that human's credentials, "the requestor" is ambiguous by construction; the element predates delegated non-human actors | Profile: fixed `requestor` values per attribution slice |
| G3 | No first-class delegation element; the published `auditevent-OnBehalfOf` extension is a single delegation hop and does not carry the authenticating-vs-authorizing split, supervision state, session linkage, sub-agent chains, or agent descriptor | HL7 publishes [`auditevent-OnBehalfOf`](https://hl7.org/fhir/extensions/StructureDefinition-auditevent-OnBehalfOf.html) (canonical `http://hl7.org/fhir/StructureDefinition/auditevent-OnBehalfOf`, Security WG, Draft, Maturity Level 1) in the FHIR Core Extensions Registry. That extension is a building block: a simple `Reference` extension on `AuditEvent.agent` expressing a single "who acted for whom" link. Two limits are structural rather than matters of emphasis. Its `Extension.extension` is `0..0`, so there is no element on the referent that could carry a `requestor`, meaning `requestor` stays on the `agent` element holding the extension. And its `value[x]` is `Reference(Organization \| Patient \| Practitioner \| PractitionerRole \| RelatedPerson \| CareTeam)`, which excludes `Device`, although `agent.who` permits `Device`; so an agent acting on behalf of another agent is not expressible, which is precisely the sub-agent chain case. This profile is the attribution layer built on top of it -- three-way slicing (authenticating / acting / authorizing), supervision state, session and chain linkage, agent descriptor, and validation that rejects an agent action whose authorizing human is neither named nor, on profile 2.1, explicitly recorded as unresolvable | Profile slicing + bounded extensions (G4-G6); the published `auditevent-OnBehalfOf` extension is compatible but insufficient |
| G4 | No supervision state | Nothing expresses whether a human was actively observing (supervised), absent (autonomous), or never present (scheduled) at the time of the action -- the first question a compliance reviewer asks about an agent action | Extension: `delegation-type` |
| G5 | No agent session or chain linkage | No convention ties an agent's actions to a reviewable session, and nothing models sub-agent chains (an agent spawning agents) | Extensions: `agent-session-id`, `chain-depth`, `parent-agent-session-id` |
| G6 | No agent descriptor constraints | `agent.who` can reference a Device, so an AI agent is *representable*, but nothing requires recording which model, version, harness, or interaction surface acted. An attribution record that cannot say which agent acted is weak evidence | Complex extension: `agent-descriptor` (interface required) |
| G7 | No authorization-denial outcome | `outcome.code` values grade success and failure severity. "The system correctly refused access" -- the DENIED semantic critical for HIPAA access reports and 42 CFR Part 2 consent denials -- has no code; mapping it to a failure grade conflates correct authorization behavior with operational error | Profile: required `outcome.detail` coding when DENIED |
| G8 | No PHI-minimization discipline for agentic content | `entity.query`, `outcome` text, and `entity.detail` values can carry arbitrary content. Nothing prohibits prompts, model outputs, screenshots, or reasoning traces -- the agentic equivalents of request bodies -- from entering the audit record | Profile invariants: prohibited content classes, scalar-only detail values |
| G9 | No validation requiring attribution completeness | Nothing makes an agent-performed event invalid when the authorizing human is missing | Profile invariant: acting slice present implies authorizing slice present (inv-1). On profile 2.1 the absence of a human is expressible, but only as an explicit `unattributed` slice (inv-7); silence stays invalid on both profiles |
| G10 | No attribution assurance (v2.1) | Nothing records how the identities in the event became known: from a token whose issuer asserted them, from operator configuration, or from the agent's own claim. Nor is there a way to state that an agent authenticated and no authorizing human could be resolved; the only shapes available assert a direct requestor or a named human | Extensions: `attribution-level`, `attribution-method`; profile slice `unattributed` |

What is deliberately *not* claimed as a gap: multi-agent structure (exists), AI actors as references (Device works), patient linkage (R5 added a first-class `patient` element, which this profile uses), or purpose-of-use (R5 `authorization` covers it). The profile builds on these rather than duplicating them.

### 2.1 Prior art and positioning

Two prior efforts in this space inform the profile's design:

- **HL7 `auditevent-OnBehalfOf` extension** (FHIR Core Extensions Registry, Draft, Maturity Level 1). Expresses a single delegation hop on `AuditEvent.agent`. Two change requests filed by this project against it, [FHIR-58715](https://jira.hl7.org/browse/FHIR-58715) on the value binding and [FHIR-58716](https://jira.hl7.org/browse/FHIR-58716) on `requestor`, were unresolved and unassigned at the time of writing (September 2026). The profile is compatible with `auditevent-OnBehalfOf` but does not rely on it alone: that extension collapses the authenticating-vs-authorizing distinction, which is exactly the split that matters in the agent-under-its-own-credential case (`actor.subject_type == "agent"` in the source schema). The three-slice design is what makes that split queryable.
- **IHE Basic Audit Log Patterns (BALP)**. The IHE AuditEvent profiling stream defines complementary `AuditEvent.agent` extensions (e.g., assurance level). The attribution profile here is orthogonal to BALP -- BALP refines participation properties, this profile refines participation *semantics* for agent-mediated action -- and the two can be applied to the same AuditEvent without conflict.

The profile's contribution is not a competing standard. It is the attribution layer that the existing `auditevent-OnBehalfOf` extension and the BALP slicing patterns can be composed with.

## 3. The profile in one view

The profile is versioned with the source schema. Each version has its own canonical, in path form to parallel `schema/versions/<ver>/`, and the translator writes the one for the event's `schema_version` into `meta.profile`:

| Source `schema_version` | Profile canonical |
|---|---|
| `2.0` | `https://bh-healthcare.github.io/bh-audit-schema/fhir/2.0/StructureDefinition/bh-audit-event` |
| `2.1` | `https://bh-healthcare.github.io/bh-audit-schema/fhir/2.1/StructureDefinition/bh-audit-event` |

A resource claims exactly one of the two, and the two are not interchangeable in either direction. A v2.0 delegated resource carries no `attribution-level` extension, so it fails inv-6 of profile 2.1. A v2.1 `unattributed` resource carries no `direct` slice, so it fails the collapse rule of profile 2.0. The cause is the one RFC 0003 section 6 states for the source schema: silence means something different in each version. Three agent slices and no attribution statement is a complete 2.0 record and an invalid 2.1 one, and one unversioned canonical would say that resource both conforms and does not. The path form is used because the profile is prose with no compiled StructureDefinition to resolve a `canonical|version` reference against; the two canonicals are two identifiers and nothing more. If an implementation guide is published, the pipe form becomes correct and that is a canonical change at that point.

### 3.1 Profile 2.0

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

### 3.2 Profile 2.1

Profile 2.1 is profile 2.0 plus the attribution assurance layer from RFC 0003. It adds one slice, amends the collapse rule, adds two invariants, and adds the two G10 extensions in section 4. Everything in 3.1 not restated here carries over unchanged.

| Slice | `agent.type` code | `agent.who` | `requestor` | Cardinality |
|---|---|---|---|---|
| direct | `direct` | the human or service that acted directly | `true` | the collapse case: 1..1 when no acting slice and the event is not `unattributed` |
| unattributed | `unattributed` | the agent credential that authenticated; no authorizing human could be resolved | `false` | 1..1 when `attribution-level` is `unattributed`; excludes every other slice |

An event at `attribution.level: "unattributed"` has no delegation block, so the acting and authorizing slices do not exist, and it must not collapse to `direct`. The authenticating slice's qualifier in 3.1, required for agentic events, does not apply here either: the credential that authenticated is carried by the `unattributed` slice itself, which is the only slice. That collapse would assert the agent acted directly as the requestor, which is the false claim the profile exists to prevent, and the translator would produce it from a correctly formed source event. The `unattributed` slice names the state instead. It carries `requestor = false` because no initiating intent could be named, and `agent.who` names the credential that authenticated, so the event is not anonymous.

**Additional invariants:**

- inv-6: if an `acting-identity` slice is present, the `attribution-level` extension is present with a value other than `unattributed` (mirrors RFC 0003 R1)
- inv-7: an `unattributed` slice is present if and only if the `attribution-level` extension is `unattributed`, and it is then the only agent slice (mirrors RFC 0003 R2, R3, and R4)

inv-6 is the reason the two profiles cannot share a canonical. Every v2.0 delegated resource has an acting slice and no `attribution-level` extension, so it fails inv-6 as written. The invariant is correct on profile 2.1 and wrong on profile 2.0.

## 4. Extension set

All canonical URLs under the bh-healthcare profile namespace, shared by both profile versions; only the profile canonical itself is versioned. Extensions are added only for G4-G6 and, on profile 2.1, G10, where no R5 element exists:

| Extension | Context | Type | Values |
|---|---|---|---|
| `delegation-type` | AuditEvent | code | `supervised`, `autonomous`, `scheduled` |
| `agent-session-id` | AuditEvent | string | opaque session identifier |
| `chain-depth` | AuditEvent | positiveInt | 1..32 |
| `parent-agent-session-id` | AuditEvent | string | opaque parent session identifier |
| `agent-descriptor` | AuditEvent.agent (acting slice) | complex | sub-extensions: `interface` (code, required: `ui_driving`, `api`, `mcp`, `cli`, `sdk`), `vendor`, `model-family`, `model-version`, `harness`, `harness-version` (strings) |
| `attribution-level` (profile 2.1 only) | AuditEvent | code | `verified`, `bound`, `asserted`, `unattributed`. Present whenever the source event carries `attribution`; required with the acting slice on profile 2.1 (inv-6). Never present on a 2.0 resource |
| `attribution-method` (profile 2.1 only) | AuditEvent | string | open vocabulary, 1 to 64 characters; present only when the source event carries `method` |

Everything else maps to native elements. That ratio -- seven extensions, the rest native -- is the design goal: maximum reuse of HL7's structure, additions only at genuine gaps.

The `attribution-level` extension is emitted independently of the delegation block. An `unattributed` event has no delegation block and would otherwise translate with its level silently dropped. The four level codes are totally ordered, weakest to strongest, `unattributed` < `asserted` < `bound` < `verified` (RFC 0003 section 4.4); the rank is not serialized in the extension, and a consumer comparing against a threshold compares on position in that sequence, never on the code string.

## 5. Element mapping (bh-audit-schema v2.0 and v2.1 -> R5 AuditEvent)

| bh-audit-schema field | R5 AuditEvent element | Notes |
|---|---|---|
| `event_id` | `id` | UUID preserved |
| `timestamp` | `recorded` | |
| `schema_version` | `meta.profile` | `.../fhir/2.0/StructureDefinition/bh-audit-event` for a `2.0` event, `.../fhir/2.1/StructureDefinition/bh-audit-event` for a `2.1` event (section 3) |
| `service.name` | `source.observer` (identifier reference) | `source.site`/`source.type` available for environment |
| `actor` (authenticating) | `agent` [authenticating slice] | `actor.roles` -> `agent.role` |
| `actor` on an `unattributed` event (profile 2.1) | `agent` [unattributed slice] | `actor.roles` -> `agent.role`; `requestor = false` |
| `delegation.acting` | `agent` [acting slice] | descriptor via `agent-descriptor` extension |
| `delegation.authorizing` | `agent` [authorizing slice] | `requestor = true` |
| `delegation.delegation_type` | extension `delegation-type` | G4 |
| `delegation.agent_session_id` | extension `agent-session-id` | G5 |
| `delegation.chain_depth` / `parent_agent_session_id` | extensions | G5, paired by inv-3 |
| `attribution.level` (v2.1) | extension `attribution-level` (`valueCode`) | G10; on an `unattributed` event this is the only attribution statement in the resource |
| `attribution.method` (v2.1) | extension `attribution-method` (`valueString`) | G10; nothing is lost on the round trip |
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

**Mapping-loss register (honesty section):** DENIED collapses into failure-grade 8 for consumers that ignore the profile's detail coding. `integrity` chaining has no AuditEvent home and is intentionally not forced into one. `correlation` trace IDs await alignment with existing tracing conventions rather than a premature extension. Attribution assurance rides on an extension because R5 AuditEvent has no native concept of it: an R5 consumer that does not know `attribution-level` sees an authenticating agent and no assurance statement, and on an `unattributed` event sees a single agent with an unfamiliar `agent.type` code and `requestor = false`. The distinction is preserved in the native format and is available but ignorable in R5, the same trade the delegation extensions already make. Each loss is documented with its mitigation rather than hidden.

## 6. Working translator

A translator (Python, [`scripts/translate_to_fhir.py`](../../scripts/translate_to_fhir.py)) converts bh-audit-schema v2.0 and v2.1 events to R5 AuditEvent resources and validates output against the R5 structure definitions. Current status against the v2.0 example corpus (7 positive = 5 core attribution scenarios + 2 RFC §7.2 session-lifecycle convention examples):

| Input event | Result | Agents |
|---|---|---|
| Agent MCP patient read (agent's own credentials) | valid R5 | 3 |
| Agent UI-driving note write (human's credentials) | valid R5 | 3 |
| Human override of an agent session | valid R5 | 1 |
| Depth-2 sub-agent export | valid R5 | 3 |
| Direct human read (collapse case) | valid R5 | 1 |
| Agent session start (CREATE on AgentSession) | valid R5 | 3 |
| Agent session end (UPDATE, `action.name: agent_session_end`) | valid R5 | 3 |

Against the v2.1 example corpus (11 positive: the 7 above carried forward with an `attribution` block on the 5 that carry `delegation`, plus the 4 RFC 0003 §11.1 additions):

| Input event | Result | Agents | `attribution-level` |
|---|---|---|---|
| Agent MCP patient read | valid R5 | 3 | `verified` |
| Agent UI-driving note write | valid R5 | 3 | `bound` |
| Human override of an agent session | valid R5 | 1 (`direct`) | none |
| Depth-2 sub-agent export | valid R5 | 3 | `verified` |
| Direct human read (collapse case) | valid R5 | 1 (`direct`) | none |
| Agent session start | valid R5 | 3 | `verified` |
| Agent session end | valid R5 | 3 | `verified` |
| Enforced-tier denial, no authorizing human | valid R5 | 1 (`unattributed`, `requestor = false`) | `unattributed` |
| Fail-open success, no authorizing human | valid R5 | 1 (`unattributed`, `requestor = false`) | `unattributed` |
| Agent-asserted call | valid R5 | 3 | `asserted` |
| Bound call with `method` omitted | valid R5 | 3 | `bound`, no `attribution-method` |

`tests/test_v21_translator.py` asserts, for both `unattributed` events, that no agent slice carries `requestor = true` and none carries the `direct` code; that the attribution extensions round-trip for every event in the corpus; and that every v2.0 event claims the 2.0 canonical and every v2.1 event the 2.1 canonical. Translator output for v2.0 events is unchanged except `meta.profile`, which now carries the 2.0 canonical in place of the unversioned one the v2.0.0 translator emitted.

Structural validation only at this stage; terminology binding validation arrives with the published CodeSystems. The full translator (bidirectional where lossless, documented loss where not) is the build deliverable.

## 7. Why a profile and not a new standard

A solo schema does not out-standard HL7, and should not try. The source schema (bh-audit-schema) remains the strict, JSON-Schema-validated production contract -- it exists because behavioral health producers need machine-enforced validation today, in production, without FHIR infrastructure. The profile is the same model expressed in HL7's terms so that FHIR-native systems, HIEs, and EMR-adjacent infrastructure can consume attribution events without adopting anything outside the FHIR ecosystem. Contract for producers, profile for the ecosystem, translator as the bridge. The intended trajectory is contribution: this profile is the kind of artifact the HL7 community can take up, reshape, and standardize properly, and it is offered in that spirit.

## 8. Recorded divergence: sub-agent chains

This project raised the G3 finding on the HL7 Security and Privacy stream in August 2026 ([thread](https://chat.fhir.org/#narrow/channel/179247-Security-and-Privacy/topic/auditevent-OnBehalfOf.20and.20the.20agent-acting-for-agent.20case/with/618104672)). The replies came from John Moehrke, who spoke to the extension's design in the first person. Moehrke's remarks, kept in the form they were made:

- The `Device` exclusion from the extension's `value[x]` was deliberate, because devices need their authorization to come from a human. Moehrke asked whether the description needs to be made clearer, and asked whether agentic AI makes the original assumption untrue, answering no, on the view that a human must always be the root of authorization.
- Given this use case, Moehrke asked whether a second agent acting because the first agent asked it to is really an on-behalf-of relationship, or simply one event triggering another, that is, two AuditEvent instances. The analogy offered was a nurse applying a bandage because a doctor asked.
- An AuditEvent records the elements of one activity and does not try to record the previous or subsequent events, which would be other events. In the human case, where the instruction is not verbal, a Task resource might exist to hold the authorization imparted on the nurse; verbal instructions are typically expected to be covered by professional practice.
- If standards are developed for MCP, that could also be the linkage.
- Audit does not mandate any specific authorization. It records facts, sometimes facts contrary to policy and authorization.

Moehrke also asked what changes should be made to AuditEvent or the extension and invited clarifying comments on the tracker item. Nothing in the thread went beyond those remarks, and none of them is a work group position.

Everything else in the pattern is this project's proposal. Linking the two events to a Task through `AuditEvent.basedOn`, and the observation that a device in the acting position has nothing like professional practice underneath it, so the Task is the only place an intact chain is recorded, were put forward from this side and written up by this project, as reporter, on [FHIR-58715](https://jira.hl7.org/browse/FHIR-58715). On that ticket this project withdrew its own request to widen the binding, and in an amendment dated 2026-09-03 withdrew its request for normative Task language, leaving two descriptive asks: a description edit on the extension that uses the words `participant` and `actor`, which the Extension definition already uses one level down, in place of `agent`, and a usage note describing the two-events-and-Task pattern as the way to record an intact chain, with no requirement attached. A related ticket, [FHIR-58716](https://jira.hl7.org/browse/FHIR-58716), asks for a usage note stating that the extension does not affect `AuditEvent.agent.requestor`. Both tickets were unresolved and unassigned at the time of writing (September 2026); nothing in them has been accepted by the work group.

This profile diverges from the two-events-and-Task pattern. The divergence is recorded here as a known one, with the reasoning, and the translator is not changed to match.

In the source schema a sub-agent action is one event. `delegation.acting` names the sub-agent, `delegation.authorizing` names the root human (RFC 0001 section 5.1: intermediate agents never occupy the authorizing position), and the chain is carried by `chain_depth` and `parent_agent_session_id`, which RFC 0001 section 6 rule 2 pairs bidirectionally. The parent agent is reachable by query across linked session identifiers and is never embedded in the event.

For a `chain_depth >= 2` event the translator therefore emits one AuditEvent with three agent slices (authenticating, acting = the sub-agent, authorizing = the root human) and the `chain-depth` and `parent-agent-session-id` extensions. The parent agent appears only as the opaque session identifier in `parent-agent-session-id`. No Task is produced and `basedOn` is not populated. Checked against `examples/2.1/sub_agent_depth2_export.json`.

Why the translator is left as it is:

- The native contract records the chain in one producer-side event because the producer that observes the sub-agent's action holds that event and nothing else. It does not hold the parent's AuditEvent and cannot mint a Task on the parent's behalf.
- A Task-linked shape needs a second resource and an identifier the two resources share. That is a store-side reconstruction from `parent-agent-session-id`, the same reconstruction the source schema already relies on for chain queries.
- The authorizing human on a sub-agent event is the root human, not the parent agent, so the single-event shape does not misstate who authorized the action. What it omits is the parent agent as a participant in this event.

A consumer that needs the Task-linked shape can derive it from the extensions: group events by `agent-session-id` and `parent-agent-session-id`, emit one Task per parent-child session pair, and populate `basedOn` on both events. The translator does not do this today. Closing the divergence, if the work group adopts guidance describing that pattern through FHIR-58715, is a profile revision with a store-side component, and it is tracked as such.
