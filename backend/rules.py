"""Inspectable heuristic agents; scores are rule fit, never probabilities."""

import json
import hashlib
import re
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from .storage import now, run, uid

UNSUPPORTED = "No verified source available / requires compliance officer review."
CATEGORIES = {
    "security": [
        "authentication",
        "authenticate",
        "password",
        "encrypt",
        "access",
        "login",
        "security",
        "role",
    ],
    "privacy": ["personal", "sensitive", "privacy", "minimis", "minimiz", "retention", "retain", "delete"],
    "compliance": ["regulat", "rbi", "kyc", "law", "compliance", "jurisdiction"],
    "performance": ["latency", "response time", "quick", "fast", "concurrent", "throughput"],
    "availability": ["uptime", "available", "availability", "recover", "backup"],
    "auditability": ["audit", "logging", "timestamp"],
    "integration": ["api", "legacy", "integrat", "disburs", "gateway"],
    "usability": ["user-friendly", "accessible", "usability", "screen reader"],
    "operational": ["maintain", "monitor", "incident", "exception", "retry"],
}


TIME_TARGET = re.compile(
    r"\b(?:\d+(?:\.\d+)?|one|two|three|four|five|ten|per)\s*(?:milliseconds?|seconds?|ms)\b"
)
AUTH_ACTION = re.compile(r"\b(?:shall|must|should)\s+(?:authenticate\b|require\s+authentication\b)")


def classify(text):
    lower = text.lower()
    categories = [
        cat
        for cat, terms in CATEGORIES.items()
        if any(re.search(r"\b" + re.escape(term), lower) for term in terms)
    ]
    if TIME_TARGET.search(lower) and "performance" not in categories:
        categories.append("performance")
    quality_attributes = {"performance", "availability", "usability", "privacy", "security"}
    if AUTH_ACTION.search(lower):
        quality_attributes.remove("security")
    kind = "non-functional" if quality_attributes.intersection(categories) else "functional"
    return kind, categories or ["business"]


def acceptance(text, categories):
    if "performance" in categories and re.search(r"\d", text):
        return [
            f"Given the agreed workload and test environment, when this behavior is measured, verify the stated numeric threshold: {text}",
            "Record the measured result, workload, and pass/fail outcome; confirm missing percentile and concurrency assumptions with the analyst.",
        ]
    if "security" in categories:
        return [
            f"Given an authorised test user and synthetic records, verify: {text}",
            "Repeat with an unauthorised user and verify access is denied without exposing restricted data.",
        ]
    return [
        f"Given the agreed preconditions and synthetic test data, execute and verify: {text}",
        "Verify invalid or missing input produces the agreed error outcome without changing existing records.",
    ]


def make_requirement(statement, source, item=None):
    kind, cats = classify(statement)
    item = item or {}
    return dict(
        id=uid("REQ"),
        source_id=source["id"],
        original_text=item.get("evidence", statement),
        statement=statement,
        kind=item.get("kind", kind),
        categories=item.get("categories", cats),
        priority=item.get(
            "priority", "Must" if "shall" in statement.lower() or "must" in statement.lower() else "Should"
        ),
        acceptance_criteria=item.get("acceptance_criteria", acceptance(statement, cats)),
        justification="Stakeholder-provided requirement; business justification requires confirmation.",
        dependencies=[],
        assumptions=[
            "Acceptance criteria are draft templates; the analyst must confirm concrete preconditions and expected outcomes."
        ],
        risk="high" if set(cats) & {"security", "privacy", "compliance"} else "medium",
        confidence=0.55 if not item else 0.65,
        status="draft",
        history=[],
        created_at=now(),
        updated_at=now(),
    )


def extract_source(project, source):
    # Sentence boundaries avoid splitting decimals. No embedded instruction is executed.
    sentences = re.split(r"\n+|(?<=[.!?])\s+(?=[A-Z])", source["text"])
    statements = [s.strip(" \t-*•") for s in sentences]
    statements = [s for s in statements if len(s) >= 12]
    if not statements:
        raise ValueError(
            "No candidate requirement statement of at least 12 characters was found. Supply a complete requirement statement."
        )
    if len(statements) > 150:
        raise ValueError(
            "This source contains more than 150 candidate statements. Split it into smaller documents; no partial extraction was saved."
        )
    if len(project["requirements"]) + len(statements) > 500:
        raise ValueError(
            "This demo supports at most 500 requirements per project. Create a separate scoped project."
        )
    for text in statements:
        project["requirements"].append(make_requirement(text, source))
    source["extracted"] = True
    run(
        project,
        "ExtractionAgent",
        [source["id"]],
        f"Extracted {len(statements)} sentence-based draft requirements. Human validation required.",
        0.55,
        [source["id"]],
    )


def quality(project):
    flags = []
    requirements = [r for r in project["requirements"] if r["status"] != "rejected"]

    def flag(ids, kind, message, question, severity="warning"):
        flags.append(
            dict(
                id=uid("FLAG"),
                requirement_ids=ids,
                type=kind,
                severity=severity,
                message=message,
                question=question,
            )
        )

    for req in requirements:
        text = req["statement"]
        vague = re.findall(
            r"\b(?:quickly|fast|easy|user-friendly|appropriate|secure|efficient|as needed|etc|adequate|soon)\b",
            text,
            re.I,
        )
        if vague:
            flag(
                [req["id"]],
                "ambiguity",
                f"Unmeasured wording: {', '.join(vague)}.",
                f"For {req['id']}, what measurable threshold or observable behavior replaces '{vague[0]}'?",
            )
        if len(text.split()) < 6 or "TBD" in text:
            flag(
                [req["id"]],
                "incomplete",
                "Actor, trigger or outcome may be missing.",
                f"For {req['id']}, specify who acts, what triggers the behavior and its observable result.",
            )
        if re.search(
            r"ignore (?:all |previous |prior )*instructions|system prompt|reveal.*secret|act as", text, re.I
        ):
            flag(
                [req["id"]],
                "untrusted_instruction",
                "Possible instruction embedded in source data. Never treated as an agent command.",
                "Is this sentence a software requirement? Reject any embedded instruction.",
                "high",
            )
        if "performance" in req["categories"] and not re.search(r"\d", text):
            flag(
                [req["id"]],
                "testability",
                "Performance requirement lacks a numeric target.",
                f"What latency, percentile and concurrent load should {req['id']} meet?",
            )
    for i, a in enumerate(requirements):
        for b in requirements[i + 1 :]:
            at, bt = a["statement"].lower(), b["statement"].lower()

            def norm(s):
                return re.sub(r"\W+", " ", s).strip()

            if norm(at) == norm(bt):
                flag(
                    [a["id"], b["id"]],
                    "duplicate",
                    "Statements are textually equivalent.",
                    "Which requirement should remain the canonical record?",
                )
                continue

            def stripped(s):
                return re.sub(r"\b(?:not|never|no)\b|\d+(?:\.\d+)?", "", norm(s))

            similar = SequenceMatcher(None, stripped(at), stripped(bt)).ratio() > 0.77
            numbers_a, numbers_b = re.findall(r"\d+(?:\.\d+)?", at), re.findall(r"\d+(?:\.\d+)?", bt)
            negative_a, negative_b = (
                bool(re.search(r"\b(?:not|never|no)\b", at)),
                bool(re.search(r"\b(?:not|never|no)\b", bt)),
            )
            if similar and ((numbers_a and numbers_b and numbers_a != numbers_b) or negative_a != negative_b):
                flag(
                    [a["id"], b["id"]],
                    "conflict",
                    "Similar statements specify incompatible values or opposite obligations; verify context.",
                    f"Which condition or value is intended for {a['id']} and {b['id']}? Edit or reject the conflicting statement.",
                    "high",
                )
    combined = " ".join(r["statement"].lower() for r in requirements)
    domains = {
        "application intake": ["application", "intake"],
        "identity verification": ["identity", "kyc"],
        "eligibility rules": ["eligibility"],
        "approval workflow": ["approval", "approve"],
        "disbursal integration": ["disburs"],
        "repayment status": ["repayment"],
        "error handling": ["error", "retry", "exception"],
        "data minimisation": ["minimis", "minimiz"],
        "availability": ["uptime", "availability", "recover"],
    }
    for domain, terms in domains.items():
        if not any(t in combined for t in terms):
            flag(
                [],
                "omission",
                f"No explicit requirement found for {domain}.",
                f"Is {domain} in scope? Specify the required behavior or explain its exclusion.",
            )

    def question_key(question):
        return question["text"], tuple(sorted(question["requirement_ids"]))

    old = {question_key(q): q for q in project["questions"]}
    questions = []
    for f in flags:
        candidate = dict(id=uid("Q"), requirement_ids=f["requirement_ids"], text=f["question"], status="open")
        relevant = [r for r in requirements if not f["requirement_ids"] or r["id"] in f["requirement_ids"]]
        context = digest(
            [
                {key: r[key] for key in ("id", "statement", "categories", "acceptance_criteria")}
                for r in relevant
            ]
        )
        previous = old.get(question_key(candidate))
        if previous and (previous.get("context_sha256") == context or previous["status"] == "open"):
            candidate = previous
        elif previous and previous["status"] == "answered":
            # Keep the historical answer separately; it cannot resolve changed evidence.
            candidate["supersedes_question_id"] = previous["id"]
        candidate["context_sha256"] = context
        questions.append(candidate)
    # Keep prior answers as the permanent interview record even after a flag disappears.
    questions += [
        q
        for q in project["questions"]
        if (q["status"] == "answered" or q.get("origin") == "llm")
        and q["id"] not in {x["id"] for x in questions}
    ]
    project["flags"], project["questions"] = flags, questions
    run(
        project,
        "QualityConflictAgent",
        [r["id"] for r in requirements],
        f"Applied ambiguity, duplicate, numeric/negation conflict, testability and scope omission heuristics; {len(flags)} flags.",
        0.65,
    )
    run(
        project,
        "ClarificationAgent",
        [f["id"] for f in flags],
        f"Prepared {sum(q['status'] == 'open' for q in questions)} context-linked follow-up questions.",
        0.65,
    )


def load_policies():
    policies = json.loads((Path(__file__).parent / "knowledge" / "policies.json").read_text(encoding="utf-8"))
    if not isinstance(policies, list) or any(not isinstance(policy, dict) for policy in policies):
        raise ValueError("Knowledge base must be a JSON list of source objects.")
    return policies


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


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
        "rule_version": "compliance-keyword-v2",
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


def compliance(project):
    policies = load_policies()
    requirements = [r for r in project["requirements"] if r["status"] != "rejected"]
    mappings = []
    for policy in policies:
        if not policy_applicable(policy, project):
            continue
        matched = [
            r["id"]
            for r in requirements
            if any(k.casefold() in r["statement"].casefold() for k in policy["keywords"])
        ]
        source = {k: v for k, v in policy.items() if k not in ("keywords", "control")}
        interpretation = (
            "Advisory mapping to a synthetic policy, not a regulatory conclusion."
            if policy["synthetic"]
            else "Advisory mapping to an approved local source; its interpretation and adequacy require compliance officer review."
        )
        mappings.append(
            dict(
                id=uid("MAP"),
                requirement_ids=matched,
                control=policy["control"],
                status="proposed",
                reason="Keyword evidence suggests a possible control mapping; semantic adequacy requires officer review."
                if matched
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
    cited = [m["source"] for m in mappings if m["source"]]
    run(
        project,
        "ComplianceAgent",
        [r["id"] for r in requirements],
        f"Retrieved {len(cited)} applicable source clauses ({sum(s['synthetic'] for s in cited)} synthetic); mappings are advisory and confidence is an uncalibrated heuristic.",
        0.5,
        [s["id"] for s in cited],
    )


FACTORS = [
    "stability",
    "complexity",
    "regulatory",
    "security",
    "stakeholders",
    "change",
    "legacy",
    "testing",
    "cadence",
]
# Each model has a target profile. Each equally weighted factor contributes 0..4.
PROFILES = {
    "Agile": [1, 3, 2, 3, 5, 5, 2, 3, 5],
    "Waterfall": [5, 3, 4, 3, 2, 1, 4, 4, 1],
    "V-Model": [5, 4, 5, 4, 3, 2, 4, 5, 2],
    "Spiral": [1, 5, 4, 5, 4, 4, 5, 4, 3],
    "DevSecOps": [2, 4, 4, 5, 4, 5, 3, 5, 5],
    "Agile / V-Model hybrid": [2, 4, 5, 4, 5, 5, 4, 5, 4],
}


def workflow(project, model):
    iterative = model in ("Agile", "DevSecOps", "Spiral", "Agile / V-Model hybrid")
    phases = [
        "Discover and baseline",
        "Risk and architecture",
        "Iterative implementation" if iterative else "Implementation",
        "Verification and validation",
        "Release readiness",
        "Operate and reassess",
    ]
    activities = [
        [f"Confirm scope for {project['name']}", "Resolve open requirements and preserve source links"],
        ["Model access boundaries and data flows", "Review legacy dependencies and failure scenarios"],
        ["Implement approved requirement IDs", "Record changes, peer review and automated checks"],
        [
            "Execute acceptance criteria and negative security tests",
            "Link each test outcome to its requirement ID",
        ],
        [
            "Review evidence, outstanding risks and compliance dispositions",
            "Prepare rollback and support procedures",
        ],
        ["Monitor incidents and requirement changes", "Reassess source versions and lifecycle assumptions"],
    ]
    if model == "Spiral":
        activities[1].append("Prototype the highest uncertainty risk before each cycle")
    if model in ("V-Model", "Agile / V-Model hybrid"):
        activities[0].append("Pair every specification level with a planned verification activity")
    if model == "DevSecOps":
        activities[2].append("Gate the delivery pipeline on secret, dependency and static security scans")
    factors = project.get("sdlc", {}).get("factors", {}) if project.get("sdlc") else {}
    if factors.get("legacy", 0) >= 4:
        activities[1].append("Map legacy data contracts, migration dependencies and rollback ownership")
        activities[3].append("Run integration contract tests against legacy-system simulators")
    if factors.get("security", 0) >= 4:
        activities[1].append(
            "Review high-risk threats, abuse cases and sensitive-data boundaries with the Compliance Officer"
        )
    if factors.get("testing", 0) >= 4:
        activities[3].append("Maintain formal test-to-requirement evidence for each verification gate")
    if factors.get("cadence", 0) >= 4:
        activities[2].append("Deliver small increments through repeatable gated release cycles")
    if factors.get("regulatory", 0) >= 4:
        activities[4].append(
            "Escalate missing approved regulatory sources; no deployment readiness is implied by this advisory plan"
        )
    roles = [
        ["Business Analyst", "Project Manager"],
        ["Software Developer", "Compliance Officer"],
        ["Software Developer"],
        ["Software Developer", "Business Analyst"],
        ["Project Manager", "Compliance Officer"],
        ["Project Manager", "Software Developer"],
    ]
    deliverables = [
        ["Approved SRS", "Traceability matrix"],
        ["Architecture decisions", "Threat and risk register"],
        ["Reviewed code", "Test evidence"],
        ["Acceptance report", "Control evidence"],
        ["Release checklist", "Rollback plan"],
        ["Change register", "Updated requirements baseline"],
    ]
    checkpoints = [
        "Classify and minimise input data",
        "Approve threat mitigations and access design",
        "Security scanning and peer review",
        "Authentication, authorisation and abuse-case tests",
        "Compliance officer and security review before deployment",
        "Monitor vulnerabilities and policy changes",
    ]
    return [
        dict(
            phase=phase,
            activities=activities[i],
            roles=roles[i],
            deliverables=deliverables[i],
            security_checkpoint=checkpoints[i],
            approval_gate="Human sign-off by " + ", ".join(roles[i]),
            entry="Previous gate complete; linked inputs available"
            if i
            else "Project scope and stakeholder input recorded",
            exit="Deliverables reviewed, evidence linked and unresolved risks explicitly accepted",
        )
        for i, phase in enumerate(phases)
    ]


def recommend(project, factors):
    rankings = []
    for model, targets in PROFILES.items():
        if "hybrid" in model and not (factors["regulatory"] >= 4 and factors["change"] >= 4):
            continue
        contributions = [4 - abs(factors[f] - target) for f, target in zip(FACTORS, targets)]
        rankings.append(
            dict(
                model=model,
                score=sum(contributions),
                max_score=36,
                rationale=[
                    f"{factor}: entered {factors[factor]}/5; model target {target}/5; contributes {part}/4."
                    for factor, target, part in zip(FACTORS, targets, contributions)
                ],
            )
        )
    rankings.sort(key=lambda r: (-r["score"], r["model"]))
    top = rankings[0]["model"]
    project["sdlc"] = dict(
        factors=factors,
        rankings=rankings,
        uncertainty="Heuristic target-profile fit, not an empirical success probability. Equal weights and self-reported factors require human validation. Close scores indicate no strong preference.",
        selected_model=top,
        status="draft",
        workflow=[],
        history=[],
    )
    project["sdlc"]["workflow"] = workflow(project, top)
    run(
        project,
        "SDLCSelectionAgent",
        [r["id"] for r in project["requirements"]],
        f"Ranked {len(rankings)} approaches with target-profile-v1. Top: {top} ({rankings[0]['score']}/36).",
        0.65,
        ["target-profile-v1"],
    )


def blockers(project):
    reasons = []
    reqs = project["requirements"]
    if not any(r["status"] == "approved" for r in reqs):
        reasons.append("At least one requirement must be approved.")
    if any(r["status"] == "draft" for r in reqs):
        reasons.append("All requirements need an approval or rejection decision.")
    if any(not s["extracted"] and not s.get("excluded", False) for s in project["sources"]):
        reasons.append("Analyse all pending sources.")
    active = {r["id"] for r in reqs if r["status"] != "rejected"}
    if any(
        f["type"] in ("conflict", "untrusted_instruction") and all(i in active for i in f["requirement_ids"])
        for f in project["flags"]
    ):
        reasons.append("Resolve conflicting requirements and embedded instructions before final export.")
    if not project["mappings"] or any(
        m["status"] not in ("approved", "rejected") for m in project["mappings"]
    ):
        reasons.append(
            "A compliance officer must disposition all mappings; unsupported sources require documented rejection."
        )
    if project["mappings"]:
        stale_reason = compliance_freshness_reason(project)
        if stale_reason:
            reasons.append(stale_reason)
    if not project["sdlc"] or project["sdlc"]["status"] != "approved":
        reasons.append("A project manager must approve the lifecycle selection.")
    return reasons
