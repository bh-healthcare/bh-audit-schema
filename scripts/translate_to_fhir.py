#!/usr/bin/env python3
"""Translate bh-audit-schema v2.0 events to FHIR R5 AuditEvent resources.

Companion to `docs/fhir/fhir-r5-gap-analysis-and-profile.md`. Implements the
element mapping in §5 of that document, including the three-role attribution
slicing (authenticating / acting / authorizing) and the bounded extension set
covering G4-G6 gaps (delegation-type, agent-session-id, chain-depth,
parent-agent-session-id, agent-descriptor).

PHI discipline: only opaque identifiers cross the boundary. No free text
beyond enum-derived display strings.

Usage:
    pip install "fhir.resources>=8.0.0"
    python scripts/translate_to_fhir.py [glob]
    python scripts/translate_to_fhir.py --no-validate [glob]

Default glob: examples/2.0/*.json
"""

import argparse
import json
import sys
from glob import glob
from pathlib import Path

CANON = "https://bh-healthcare.github.io/bh-audit-schema/fhir"
EXT = f"{CANON}/StructureDefinition"
CS = f"{CANON}/CodeSystem"

ACTION_MAP = {
    "READ": "R", "CREATE": "C", "UPDATE": "U", "DELETE": "D",
    "EXPORT": "E", "LOGIN": "E", "LOGOUT": "E", "PRINT": "E",
    "OVERRIDE": "E", "OTHER": "E",
}

OUTCOME_MAP = {
    "SUCCESS": ("0", "Success"),
    "FAILURE": ("8", "Serious failure"),
    "DENIED": ("8", "Serious failure"),
}

CLASSIFICATION_MAP = {
    "PHI": "R", "PII": "N", "NONE": "U", "UNKNOWN": "U",
}


def _idref(value, type_=None):
    ref = {"identifier": {"system": f"{CANON}/Identifier/opaque", "value": value}}
    if type_:
        ref["type"] = type_
    return ref


def _attribution_agent(role_code, who_id, requestor, roles=None, extensions=None):
    agent = {
        "type": {"coding": [{"system": f"{CS}/attribution-role", "code": role_code}]},
        "who": _idref(who_id),
        "requestor": requestor,
    }
    if roles:
        agent["role"] = [{"text": r} for r in roles]
    if extensions:
        agent["extension"] = extensions
    return agent


def translate(event: dict) -> dict:
    """Translate one bh-audit-schema v2.0 event to an R5 AuditEvent dict."""
    action = event["action"]
    resource = event["resource"]
    outcome = event["outcome"]
    delegation = event.get("delegation")

    ae = {
        "resourceType": "AuditEvent",
        "id": event["event_id"],
        "meta": {"profile": [f"{CANON}/StructureDefinition/bh-audit-event"]},
        "category": [{"coding": [{"system": f"{CS}/event-category",
                                  "code": "bh-audit"}]}],
        "code": {"coding": [{"system": f"{CS}/action-name",
                             "code": action.get("name", action["type"].lower())}]},
        "action": ACTION_MAP[action["type"]],
        "recorded": event["timestamp"],
        "agent": [],
        "source": {"observer": _idref(event["service"]["name"])},
        "entity": [],
    }

    code, display = OUTCOME_MAP[outcome["status"]]
    ae["outcome"] = {"code": {
        "system": "http://terminology.hl7.org/CodeSystem/audit-event-outcome",
        "code": code, "display": display}}
    details = []
    if outcome["status"] == "DENIED":
        details.append({"coding": [{"system": f"{CS}/outcome-detail",
                                    "code": "denied"}]})
    if outcome.get("error_type"):
        details.append({"coding": [{"system": f"{CS}/error-type",
                                    "code": outcome["error_type"]}]})
    if details:
        ae["outcome"]["detail"] = details

    if delegation:
        ext = [
            {"url": f"{EXT}/delegation-type",
             "valueCode": delegation["delegation_type"]},
            {"url": f"{EXT}/agent-session-id",
             "valueString": delegation["agent_session_id"]},
        ]
        if "chain_depth" in delegation:
            ext.append({"url": f"{EXT}/chain-depth",
                        "valuePositiveInt": delegation["chain_depth"]})
        if "parent_agent_session_id" in delegation:
            ext.append({"url": f"{EXT}/parent-agent-session-id",
                        "valueString": delegation["parent_agent_session_id"]})
        ae["extension"] = ext

    actor = event["actor"]
    if delegation:
        ae["agent"].append(_attribution_agent(
            "authenticating-identity", actor["subject_id"],
            requestor=False, roles=actor.get("roles")))
        acting = delegation["acting"]
        desc = acting["agent"]
        desc_ext = [{"url": "interface", "valueCode": desc["interface"]}]
        for k in ("vendor", "model_family", "model_version",
                  "harness", "harness_version"):
            if k in desc:
                desc_ext.append({"url": k.replace("_", "-"),
                                 "valueString": desc[k]})
        ae["agent"].append(_attribution_agent(
            "acting-identity", acting["subject_id"], requestor=False,
            extensions=[{"url": f"{EXT}/agent-descriptor",
                         "extension": desc_ext}]))
        ae["agent"].append(_attribution_agent(
            "authorizing-identity", delegation["authorizing"]["subject_id"],
            requestor=True))
    else:
        ae["agent"].append(_attribution_agent(
            "direct", actor["subject_id"], requestor=True,
            roles=actor.get("roles")))

    if resource.get("patient_id"):
        ae["patient"] = _idref(resource["patient_id"], type_="Patient")

    entity = {"role": {"text": resource["type"]}}
    if resource.get("id"):
        entity["what"] = _idref(resource["id"])
    if action.get("data_classification"):
        entity["securityLabel"] = [{"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
            "code": CLASSIFICATION_MAP[action["data_classification"]]}]}]
    ae["entity"].append(entity)

    if "http" in event:
        h = event["http"]
        det = []
        for key in ("method", "route_template", "status_code"):
            if key in h:
                det.append({"type": {"coding": [{"system": f"{CS}/http-detail",
                                                 "code": key}]},
                            "valueString": str(h[key])})
        if det:
            ae["entity"].append(
                {"role": {"text": "Transaction"}, "detail": det})
        if "client_ip" in h:
            # Per FHIR companion §5: http.client_ip -> agent.network[x] on
            # the relevant slice. "Relevant slice" is the authenticating
            # agent in delegated events (the credential that connected),
            # else the single direct agent.
            target = ae["agent"][0]
            target["networkString"] = h["client_ip"]

    if "metadata" in event:
        det = [{"type": {"coding": [{"system": f"{CS}/metadata",
                                     "code": k}]},
                "valueString": str(v)}
               for k, v in event["metadata"].items() if v is not None]
        if det:
            ae["entity"].append({"role": {"text": "Metadata"}, "detail": det})

    return ae


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*",
                        help="Event JSON files or globs (default: examples/2.0/*.json)")
    parser.add_argument("--no-validate", action="store_true",
                        help="Skip R5 structural validation (no fhir.resources required)")
    args = parser.parse_args()

    if args.paths:
        files = []
        for p in args.paths:
            files.extend(glob(p))
    else:
        repo_root = Path(__file__).resolve().parent.parent
        files = sorted((repo_root / "examples" / "2.0").glob("*.json"))
        files = [str(f) for f in files]

    if not files:
        print("No files matched.", file=sys.stderr)
        return 1

    if not args.no_validate:
        try:
            from fhir.resources.auditevent import AuditEvent
        except ImportError:
            print('ERROR: fhir.resources not installed. Install with: '
                  'pip install "fhir.resources>=8.0.0"  '
                  '(or re-run with --no-validate to skip R5 validation).',
                  file=sys.stderr)
            return 2

    failures = 0
    for path in sorted(files):
        with open(path) as f:
            event = json.load(f)
        if event.get("schema_version") != "2.0":
            continue
        resource = translate(event)
        name = Path(path).name
        if args.no_validate:
            print(f"  TRANSLATED  {name} (agents: {len(resource['agent'])})")
            continue
        try:
            AuditEvent.model_validate(resource)
            print(f"  VALID R5 AuditEvent  {name} "
                  f"(agents: {len(resource['agent'])})")
        except Exception as exc:
            failures += 1
            print(f"  INVALID  {name}: {exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
