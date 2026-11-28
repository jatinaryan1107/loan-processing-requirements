"""Human-readable SRS and full traceable JSON projection."""

import copy

from ..storage import now


def payload(project, final=False):
    """Separate the adopted baseline from retained, explicitly excluded review evidence."""
    result = copy.deepcopy(project)
    if final:
        excluded = result.get("excluded_requirements", [])
        excluded_ids = {r["id"] for r in excluded}
        excluded.extend(
            r for r in result["requirements"] if r["status"] != "approved" and r["id"] not in excluded_ids
        )
        result["excluded_requirements"] = excluded
        result["requirements"] = [r for r in result["requirements"] if r["status"] == "approved"]
        result["baseline_scope"] = (
            "Only the approved records in requirements form the adopted baseline. excluded_requirements, original sources and audit history are retained evidence, not implementation obligations."
        )
    return result


def markdown(project, final=False):
    project = payload(project, final)
    lines = [
        f"# {project['name']}",
        "",
        f"{'Approved baseline' if final else 'Draft'} software requirements specification",
        "",
        f"Generated: {now()}",
        "",
        project["description"],
        "",
        "Domain: requirements for loan-processing software. This system does not process loans or provide legal determinations.",
        "",
        f"Jurisdiction: {project['jurisdiction']}",
        f"Synthetic demonstration project: {project['synthetic']}",
        "",
        "## Requirements and acceptance criteria",
        "",
    ]
    if final:
        lines += [project["baseline_scope"], ""]
    for req in project["requirements"]:
        lines += [
            f"### {req['id']} — {req['status']}",
            req["statement"],
            "",
            f"Type: {req['kind']} | Categories: {', '.join(req['categories'])} | Priority: {req['priority']} | Risk: {req['risk']}",
            f"Source: {req['source_id']}",
            f"Original evidence: {req['original_text']}",
            f"Justification: {req['justification']}",
            "",
            "Acceptance criteria (approved with this requirement):"
            if req["status"] == "approved"
            else "Acceptance criteria (draft; human review required):",
        ]
        lines += [f"- {criterion}" for criterion in req["acceptance_criteria"]]
        lines += [
            "",
            "User story:",
            f"As an authorised stakeholder, I want the software behavior described in {req['id']}, so that {req['justification']}",
            "",
            "Use case:",
            f"- Actor: authorised user specified by {req['id']}; confirm during design.",
            "- Preconditions: agreed input data and relevant role permissions are available.",
            f"- Main outcome: {req['statement']}",
            "- Alternative path: invalid input is rejected with an agreed error; confirm exception details.",
            "",
            f"Dependencies: {', '.join(req['dependencies']) or 'Not yet specified'}",
            f"Assumptions: {'; '.join(req['assumptions'])}",
            "",
        ]
    lines += [
        "## Traceability matrix",
        "",
        "| Requirement | Original source | Status | Controls |",
        "|---|---|---|---|",
    ]
    for req in project["requirements"]:
        mappings = [m["id"] for m in project["mappings"] if req["id"] in m["requirement_ids"]]
        lines.append(
            f"| {req['id']} | {req['source_id']} | {req['status']} | {', '.join(mappings) or 'Unmapped'} |"
        )
    if final and project.get("excluded_requirements"):
        lines += [
            "",
            "## Excluded requirements",
            "",
            "These records are retained for decision traceability. They are outside the approved implementation baseline.",
            "",
        ]
        for req in project["excluded_requirements"]:
            lines += [
                f"### {req['id']} — {req['status']}",
                req["statement"],
                f"Original source: {req['source_id']}",
                "",
            ]
    lines += [
        "",
        "## Compliance review",
        "",
        "All mappings are advisory. No authoritative financial regulation is bundled. A rejected mapping documents disposition, not compliance or waived legal obligations.",
        "",
    ]
    snapshot = project.get("compliance_snapshot")
    if snapshot:
        lines += [
            f"Reviewed knowledge-base digest: {snapshot['corpus_sha256']}",
            f"Applicability snapshot: {snapshot['applicability_sha256']} | Evaluated: {snapshot['evaluated_at']}",
            "",
        ]
    for m in project["mappings"]:
        lines += [f"### {m['control']} — {m['status']}", m["reason"], m["interpretation"]]
        if m["source"]:
            s = m["source"]
            lines += [
                f"Source: {s['id']} — {s['title']}, clause {s['clause']}, version {s['version']}, effective {s['effective_date']}",
                f"Jurisdiction: {s['jurisdiction']}; applicability: {s['applicability']}",
                f"Evidence: {s['text']}",
            ]
        for h in m["history"]:
            lines.append(f"Review: {h['decision']} by {h['actor']} at {h['at']}; {h['note']}")
        lines += [""]
    lines += ["## SDLC recommendation and workflow", ""]
    if project["sdlc"]:
        sdlc = project["sdlc"]
        lines += [f"Selected: {sdlc['selected_model']} ({sdlc['status']})", sdlc["uncertainty"], ""]
        for item in sdlc["rankings"]:
            lines += [f"### {item['model']}: {item['score']}/{item['max_score']}"] + [
                f"- {reason}" for reason in item["rationale"]
            ]
        for phase in sdlc["workflow"]:
            lines += [
                "",
                f"### {phase['phase']}",
                *[f"- {a}" for a in phase["activities"]],
                f"Roles: {', '.join(phase['roles'])}",
                f"Deliverables: {', '.join(phase['deliverables'])}",
                f"Security: {phase['security_checkpoint']}",
                f"Gate: {phase['approval_gate']}",
                f"Entry: {phase['entry']}",
                f"Exit: {phase['exit']}",
            ]
    else:
        lines.append("Lifecycle factors have not been assessed.")
    lines += ["", "## Risks and open issues", ""]
    for f in project["flags"]:
        lines.append(
            f"- [{f['severity']}] {f['type']}: {f['message']} ({', '.join(f['requirement_ids']) or 'Project scope'}). Mitigation: {f['question']}"
        )
    for q in project["questions"]:
        lines.append(f"- [{q['status']}] {q['text']} Answer: {q.get('answer', 'Pending')}")
    lines += ["", "## Input sources", ""]
    for s in project["sources"]:
        lines += [
            f"### {s['id']} — {s['source_name']}",
            f"Stakeholder: {s['stakeholder']} | Captured: {s['created_at']}",
            "Source disposition: excluded from requirement extraction; retained as evidence."
            if s.get("excluded")
            else "Source disposition: supporting evidence; original input is not itself an approved requirement.",
            s["text"],
            "",
        ]
    lines += ["## Audit trail", ""]
    for event in project["audit"]:
        lines.append(
            f"- {event['at']} — {event['actor']} ({event['role']}): {event['action']}; {event['details']}"
        )
    lines += ["", "## Agent execution records", ""]
    for r in project["runs"]:
        lines.append(
            f"- {r['at']} — {r['agent']} / {r['provider']} / v{r['version']}: {r['outcome']}; confidence {r['confidence']}; inputs {', '.join(r['input_ids'])}"
        )
    return "\n".join(lines) + "\n"
