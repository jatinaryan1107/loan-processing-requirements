"""Find review issues and generate evidence-linked follow-up questions."""

import re
from difflib import SequenceMatcher
from ..storage import run, uid
from . import clarification_agent


INSTANT_APPROVAL = re.compile(
    r"\b(?:instant(?:aneous)?|immediate|automatic) approvals?\b|"
    r"\bapprovals? (?:shall|should|must|will) be (?:instant(?:aneous)?|immediate|automatic)\b",
    re.I,
)
OFFICER_REVIEW = re.compile(
    r"\b(?:credit |loan )?officers? (?:shall|should|must|will) (?:check|review) (?:each|every|all)\b",
    re.I,
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
        if (
            INSTANT_APPROVAL.search(text)
            and OFFICER_REVIEW.search(text)
            and not re.search(r"\b(?:after|following|once|upon|until|provisional|preliminary)\b", text, re.I)
        ):
            flag(
                [req["id"]],
                "workflow_ambiguity",
                "Immediate approval and officer review are both requested, but their order is unclear.",
                "Is the instant result provisional or final, and when must the credit officer review the application?",
            )
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

    project["flags"] = flags
    run(
        project,
        "QualityConflictAgent",
        [r["id"] for r in requirements],
        f"Checked vague wording, approval order, duplicates, numeric/negation conflicts, testability and scope omissions; {len(flags)} flags.",
        0.65,
    )
    clarification_agent.prepare(project, requirements, flags)
