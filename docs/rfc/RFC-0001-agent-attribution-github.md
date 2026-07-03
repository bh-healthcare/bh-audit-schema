<!--
RFC 0001: AI Agent Attribution and the Human-Agent Delegation Chain
Repository: bh-healthcare/bh-audit-schema
This document is a draft for community discussion. This is not a release.
-->

# RFC 0001: AI Agent Attribution and the Human-Agent Delegation Chain

| | |
|---|---|
| **RFC** | 0001 |
| **Title** | AI Agent Attribution and the Human-Agent Delegation Chain |
| **Status** | Draft for discussion |
| **Target** | bh-audit-schema v2.0 |
| **Tracking issue** | [#6](https://github.com/bh-healthcare/bh-audit-schema/issues/6) |
| **Companion** | [`fhir/fhir-r5-gap-analysis-and-profile.md`](../fhir/fhir-r5-gap-analysis-and-profile.md) |
| **Discussion period** | 14 days minimum (major version, per [GOVERNANCE.md](../../GOVERNANCE.md)) |
| **Supersedes** | none |
| **Created** | 2026-06 |

---

## Table of Contents

1. [Summary](#1-summary)
2. [Scope and Non-Goals](#2-scope-and-non-goals)
3. [What This Standard Does and Does Not Claim](#3-what-this-standard-does-and-does-not-claim)
4. [The Three-Role Model](#4-the-three-role-model)
5. [The `delegation` Object](#5-the-delegation-object)
6. [Conditional Validation](#6-conditional-validation)
7. [Event Conventions](#7-event-conventions)
8. [PHI Safety in Agentic Context](#8-phi-safety-in-agentic-context)
9. [FHIR R5 AuditEvent Alignment](#9-fhir-r5-auditevent-alignment)
10. [OAuth 2.0 Token Exchange Alignment](#10-oauth-20-token-exchange-alignment)
11. [Emission Tiers](#11-emission-tiers)
12. [Controls Mapping Delta](#12-controls-mapping-delta)
13. [Versioning and Migration](#13-versioning-and-migration)
14. [Deferred and Future Work](#14-deferred-and-future-work)
15. [Validation Suite](#15-validation-suite)
16. [Reference: Full Example Event](#16-reference-full-example-event)

---

## 1. Summary

Today the bh-audit-schema v1.x models a single actor per audit event. The `actor` field encompasses three meanings:

- The entity that authenticated into the system
- The entity that performed the action
- The human entity whose intent the action represents

As of this date, every event the schema has validated, whether in testing or production, has had these three entities coalesce into one.
Unfortunately, this year with the introduction of AI agents that effectively operate software, this assumption can no longer be maintained. Agents can drive a GUI, call APIs, or run scheduled work with no human oversight. 
In each of these cases the current audit schema has no way to express the separation. FHIR R5 AuditEvent also does not support this separation to the degree that it is needed. FHIR R5 does support multiple participants per event, but the attribution semantics, delegation linkage, supervision state, and validation discipline do not (see the companion FHIR gap analysis).

This RFC describes v2.0 as two artifacts, a schema extension and a FHIR profile:

1. **Schema extension.** A multi-actor attribution model (authenticating, acting, authorizing), a new `delegation` object, an extended actor taxonomy, conditional validation that makes unattributed agent actions invalid by construction, and event conventions for agent session lifecycle and human override.
2. **FHIR expression.** A proposed profile extension of R5 AuditEvent that closes the identified gaps using attribution-typed agent slices, a bounded extension set, and profile invariants, with a working translator between the two.

FHIR R5 AuditEvent alignment is a primary design constraint of v2.0. Every v2.0 field is intended to map to a FHIR R5 AuditEvent element or a documented, mitigated loss.

## 2. Scope and Non-Goals

**In scope:** attribution of actions performed by AI agents operating under delegated human authority, in behavioral health systems that handle PHI.

**Out of scope for v2.0:**

- Human-proxy delegation (a human acting under another human's authority).
- Consent document modeling (this will require a separate effort and has to be tracked separately; agent events adopt it when it becomes available).
- Agent capability declaration and verification (belongs to the credential/identity layer, not the audit record).
- Detection of non-cooperating agents (see Section 3).

## 3. What This Standard Does and Does Not Claim

This section is normative.

The schema is an audit record model. It is not intended as a detection mechanism but as a reporting and auditing mechanism. It provides a deployment that has adopted it a vocabulary to record agent attribution truthfully and a validator that rejects agent events when the attribution is missing. It cannot make a non-cooperating agent identify itself.

To a system being driven by an agent using a human's credentials, the action is indistinguishable from the human themselves acting on the system. That system cannot emit the delegation record because it does not know one is needed. Only the agent-side infrastructure (the harness, the gateway, the runtime) knows and is responsible for emitting the delegation record. Therefore:

- Attribution events for agent actions have to be emitted by agent-side infrastructure, not simply by the target system.
- A deployment that routes agent traffic through an enforcing gateway can guarantee attribution for that traffic.
- A deployment that relies on agents voluntarily self-reporting can claim only cooperative attribution.
- An agent that does not participate in the audit record is out of scope. Any deployment claiming otherwise is overclaiming.

This standard gives organizations and regulators an enforceable requirement ("agent-mediated access to systems containing ePHI must emit attribution events conforming to this specification") in place of an impossible detection mechanism. Section 11 defines emission tiers so a deployment can state precisely which guarantee it provides. It is the responsibility of the deployment to ensure that the agent-side infrastructure is configured to emit the attribution events.

## 4. The Three-Role Model

Every audited action has three identity roles.

| Role | Definition | v2.0 location |
|---|---|---|
| Authenticating identity | The identity whose credentials were presented to the target system | `actor` |
| Acting identity | The entity that physically performed the action | `delegation.acting` |
| Authorizing identity | The human whose intent the action represents | `delegation.authorizing` |

In a direct human action, all three collapse into one person and the event is structurally identical to a v1.x event. In an agent-mediated action, the roles separate. Two canonical separations:

**Agent under human credentials (UI driving).** The agent operates the interface inside the human's authenticated session. `actor` is the human (their credentials were presented). `delegation.acting` is the agent. `delegation.authorizing` is the human. Authenticating and authorizing are the same person; acting is not.

**Agent under its own credentials (API, MCP, service account).** The agent presents its own credential. `actor.subject_type` is `agent`. `delegation.acting` describes the agent. `delegation.authorizing` is the human who delegated the work. All three roles differ.

### 4.1 Actor Taxonomy

`subject_type` becomes a three-value enum, published as `$defs/SubjectType`.

| Value | Definition |
|---|---|
| `human` | An authenticated human user |
| `service` | Deterministic code acting under its own service identity. Behavior is fixed by its programming; no delegated human intent is interpreted at runtime |
| `agent` | A non-deterministic AI actor operating under delegated human authority. Behavior is produced by a model interpreting an instruction |

The service/agent boundary is intent interpretation. A nightly export job is a service: what it does was decided when it was written. An agent told to "prepare the weekly attendance summary" decides at runtime what actions that requires. The distinction matters for audit review because agent actions require examining the delegation, not only the code.

### 4.2 Semantics Change to `actor`

In v2.0, `actor` is defined precisely as the authenticating identity: the identity whose credentials were presented. This is the semantic core of the major version. In v1.x, the query "all actions by user Y" meant "all actions Y performed." In an environment with agents, the same query against the same field means "all actions performed under Y's credentials," a different compliance claim. v2.0 events make the distinction explicit; v1.x events make no claim either way. The schema version becomes the marker of which attribution model an event asserts.

## 5. The `delegation` Object

A new optional top-level object. Its presence asserts the action was agent-mediated. Its absence on a v2.0 event asserts a direct, non-delegated action.

```json
"delegation": {
  "acting": {
    "subject_id": "agent_inst_4471",
    "subject_type": "agent",
    "agent": {
      "interface": "mcp",
      "vendor": "vendor_a",
      "model_family": "model_x",
      "model_version": "x-3.1",
      "harness": "mcp_gateway",
      "harness_version": "0.4.2"
    }
  },
  "authorizing": {
    "subject_id": "user_123",
    "subject_type": "human",
    "org_id": "org_77"
  },
  "delegation_type": "supervised",
  "agent_session_id": "agsess_01J9X0001",
  "chain_depth": 1
}
```

### 5.1 Field Semantics

**`acting`** (required). The agent that performed the action. `subject_type` is const `agent` in v2.0; human-proxy delegation is deferred (Section 14).

**`acting.agent`** (required). The agent descriptor. `interface` is the only required sub-field because the interaction surface determines the risk class and the available enforcement points.

| `interface` | Meaning | Enforcement reality |
|---|---|---|
| `ui_driving` | Agent operated a graphical interface as a human would | Target system cannot distinguish agent from human; attribution depends on agent-side emission |
| `api` | Direct HTTP API calls | Enforceable at the API layer |
| `mcp` | Tool calls through a Model Context Protocol server or gateway | Enforceable at the gateway; the strongest available control point |
| `cli` | Command-line interface | Enforceable at wrapper level |
| `sdk` | Vendor or first-party SDK | Enforceable at SDK level |

`vendor`, `model_family`, `model_version`, `harness`, `harness_version` are optional but strongly recommended. An attribution record that cannot say which agent acted is weak evidence. None of these fields may carry free-text prompt or configuration content.

**`authorizing`** (required). The human whose intent the action represents. `subject_type` is const `human`. For sub-agent chains this is always the root human; intermediate agents are reachable through the session chain, not by reassigning authorization. An agent cannot authorize.

**`delegation_type`** (required). Records the supervision state, the first question a compliance reviewer asks about an agent action.

| Value | Meaning |
|---|---|
| `supervised` | A human is actively observing and can intervene in real time |
| `autonomous` | The agent acts without real-time human observation |
| `scheduled` | The agent was launched by a timer or trigger with no human present at execution time |

**`agent_session_id`** (required). Correlates every action to its session lifecycle events (Section 7.2). An agent action that cannot be tied to a session cannot be reviewed as a session, and session-level review is how humans audit agent behavior.

**`chain_depth`** and **`parent_agent_session_id`**. Sub-agent support. Depth 1 is an agent delegated directly by the authorizing human; depth 2 is a sub-agent spawned by a depth-1 agent. Chains are reconstructed by query across linked session IDs and are never embedded in events. Embedding would bloat every event and expand the PHI surface for zero query benefit. Validation enforces the pairing in both directions: depth >= 2 requires a parent, and a parent requires depth >= 2.

## 6. Conditional Validation

Three rule groups, in the established v1.1 `allOf` pattern.

1. `actor.subject_type == "agent"` requires `delegation`. An agent acting under its own credential with no identifiable authorizing human is invalid by construction. This is the compliance property the schema exists to enforce.
2. Within `delegation`: `chain_depth >= 2` requires `parent_agent_session_id`, and `parent_agent_session_id` requires `chain_depth >= 2`. The `dependentRequired` keyword is insufficient here because it checks presence, not value; a depth-1 agent claiming a parent is contradictory and must fail.
3. `action.type == "OVERRIDE"` requires `actor.subject_type == "human"`, `resource.type == "AgentSession"` with `resource.id` present, and forbids `delegation`. Only humans override, and an override is by definition a direct action.

### 6.1 Known Validator Behavior

When an agent-actor event also carries `action.type: OVERRIDE`, rules 1 and 3 both fail and standard validators report whichever they hit first, typically "delegation is a required property" rather than "agents cannot override." The combined effect is correct (the event is unsatisfiable); the error message is less direct than ideal. Reference implementations should add a friendlier pre-check.

### 6.2 What Validation Cannot Enforce

The UI-driving case. When an agent acts under human credentials, `actor.subject_type` is `human` and the schema cannot conditionally require `delegation`, because a structurally identical event describes a genuine direct human action. Truthfulness of that case rests entirely on the emitting layer. This is the representational limit from Section 3 expressed at the field level, and it is why the emission tiers in Section 11 are part of the specification rather than deployment advice.

## 7. Event Conventions

### 7.1 No Agent-Specific Action Types for Resource Operations

An agent reading a chart is a `READ`. The proposal in issue #6 to add `AI_AGENT_DATA_ACCESS` and `AI_AGENT_DATA_WRITE` action types is rejected: it encodes the actor into the action taxonomy, which breaks the orthogonality that makes the schema queryable. Every existing compliance query filtering `action.type` would silently miss agent events, and every consumer would carry two parallel taxonomies indefinitely. Attribution lives in the actor model. The action taxonomy stays about what happened.

### 7.2 Agent Session Lifecycle

Sessions are modeled as a resource, reusing the existing taxonomy.

| Lifecycle moment | Convention |
|---|---|
| Session start | `action.type: CREATE`, `resource.type: AgentSession`, `resource.id` = the session ID, `delegation` present |
| Session end | `action.type: UPDATE`, `action.name: agent_session_end`, `resource.type: AgentSession`, `delegation` present |

Session end is an `UPDATE` (the session record is finalized) rather than a `DELETE` (nothing is removed). This convention adds zero enum values for lifecycle.

### 7.3 `OVERRIDE` (New Action Type)

The single addition to `ActionType`. Records a human interrupting, cancelling, or reversing an agent action or session. The event's `actor` is the human directly; `resource` is the `AgentSession` being overridden; `delegation` is absent because the override itself is a direct human action. `action.name` and scalar `metadata` carry the override category. v2.0 scopes override to humans; agent-initiated halts of sub-agents are deferred.

### 7.4 Consent Verification

Issue #6 proposed `AI_AGENT_CONSENT_VERIFICATION` as an event type. Deferred to the consent modeling work already planned for the schema, an independent axis from agent attribution. The existing `outcome.error_type: ConsentRequired` convention covers consent-gated denials for agent events identically to human events.

## 8. PHI Safety in Agentic Context

The v1 threat model identified request and response bodies as the primary PHI leakage vector. Agentic operation creates new vectors of the same species, and the rule is unchanged: no bodies.

| Vector | Rule |
|---|---|
| Prompts and instructions | Never enter audit events. A prompt is the new request body |
| Model outputs | Never enter audit events |
| Screenshots and rendered context | Never enter audit events. A screenshot of a chart is the chart |
| Reasoning traces | Never enter audit events |

The schema enforces what it structurally can: no field accepts this content, `metadata` remains scalar-only with bounded properties, and `additionalProperties: false` rejects smuggled fields. Deployments that need prompt or context retention for review store it in a separately access-controlled artifact store and may reference it with an opaque identifier in `metadata` (for example, `context_artifact_id`). The audit log must remain useful without PHI access.

This resolves issue #6 open question 2 (no prompt/output content in events) and open question 1 (granularity is action-level, never keystroke-level, because keystroke capture is content capture).

## 9. FHIR R5 AuditEvent Alignment

R5 AuditEvent supports multiple participants per event (`agent` is 1..*), permits AI actors (`agent.who` can reference a Device), and added a first-class `patient` element. This RFC claims no novelty on multi-actor audit structure. What R5 lacks is the attribution layer:

- No vocabulary distinguishing authenticating, acting, and authorizing identities.
- A single `requestor` boolean that cannot carry the split when work has been performed by an agent under a human's credentials, whether authorized by them or not.
- No delegation element on `agent`. FHIR's delegation primitive, `Provenance.agent.onBehalfOf`, lives on the *generation* side of FHIR's stated Provenance/AuditEvent split, while AuditEvent, the *usage* record, has no counterpart. Agent access auditing is a usage problem.
- No supervision-state concept, agent session linkage, or sub-agent chain model.
- No agent descriptor constraints.
- No authorization-denial outcome semantic distinct from operational failure.
- No PHI-minimization discipline against prompts, outputs, or rendered context.

v2.0 ships its FHIR expression as a first-class deliverable that includes a proposed R5 AuditEvent profile with attribution-typed agent slices, a bounded extension set covering only the genuine gaps, profile invariants mirroring this RFC's conditional validation, and a complete element mapping with a documented loss register.
The full analysis lives in a companion document, and a working translator validates the mapping against the entire v2.0 example corpus.
The positioning of this RFC is intentionally contributive and is not intended as a competitive parallel. The JSON Schema contract serves producers that need strict machine validation without FHIR infrastructure, the profile serves the FHIR ecosystem, and the translator bridges them.

## 10. OAuth 2.0 Token Exchange Alignment

RFC 8693 defines the `act` (actor) claim with nested delegation chains, the standards-track expression of delegated authority at the credential layer. v2.0 field semantics are deliberately compatible: `actor` corresponds to the subject of the presented token, `delegation.acting` to the `act` claim's actor, and `chain_depth` to nested `act` claims. When on-behalf-of token issuance for agents becomes common, v2.0 events are the audit layer already shaped for it, with no redesign.

## 11. Emission Tiers

A deployment's attribution guarantee is only as strong as its weakest emission path. The specification defines three tiers so claims can be precise.

| Tier | Mechanism | Guarantee |
|---|---|---|
| **Enforced** | Agent traffic passes through a gateway or middleware that constructs and emits attribution events itself (MCP gateway, API proxy, instrumented SDK). The agent cannot reach the target system without the emission occurring | Attribution is guaranteed for all traffic on the controlled path |
| **Instrumented** | The agent harness or runtime emits events through hooks. Cooperative but structural; bypassing requires modifying the runtime | Attribution is guaranteed for actions taken through the instrumented runtime |
| **Advisory** | Rules and instruction files direct agents to self-report through a published endpoint | No guarantee. An instruction asking an agent to self-report is an honor system in a text file |

Advisory-tier templates are worth publishing as an adoption on-ramp for teams that have nothing, and the specification includes them. They are not audit infrastructure and must not be described as such. The reference implementation targets the enforced tier first, via MCP middleware, because the MCP gateway is the strongest control point in current agent deployments.

Compliance language a deployment can honestly use, by tier: enforced, "all agent actions against system X are attributed"; instrumented, "all actions by our deployed agents are attributed"; advisory, "our agents are instructed to report their actions."

## 12. Controls Mapping Delta

Full mappings go to [`docs/controls-mapping.md`](../../docs/controls-mapping.md) at implementation time. The deltas:

**HIPAA Sec. 164.312(d), Person or Entity Authentication.** The strongest new hook. The provision requires verifying that a person or entity seeking access is who they claim to be. Agent-mediated access under human credentials is precisely the scenario where the authenticated identity and the acting entity diverge, and the delegation object is the record of that divergence. `delegation.acting` plus `actor` together document which entity actually exercised the authenticated access.

**HIPAA Sec. 164.312(b), Audit Controls.** Extended: the recorded activity now distinguishes the performing entity from the credentialed identity. `delegation_type` records the supervision state at the time of each action.

**42 CFR Part 2 Sec. 2.13 / Sec. 2.16.** Agent access to SUD records inherits all existing protections; additionally, `delegation.authorizing` makes consent accountability attach to a human even when an agent performed the access, and `interface: ui_driving` flags the access pattern with the weakest technical controls for heightened review.

**SOC 2 CC6.1 / CC7.2.** Agent session monitoring, override-rate analysis, and autonomous-action volume become queryable monitoring dimensions.

**NIST AI RMF (GOVERN, MAP) and ISO/IEC 42001 Sec. 8.3.** The delegation record is the operational evidence layer for governance claims: who authorized which agent to do what, under what supervision mode, with what override history. The mapping document states this as supporting evidence, not certification.

## 13. Versioning and Migration

v2.0 is structurally additive: every valid v1.1 event becomes a valid v2.0 event by updating `schema_version`. The major version is justified by the semantics change to `actor` (Section 4.2): v2.0 events assert an attribution model; v1.x events do not.

Migration notes:

- Producers in agent-free environments: update `schema_version` to `2.0`. Nothing else changes, and the absence of `delegation` now positively asserts direct action.
- Producers in agent-exposed environments: route agent traffic through an enforced or instrumented emission path before claiming v2.0 attribution semantics.
- Consumers: queries of the form "all actions by user Y" should be reviewed and, where the intent is "performed personally by Y," extended with `delegation IS NULL` or the store's equivalent.
- v1.x remains supported per the existing 6-month-minimum policy.

## 14. Deferred and Future Work

| Item | Disposition |
|---|---|
| Human-proxy delegation | Deferred; real in healthcare operations, independent design axis |
| Consent modeling (consent IDs, purpose, break-the-glass) | Existing planned work; agent events adopt it when it lands |
| Agent capability declaration and verification (issue #6 Q4) | Deferred; belongs to the identity/credential layer, not the audit record |
| FHIR AuditEvent bidirectional mapping | Promoted into v2.0 scope: gap analysis, profile, and translator are core deliverables (Section 9) |
| Cross-org delegation chains / federated identity (issue #6 Q3) | Partially served by `org_id`/`owner_org_id` plus `authorizing.org_id`; full HIE federation deferred until a concrete deployment drives requirements |
| Real-time vs batch emission guidance (issue #6 Q5) | Reference implementation docs, not schema |

## 15. Validation Suite

The draft schema was exercised against a positive corpus and a negative corpus that combines minimal counter-examples and adversarial probes. Every case is committed and runnable under `pytest tests/` and `python scripts/validate_examples.py`.

| Suite | Cases | Result |
|---|---|---|
| Positive examples (must validate) | 7 | 7 pass |
| Negative cases (must fail, includes adversarial probes) | 13 | 13 fail |
| FHIR R5 translation (must produce valid AuditEvent) | 7 | 7 valid |

Positive corpus -- 5 core attribution scenarios plus 2 RFC §7.2 session-lifecycle convention examples:

- Core: agent MCP read, agent UI-driving write, human override, depth-2 sub-agent export, human-direct read.
- Session lifecycle: agent session start (`CREATE` on `AgentSession`), agent session end (`UPDATE` with `action.name: agent_session_end`).

Notable findings carried into the spec:

- The presence/value asymmetry in `dependentRequired` required an explicit bidirectional conditional for the chain fields (Section 6, rule 2).
- Rule interaction makes agent-initiated `OVERRIDE` unsatisfiable with a non-obvious error message (Section 6.1).
- Prompt content smuggled as nested metadata or as an extra `delegation` property is rejected by the scalar-metadata and strict-validation rules inherited from v1.1.

## 16. Reference: Full Example Event

Agent reading a patient record through an MCP gateway under its own delegated credential (supervised, depth 1).

```json
{
  "schema_version": "2.0",
  "event_id": "7c1a2b3d-4e5f-4a6b-8c9d-0e1f2a3b4c5d",
  "timestamp": "2026-06-12T14:02:11Z",
  "service": { "name": "bh-intake-api", "environment": "prod" },
  "correlation": { "request_id": "req_agent_mcp_001", "trace_id": "trace_a1b2c3d4e5" },
  "actor": {
    "subject_id": "agent_cred_009",
    "subject_type": "agent",
    "org_id": "org_77",
    "roles": ["care_coordinator_delegate"]
  },
  "delegation": {
    "acting": {
      "subject_id": "agent_inst_4471",
      "subject_type": "agent",
      "agent": {
        "interface": "mcp",
        "vendor": "vendor_a",
        "model_family": "model_x",
        "model_version": "x-3.1",
        "harness": "mcp_gateway",
        "harness_version": "0.4.2"
      }
    },
    "authorizing": { "subject_id": "user_123", "subject_type": "human", "org_id": "org_77" },
    "delegation_type": "supervised",
    "agent_session_id": "agsess_01J9X0001",
    "chain_depth": 1
  },
  "action": { "type": "READ", "phi_touched": true, "data_classification": "PHI" },
  "resource": { "type": "Patient", "id": "pat_456", "patient_id": "pat_456" },
  "outcome": { "status": "SUCCESS" }
}
```

Additional examples (UI-driving write, human override, depth-2 sub-agent chain, human-direct read) are in [`examples/2.0/`](../../examples/2.0/).
