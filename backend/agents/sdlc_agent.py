"""Score lifecycle profiles and build their delivery workflows."""

from ..storage import run


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
