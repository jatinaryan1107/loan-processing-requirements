"""Filter policy eligibility, propose mappings and track review freshness."""

import json
from datetime import date
from pathlib import Path
from .. import retrieval
from ..storage import digest, now, run, uid


UNSUPPORTED = "No verified source available / requires compliance officer review."


def load_policies():
    policies = json.loads(
        (Path(__file__).resolve().parents[1] / "knowledge" / "policies.json").read_text(encoding="utf-8")
    )
    if not isinstance(policies, list) or any(not isinstance(policy, dict) for policy in policies):
        raise ValueError("Knowledge base must be a JSON list of source objects.")
    return policies


def knowledge_snapshot(project, policies):
    return {
        "corpus_sha256": digest(policies),
        "applicability_sha256": digest(
            {
                "project_id": project["id"],
                "jurisdiction": project["jurisdiction"],
                "synthetic": project["synthetic"],
                "applicable_sources": [policy for policy in policies if policy_applicable(policy, project)],
            }
        ),
        "rule_version": "compliance-hybrid-v3",
        "evaluated_at": now(),
    }


def compliance_freshness_reason(project):
    snapshot = project.get("compliance_snapshot")
    if not snapshot:
        return "Compliance review has no knowledge-base snapshot. Rerun compliance and renew its approvals."
    try:
        current = knowledge_snapshot(project, load_policies())
    except (OSError, ValueError, TypeError):
        return (
            "Knowledge base is unavailable or invalid. Restore approved sources and rerun compliance review."
        )
    if any(
        snapshot.get(key) != current[key] for key in ("corpus_sha256", "applicability_sha256", "rule_version")
    ):
        return "Knowledge-base content or current applicability has changed. Rerun compliance and renew its approvals."
    return None


def policy_applicable(policy, project):
    """Fail closed unless a source has complete metadata and explicit applicability."""
    required_text = (
        "id",
        "title",
        "clause",
        "text",
        "jurisdiction",
        "version",
        "effective_date",
        "applicability",
        "control",
    )
    if any(not isinstance(policy.get(key), str) or not policy[key].strip() for key in required_text):
        return False
    if not isinstance(policy.get("synthetic"), bool):
        return False
    if (
        not isinstance(policy.get("keywords"), list)
        or not policy["keywords"]
        or any(not isinstance(k, str) or not k.strip() for k in policy["keywords"])
    ):
        return False
    if policy["synthetic"]:
        if not project["synthetic"]:
            return False
    else:
        # Merely importing a JSON file cannot establish an approved regulation.
        if not isinstance(policy.get("approved_by"), str) or not policy["approved_by"].strip():
            return False
        if (
            not isinstance(policy.get("applicable_project_ids"), list)
            or project["id"] not in policy["applicable_project_ids"]
        ):
            return False
        if policy["jurisdiction"].casefold() != project["jurisdiction"].casefold():
            return False
    try:
        if date.fromisoformat(policy["effective_date"]) > date.today():
            return False
        if policy.get("expires_on") and date.fromisoformat(policy["expires_on"]) < date.today():
            return False
    except (ValueError, TypeError):
        return False
    return True


def compliance(project, *, use_vectors=False):
    policies = load_policies()
    requirements = [r for r in project["requirements"] if r["status"] != "rejected"]
    eligible = [policy for policy in policies if policy_applicable(policy, project)]
    vector_search = bool(use_vectors and eligible and requirements)
    distances = retrieval.search(eligible, requirements) if vector_search else {}
    mappings = []
    for policy in eligible:
        matches = []
        for req in requirements:
            terms = [k for k in policy["keywords"] if k.casefold() in req["statement"].casefold()]
            distance = distances.get((policy["id"], req["id"]))
            if terms or distance is not None:
                matches.append(dict(requirement_id=req["id"], keywords=terms, cosine_distance=distance))
        source = {k: v for k, v in policy.items() if k not in ("keywords", "control")}
        interpretation = (
            "Advisory mapping to a synthetic policy, not a regulatory conclusion."
            if policy["synthetic"]
            else "Advisory mapping to an approved local source; its interpretation and adequacy require compliance officer review."
        )
        mappings.append(
            dict(
                id=uid("MAP"),
                requirement_ids=[m["requirement_id"] for m in matches],
                matches=matches,
                control=policy["control"],
                status="proposed",
                reason="Candidate requirements are listed with their retrieval evidence. An officer must assess coverage."
                if matches
                else "Source-backed control has no matching requirement; potential gap.",
                interpretation=interpretation,
                source=source,
                history=[],
            )
        )
    for control in [
        "Authentication",
        "Access control",
        "Auditability",
        "Data minimisation",
        "Sensitive data protection",
        "Applicable financial regulations",
    ]:
        if not any(m["control"] == control for m in mappings):
            mappings.append(
                dict(
                    id=uid("MAP"),
                    requirement_ids=[],
                    control=control,
                    status="unsupported",
                    reason=UNSUPPORTED,
                    interpretation="Obtain an approved, applicable source and a compliance officer assessment.",
                    source=None,
                    history=[],
                )
            )
    for r in requirements:
        if "compliance" in r["categories"] and not any(
            m["source"] and not m["source"]["synthetic"] and r["id"] in m["requirement_ids"] for m in mappings
        ):
            mappings.append(
                dict(
                    id=uid("MAP"),
                    requirement_ids=[r["id"]],
                    control="Regulatory applicability",
                    status="unsupported",
                    reason=UNSUPPORTED,
                    interpretation="No approved financial regulation has been supplied for this requirement.",
                    source=None,
                    history=[],
                )
            )
    project["mappings"] = mappings
    project["compliance_snapshot"] = knowledge_snapshot(project, policies)
    method = "Keyword matching"
    if vector_search:
        method = f"ChromaDB {retrieval.MODEL}, cosine distance <= {retrieval.MAX_DISTANCE:.2f}, plus keywords"
    elif use_vectors:
        method = "No eligible clause or requirement to query"
    project["compliance_snapshot"]["retrieval"] = method
    cited = [m["source"] for m in mappings if m["source"]]
    run(
        project,
        "ComplianceAgent",
        [r["id"] for r in requirements],
        f"{method}. Found {len(cited)} applicable source clauses ({sum(s['synthetic'] for s in cited)} synthetic). Mappings are advisory.",
        0.5,
        [s["id"] for s in cited],
        provider="local-chromadb+rules" if vector_search else "local-rules-v1",
    )
