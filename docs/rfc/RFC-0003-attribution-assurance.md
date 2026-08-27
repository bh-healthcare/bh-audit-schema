<!--
RFC 0003: Attribution Assurance and the Unattributed Agent
Repository: bh-healthcare/bh-audit-schema
This document is a draft for community discussion. This is not a release.
-->

# RFC 0003: Attribution Assurance and the Unattributed Agent

| | |
|---|---|
| **RFC** | 0003 |
| **Title** | Attribution Assurance and the Unattributed Agent |
| **Status** | Draft for discussion. Target version and naming settled 2026-08-14; ordering added 2026-08-26; one open item in section 12.2, plus one deferred to RFC 0002 |
| **Target** | bh-audit-schema v2.1 |
| **Tracking issue** | [#13](https://github.com/bh-healthcare/bh-audit-schema/issues/13) |
| **Companion** | [RFC 0001: AI Agent Attribution and the Human-Agent Delegation Chain](RFC-0001-agent-attribution-github.md), [RFC 0002: Enforced Attribution Emission for MCP Tool Calls](https://github.com/bh-healthcare/bh-mcp-attribution/blob/main/docs/rfc/RFC-0002-mcp-attribution-enforcement.md) |
| **Depends on** | bh-audit-schema `2.0` |
| **Discussion period** | 14 days minimum, closing 2026-09-06 (minor version with a conditional required field, per [GOVERNANCE.md](../../GOVERNANCE.md)) |
| **Supersedes** | none |
| **Created** | 2026-08-23 |

---

## Table of Contents

1. [Summary](#1-summary)
2. [Scope and Non-Goals](#2-scope-and-non-goals)
3. [Two Gaps, Demonstrated](#3-two-gaps-demonstrated)
4. [The `attribution` Object](#4-the-attribution-object)
5. [Conditional Validation](#5-conditional-validation)
6. [What Silence Means in v2.1](#6-what-silence-means-in-v21)
7. [Assurance and Emission Tier Are Independent Axes](#7-assurance-and-emission-tier-are-independent-axes)
8. [Rejected Alternatives](#8-rejected-alternatives)
9. [FHIR R5 Translation](#9-fhir-r5-translation)
10. [Migration and Cross-Package Impact](#10-migration-and-cross-package-impact)
11. [Validation Suite](#11-validation-suite)
12. [Decisions and Open Items](#12-decisions-and-open-items)
13. [Consequences for the Reference Implementation Schedule](#13-consequences-for-the-reference-implementation-schedule)

---

## 1. Summary

RFC 0001 established that an audit event can name three identities: the authenticating identity in `actor`, and the acting agent and authorizing human in `delegation`. It did not establish how strongly any of that is known, and it did not provide a way to record that an agent acted and no authorizing human could be named.

Those two omissions look like one design preference and one edge case. They are neither. Section 3 demonstrates, against the released schema and its validation corpus, that:

1. A token-derived attribution and an agent-supplied attribution serialize to **byte-identical** v2.0 events. The distinction between the strongest and the weakest binding is not merely absent from the record, it is unrecoverable from it.
2. An event stating that an agent authenticated and no authorizing human could be named is **rejected by v2.0**. It is not ambiguous, it is invalid. The honest shape of that event is byte-for-byte the shape of negative test case `01_agent_actor_without_delegation.json`, which v2.0 exists to reject.

Consequence two is the more serious. RFC 0002 section 6 commits the enforced tier to emitting a record for every denial, on the grounds that a denial leaving no record is indistinguishable from a call that was never attempted. v2.0 cannot represent that record. The tier's most important event is the one the format forbids.

This RFC proposes a single new top-level object, `attribution`, carrying a closed `level` enum and an open `method` string, and four conditional validation rules. One field resolves both gaps because both are the same question asked twice: what does this event claim about how its own attribution was established?

## 2. Scope and Non-Goals

**In scope:** recording the provenance of an event's attribution, and recording the case where attribution could not be established.

**Out of scope:**

- Judging whether a given level is good enough. That is a deployment policy decision and belongs to the enforcing layer, not the record. The schema's job is to make the level legible, not to set a floor.
- Changing the three-role model, the delegation chain constraints, or the `actor` semantics established in RFC 0001. None of those move.
- Human-proxy delegation. Deferred in RFC 0001 section 14, still deferred.
- Detecting a non-cooperating agent. RFC 0001 section 3 and RFC 0002 section 2.1 state this limit and this RFC does not soften it. An agent driving a user interface under a human's credentials produces a `verified` event describing a human acting directly, and that is correct as far as the target system can know.

## 3. Two Gaps, Demonstrated

Both claims below were checked by validating candidate events against `schema/versions/2.0/audit_event.schema.json` with the format checker enabled. Section 11 gives the harness.

### 3.1 Gap one: weak and strong bindings are indistinguishable

RFC 0002 section 4 defines three resolution paths of unequal strength. A token presented on the session, where the issuer asserts `sub` and the nested `act` chain, cannot be forged by the agent. Operator configuration mapping a credential to an authorizing identity is an assertion by the operator, not proof of a human's involvement in this call. A per-call attribution block supplied by the agent is forgeable by the agent.

Take two events. In the first, the authorizing human came from an ID-JAG token. In the second, the agent supplied that identity itself. Serialize both as v2.0 with keys sorted, and they are identical strings. Both validate. Nothing in the record distinguishes them, and nothing added later can recover the distinction, because the information was never in the event.

This is not a validation failure. It is silent degradation, which is worse. A deployment resolving every call from agent-supplied metadata emits events that a downstream consumer cannot tell apart from a deployment running full token exchange. RFC 0001 section 11 draws the tier boundary precisely to prevent a claim of guaranteed attribution from resting on an honor system, and then the event format discards the one fact that would let a consumer check.

### 3.2 Gap two: the enforced tier cannot record its own denials

v2.0 carries this conditional rule:

```json
{
  "if":   { "properties": { "actor": { "properties": { "subject_type": { "const": "agent" } },
                                       "required": ["subject_type"] } },
            "required": ["actor"] },
  "then": { "required": ["delegation"] }
}
```

An agent authenticating identity requires a delegation block. The delegation block requires `authorizing`, whose `subject_type` is `const: "human"`. So an event asserting "an agent presented credentials and no authorizing human could be named" requires a delegation block that requires the very identity the event exists to report as missing.

Validated results for the four shapes a producer could reach for:

| Candidate denial event | v2.0 verdict | Cost |
|---|---|---|
| `actor.subject_type: "agent"`, no delegation | **Rejected**, `'delegation' is a required property` | The honest shape does not validate |
| `actor.subject_type: "service"` | Valid | Mislabels an agent as deterministic code, against the taxonomy in RFC 0001 section 4.1 |
| `actor.subject_type: "human"` | Valid | Mislabels an agent as a person |
| delegation with `authorizing.subject_id: "UNKNOWN"` | Valid | Fabricates a human. Worst of the four, and the only one that leaves a well-formed record |
| Emit nothing | n/a | Forbidden by RFC 0002 section 6. Makes the denial rate unmeasurable, which is the main signal a deployment is misconfigured |

Every available option either fails validation or corrupts a field whose meaning RFC 0001 section 4.2 made load-bearing. The first row is the important one: the honest shape is the same shape as negative case `01_agent_actor_without_delegation.json`. The reference implementation's most important event is currently a test case for invalidity.

### 3.3 This is not only about denials

`build_denial_event` is the obvious site, but the gap is wider.

RFC 0002 section 8 provides a `BH_FAIL_OPEN` escape hatch and commits that when the door is open, the fact is recorded. A fail-open call that proceeds without resolvable attribution is a **successful** agent tool call with no authorizing human. That event hits the same wall as the denial: `actor` is an agent, no delegation block exists to write, validation fails. The escape hatch that exists so the record can be read honestly after an incident produces an event the format rejects.

The same shape arrives from any future ingest of instrumented or advisory-tier events, where an agent self-reports an action without naming an authorizer. A field on the epistemic axis covers all three cases. A fix scoped to denials covers one.

## 4. The `attribution` Object

A new optional top-level object.

```json
"attribution": {
  "level": "verified",
  "method": "id_jag"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `level` | closed enum | yes | Normative. Consumers reason over this |
| `method` | string, 1 to 64 chars | no | Forensic detail. Open vocabulary, grows without schema churn |

### 4.1 Levels

| Level | Meaning | Forgeable by the agent |
|---|---|---|
| `verified` | Derived from a token whose issuer asserted the identities | No |
| `bound` | Operator configuration maps a credential or session to an authorizing identity | No, but it is the operator's assertion rather than proof of a human's involvement in this call |
| `asserted` | Supplied by the agent in the call itself | Yes |
| `unattributed` | An agent was involved and no authorizing human could be named. No delegation block is present | n/a |

The split between a closed `level` and an open `method` is deliberate. A consumer writing a query needs a small fixed vocabulary it can filter on and reason about completely. An investigator reading a single event wants to know it came from an ID-JAG token rather than a bearer token with an `act` claim. Those are different audiences with different stability requirements, and merging them would force a schema revision every time a new credential type appears.

### 4.2 There is no `unknown` level

A producer that cannot determine how it established an attribution is describing `asserted`. It accepted an identity it cannot vouch for, which is exactly what `asserted` means. Adding `unknown` would create a second way to say "no claim", and a value that every uncertain producer defaults to becomes the modal value and carries no information.

`unattributed` is not `unknown`. It is a positive assertion: resolution ran and produced no authorizing human. That is a finding, not an absence of one.

### 4.3 One level for the block, reporting the weakest binding

A delegation block holds at least two identities, and they can be established by different mechanisms. The authorizing human may come from a token while the acting agent identity comes from configuration.

`level` describes the block as a whole and reports the **weakest** mechanism that contributed to it. Weakest is defined by the ordering in section 4.4. The alternative, a level per identity, is more precise and worse: every downstream consumer would have to invent its own rule for combining two or three levels into the single predicate a query needs, and those rules would differ between consumers. One field means one predicate, and the enforced-tier query is `level IN ('verified', 'bound')`.

Stated plainly because it is a real commitment: reversing this later breaks consumer filters. Per-identity assurance designs for a problem no implementer has reported.

### 4.4 The levels are ordered, and the order is normative

The four levels form a total order, weakest to strongest:

`unattributed` < `asserted` < `bound` < `verified`

An implementation comparing a level against a threshold ***MUST*** compare on position in this sequence and ***MUST NOT*** compare the serialized strings. Lexical order of the four values is `asserted` < `bound` < `unattributed` < `verified`, which places the weakest level above bound. A string comparison against a bound threshold therefore admits `unattributed`, which is the one value the threshold exists to exclude. The two orderings agree on the other three values, so an implementation written before `unattributed` existed passes every test it has and fails only on the case the level was added to express.

This applies to query languages as well as to programming languages. A threshold in SQL is expressed as explicit set membership or as a join against a rank table, never as a string comparison on the stored value.

The position is a property of this specification and is not serialized. An event carries level as a string and carries nothing else about its rank. See section 8.7.

`unattributed` sorts lowest although it is not a weaker binding but the absence of one. The order exists to answer one question, whether an event meets a stated floor, and for `unattributed` the answer is no at every floor. Section 2 is unchanged: defining the order is not setting the floor. Where the floor sits remains a deployment policy decision.

## 5. Conditional Validation

Four rules, of which one amends a v2.0 rule.

**R1, new.** If `delegation` is present, `attribution` is required and `level` must be one of `verified`, `bound`, `asserted`.

A delegation block that does not say how it is known is the second way to say nothing that v2.0 was built to eliminate. This is the rule that makes the field load-bearing rather than decorative.

**R2, new.** If `level` is `unattributed`, `delegation` is forbidden.

`unattributed` asserts there is no delegation block to describe. Permitting both would allow an event to claim an authorizing human and simultaneously claim none could be found.

**R3, new.** If `level` is `verified`, `bound`, or `asserted`, `delegation` is required.

The mirror of R2. An assurance level other than `unattributed` describes a delegation block, so one must exist.

**R4, amended from v2.0.** If `actor.subject_type` is `agent`, then either `delegation` is present, or `attribution.level` is `unattributed`.

This relaxes the v2.0 rule quoted in section 3.2, and the relaxation is narrow by design. An agent authenticating identity still has to be explained. What changes is that "could not be attributed" becomes an available explanation, stated explicitly, rather than the only unavailable one. Silence remains invalid: negative case `01_agent_actor_without_delegation.json`, which carries neither block, is still rejected under v2.1.

**Amendment to the OVERRIDE rule.** v2.0 already forbids `delegation` on an `OVERRIDE` action and requires a human actor. v2.1 also forbids `attribution`. An override is a human interrupting an agent session, performed by a named person, so there is no agent attribution to state and `unattributed` on such an event would be a contradiction.

## 6. What Silence Means in v2.1

v2.0 made the absence of `delegation` mean something specific: a direct, non-delegated action. RFC 0001 section 13 states it as the absence "positively asserting" direct action, and section 4.2 names the mechanism, which is that the schema version marker declares which attribution model an event asserts.

v2.1 uses the same mechanism a second time and narrows the claim by one step:

| `delegation` | `attribution` | The event asserts |
|---|---|---|
| absent | absent | No agent was involved |
| absent | `level: unattributed` | An agent was involved and could not be attributed |
| present | `level: verified` / `bound` / `asserted` | An agent was involved, here is who authorized it, and here is how strongly that is known |
| present | absent | Invalid |
| absent | `level` other than `unattributed` | Invalid |

The first row is unchanged from v2.0, which is why this is additive for producers in agent-free environments. Nothing about their events or their meaning changes beyond the version string.

The middle row is the new capability. Before v2.1, an event could not distinguish "no agent" from "an agent I could not name", and the format resolved that ambiguity by rejecting the second case rather than by expressing it.

## 7. Assurance and Emission Tier Are Independent Axes

These get conflated on first reading, and conflating them makes both useless.

**Emission tier** is a property of a deployment's emission path: can the agent reach the target system without an event being produced? Enforced means no, instrumented means not without modifying the runtime, advisory means yes.

**Assurance level** is a property of a single event: how was this attribution established?

An enforced-tier gateway emitting `asserted` events is a real and honest configuration. Emission is guaranteed, and the content of what is emitted is agent-supplied. The deployment can truthfully say every agent action on the controlled path is recorded, and it cannot truthfully say the authorizing human named in those records was verified. Both facts are now in the record.

The schema does not constrain the combination, because the schema describes events and the tier describes deployments. An advisory-tier producer emitting `verified` is not forbidden here. It is implausible, and a consumer noticing implausible combinations is a use for the field rather than an argument against it.

## 8. Rejected Alternatives

### 8.1 An `error_type` convention with a documented carve-out

Use `outcome.error_type: "no_attribution"` plus a rule that a `DENIED` event with that error type means an agent was involved but unattributable.

Rejected on three counts, the first fatal. It does not fix gap two at all: the event still fails validation, because the rejection comes from the `actor` and `delegation` rule and nothing in `outcome` affects it. Second, `error_type` is a free string with a 128 character limit, so the distinction would live in a convention a consumer has to know rather than in a value it can enumerate, which is the reviewer convention this body of work exists to replace. Third, `error_type` is only present on `FAILURE` and `DENIED`, so it cannot express the fail-open success case in section 3.3.

### 8.2 A distinct `action.type`

Add an action type such as `AGENT_DENIED` and exempt it from the delegation requirement.

Architecturally available, and there is precedent: `OVERRIDE` already carries a bespoke conditional rule including `not: { required: ["delegation"] }`. Rejected anyway. `ActionType` is a closed enum, so this is a schema change of the same cost with worse semantics. `action.type` describes what was attempted, and a denied chart read is still an attempted read, so folding the attribution state into it destroys the ability to ask what agents are trying to do separately from how well they are attributed. And it covers denials only, leaving fail-open and any future advisory ingest unrepresentable.

### 8.3 Make `delegation.authorizing` optional

Rejected without qualification. The constraint that a delegation block always names a human authorizer is the property that makes the record able to name an accountable person, and RFC 0001's rule that no agent may occupy the authorizing position at any depth depends on that field being present and human. Relaxing it to solve a reporting problem would trade the guarantee for the report.

### 8.4 Carry an agent descriptor inside `attribution` for the unattributed case

Tempting, because knowing which agent hit the wall is operationally most of the value of a denial event.

Rejected. `actor` already names the agent credential with `subject_type: "agent"`, so an unattributed event is not anonymous. Adding a second location where agent facts can live recreates precisely the failure documented in the `onBehalfOf` analysis: an optional field in an alternative location that queries do not reach, so the data is technically present and practically absent.

The cost is real and is accepted rather than hidden. On an unattributed event, `interface`, `vendor`, `model_family` and the rest of the agent descriptor are lost, because that descriptor lives in `delegation.acting.agent` and there is no delegation block. Denials cannot be segmented by interaction surface. If that turns out to matter to an implementer, the answer is a future revision with evidence behind it, not a speculative second identity path now.

### 8.5 Keep assurance in the reference library only

Rejected. A level recorded only in the enforcing library is invisible to every consumer querying the audit store, which is the only place the distinction is needed. It also cannot address gap two, since that is a validation failure in the shared format and no amount of library-local state changes what validates.

### 8.6 Make `attribution` fully optional, deferring R1 to a major version

This would make v2.1 a purely additive minor bump with no conditional required field, which is the cleanest possible versioning story. Considered and rejected in section 12.1.

The cost is that an event with a delegation block and no attribution block would be legal and would mean nothing determinate, which is the hole R1 exists to close. Half of this RFC's value is the guarantee that if an event names an authorizing human, it also says how that name was obtained. Without R1 there is no such guarantee, only a field some producers populate.

### 8.7 Serialize the rank alongside the level

Carry a numeric `rank` next to `level`, or replace the enum with an integer.

Rejected. Two encodings of one fact drift, and the format would then need a validation rule asserting they agree. It also puts the numbering in the wire format, so inserting a level between two existing ones becomes a breaking change to every stored event rather than a revision to this document. The order is a property of the vocabulary and belongs with the specification that defines the vocabulary.

## 9. FHIR R5 Translation

The existing translator implements a bounded extension set for the gaps R5 does not cover. `attribution` follows that pattern:

- `level` becomes an extension at `{EXT}/attribution-level` as a `valueCode`.
- `method` becomes `{EXT}/attribution-method` as a `valueString`. Nothing is lost on the round trip.

Two translator changes are required, and the second is not cosmetic.

First, the extension array is currently built inside `if delegation:`, so an event with no delegation block carries no extensions at all. That gate has to widen, or unattributed events translate with the attribution level silently dropped.

Second, and more importantly, the agent slicing has exactly two branches. With a delegation block it emits `authenticating-identity`, `acting-identity` and `authorizing-identity`. Without one it falls to an `else` that emits a single slice with role `direct` and `requestor: true`. An unattributed event has no delegation block, so it would take the `else` branch and the R5 output would assert that the agent acted **directly, as the requestor**. That is the false claim this entire body of work exists to prevent, generated automatically by the translator, from a correctly formed source event.

A third branch is required, emitting a slice with a role that names the state rather than defaulting to `direct`.

Honest limitation: R5 AuditEvent has no native concept of attribution assurance, so this rides on an extension. An R5 consumer that does not know the extension sees an authenticating agent and no assurance statement. The distinction is preserved in the native format and available but ignorable in R5, which is the same trade the delegation extensions already make.

## 10. Migration and Cross-Package Impact

### 10.1 Producers

| Producer situation | Required change |
|---|---|
| Agent-free environment | Update `schema_version` to `2.1`. Nothing else |
| Emits delegation blocks | Add `attribution` to every event carrying delegation. Determine the level from the resolution path actually used, and do not default it to `verified` |
| Enforcing layer | Also emit `unattributed` events on the denial and fail-open paths, which were previously unrepresentable |

The middle row is the migration work, and the instruction not to default the level is the whole point. A producer that cannot tell which path produced an attribution is describing `asserted`, per section 4.2.

### 10.2 Consumers

Queries of the form "all agent actions with a named authorizing human" continue to work unchanged, because such events still carry a delegation block. Two additions are worth making at migration time rather than later:

- A deployment health query on `attribution.level = 'unattributed'`, which was previously unrepresentable and is now the clearest signal that an enforcing layer is misconfigured or that an agent is reaching a tool without credentials.
- A posture query on the distribution of `level` across a service, which answers whether a deployment claiming enforced-tier attribution is actually resolving identities from tokens.
- A threshold on `attribution.level` is expressed as explicit set membership or as a join against a rank table. A string comparison in SQL is lexical and admits `unattributed` above `bound`. See section 4.4.

### 10.3 Downstream packages

Verified against the current state of each repository rather than assumed:

| Package | Current state | Impact |
|---|---|---|
| `bh-audit-logger` | `SCHEMA_VERSION = "2.0"`, version-aware `load_schema(version)`, vendors 1.0, 1.1 and 2.0 | Low. Drop in a `versions/2.1/` directory, widen the `target_schema_version` literal, move the default. The negotiation machinery already exists |
| `bh-fastapi-audit` | `SCHEMA_VERSION = "1.1"`, `target_schema_version: Literal["1.0", "1.1"]`, vendors 1.0 and 1.1 only | None. It is not on 2.0, so a 2.1 release does not touch it. Its own gap to v2 is a separate matter and should not be folded into this one |
| `bh-audit-logger-examples` | Consumes whatever the logger emits | Version references and a full example run once the logger moves |
| `bh-mcp-attribution` | Pinned to `v2.0.0`, emitter not yet implemented | Pin moves to `2.1.0` on release day. v0.1.0 ships 2026-09-06 with v2.1, per RFC 0002 section 13.2 |

### 10.4 Repository artifacts

Per the schema governance rules, a v2.1 release requires: the new versioned schema plus a byte-identical root pointer copy, `examples/2.1/` with the corpus in section 11, `docs/field-definitions.md`, `docs/versioning.md` version history, `docs/event-types.md` for the new outcome pattern, `docs/controls-mapping.md` where the assurance distinction bears on HIPAA and Part 2 alignment, `docs/query-examples.md` for the two queries in section 10.2, the FHIR gap analysis and profile document for the extension set in section 9, `schema/versions/2.1/CHANGELOG.md`, and the root `CHANGELOG.md`.

## 11. Validation Suite

The design in sections 4 and 5 was drafted as a complete candidate schema and run against the real released corpus before this document was written. Results:

| Check | Result |
|---|---|
| The 7 v2.0 positive examples still validate against v2.0, unchanged | 7 of 7 valid |
| The 7 positives re-marked `2.1` with no `attribution` block | The 4 delegation-bearing events rejected on `'attribution' is a required property`, the 3 others valid. R1 bites where intended and nowhere else |
| The 7 positives re-marked `2.1` with `attribution` added where delegation exists | 7 of 7 valid |
| The 13 v2.0 negative examples re-marked `2.1` | 13 of 13 still rejected. v2.1 legalizes nothing v2.0 forbade |
| The denial shape from section 3.2, with `level: unattributed` | Valid under v2.1, rejected under v2.0 |
| The fail-open success shape from section 3.3 | Valid under v2.1, rejected under v2.0 |
| A `verified` and an `asserted` event, with `attribution` stripped and re-marked `2.0` | Both valid, and byte-identical with keys sorted. Gap one demonstrated rather than asserted |
| 8 new negative shapes for the R1 to R4 boundaries | 8 of 8 rejected |

### 11.1 Proposed v2.1 corpus

11 positive and 21 negative, from 7 and 13.

Positive adds four: an enforced-tier denial at `unattributed`, a fail-open success at `unattributed`, an `asserted` call event, and an `attribution` block carrying `level` with `method` omitted. The four existing agent examples gain an `attribution` block, with at least one at `bound` so the corpus does not exercise a single level.

Negative adds eight: delegation without attribution, `unattributed` alongside a delegation block, a non-`unattributed` level without a delegation block, a level outside the enum, `attribution` missing `level`, `attribution` with an extra property, an `OVERRIDE` carrying `attribution`, and an agent actor carrying neither block.

### 11.2 An implementation note on error messages

R2, R4 and the OVERRIDE amendment are expressed with `not` and `anyOf`, and JSON Schema reports those by echoing the whole instance rather than naming the offending field. Confirmed in the run: a level outside the enum reports `attribution/level: 'unattributed' was expected`, which is misleading, since the real fault is an enum violation and `unattributed` is not the only acceptable value.

A producer should validate these invariants itself and raise its own message. Relying on validator output here gives an operator a wall of JSON and the wrong diagnosis.

### 11.3 Ordering conformance

The ordering in section 4.4 is not expressible in JSON Schema and is not covered by the corpus in 11.1. An implementation claiming conformance demonstrates the full threshold matrix: each of the four levels against each of the three thresholds `asserted`, `bound`, `verified`, twelve cases. The case that distinguishes a conforming implementation from a lexical one is `unattributed` against a `bound` threshold, which denies.

## 12. Decisions and Open Items

### 12.1 Settled

**Target version: v2.1.** 

The levels are totally ordered and the order is normative. Decided 2026-08-26, during the discussion period.

The draft as published used "weakest" normatively in section 4.3 without defining an order. The natural derivation from the level names is string comparison, and string comparison places `unattributed` above `bound`. The three levels that predate `unattributed` sort identically under both orderings, so the defect was not observable until the fourth level was proposed. Recorded rather than silently corrected, because the failure mode generalizes: a ranked closed enum whose rank is not stated normatively gets a rank invented independently by every implementer.

Decided 2026-08-14.

`docs/versioning.md` already lists "adding conditional validation requirements" and "relaxing validation constraints" as non-breaking, which describes R2, R3, R4 and the OVERRIDE amendment exactly. R1 was the question, because it makes a new field required whenever an existing optional block is present, and the governance rules stated that a required field is never added without a major bump.

The rule's purpose is to prevent existing records from being silently invalidated, and `schema_version` being a `const` per version already prevents that absolutely. A v2.0 event is never validated against v2.1. No stored record changes meaning and no consumer reinterprets history. What a conditionally required field does break is a producer that updates its version string without adding the field, and that producer gets a hard validation failure at the point of emission, which is where the problem should surface.

The rule was stated too broadly rather than being wrong, so it has been tightened rather than waived. `docs/versioning.md` now distinguishes a field required unconditionally at the root, which stays a major bump, from a field required only inside an already-optional object, which is a minor bump. The reasoning is recorded there so this decision does not have to be reconstructed from an RFC later.

The counter-argument is preserved because it should be raised again if this comes up in review: reaching for the intent of a governance rule while proposing the change that rule constrains is exactly the moment to be suspicious of one's own reasoning. The defence is that the tightening is written down as general policy, applies to changes not yet contemplated, and would have been the right wording before this RFC existed.

A migration guide is written regardless of the version number, because the producer-side work in section 10.1 is real whether or not the major digit moves.

**Naming: `attribution`, with levels `verified`, `bound`, `asserted`, `unattributed`.** Decided 2026-08-14.

`attribution` because the block is the event's statement about its own attribution, and because `assurance: unattributed` reads as a category error. `verified` / `bound` / `asserted` over `attested` / `configured` / `claimed` because each names the mechanism rather than an editorial judgement about it, and because `bound` states what the operator did, which `configured` does not.

Permanent once released. Recorded with the date so it is visible as a decision rather than as an accident of whoever wrote the first draft.

**One level per delegation block, reporting the weakest binding.** See section 4.3. Per-identity assurance designs for a problem no implementer has reported, and reversing this later breaks consumer filters.

### 12.2 Open

**1. Should `method` become a closed enum in a later version?** Left open deliberately. Closing it early forces a schema revision for each new credential type; leaving it open forever means no consumer can rely on it. Revisit when there is evidence about which values appear in practice.

**2. Does `asserted` belong in the enforced tier at all?** This is RFC 0002 open decision 2 and it is not resolved here. It interacts: if the enforced tier refuses agent-asserted attribution, `asserted` events come only from instrumented and advisory producers, and the level's main job becomes marking ingested events from weaker tiers. The field is needed either way, so this does not block v2.1.

## 13. Consequences for the Reference Implementation Schedule

Stated here because it is a scheduling fact that follows from a schema fact, and the two are easy to track separately until one blocks the other.

`bh-mcp-attribution` currently defines `AssuranceLevel` in `context/models.py` with no field in any emittable event to carry it, and `build_denial_event` with a documented contract for a `context=None` case that cannot produce a valid v2.0 event. Neither is a defect in that repository. Both are correct implementations of a design that its pinned schema version cannot express. `AssuranceLevel` in `context/models.py` derives its comparison from the enum's string values and satisfies section 4.4 only for the three levels that predate `unattributed`. It requires an explicit rank before `minimum_assurance` can be trusted.

The consequence is that the two releases are coupled. v2.1 lands 2026-09-06, the same day v0.1.0 ships pinned to `2.1.0`, so the walking skeleton is not blocked and the first emitted events carry the field this RFC exists to add. Retrofitting is not available: an assurance level cannot be recovered from a corpus emitted without it, because the information was never captured. That is why the two releases were coupled rather than sequenced.

This decision belongs before v2.1 releases on 2026-09-06.
