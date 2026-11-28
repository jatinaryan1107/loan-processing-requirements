"""Extract, classify and prioritise draft requirements."""

import re
from .classification_agent import classify
from .risk_agent import rate
from ..storage import now, run, uid


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
    cats = item.get("categories", cats)
    return dict(
        id=uid("REQ"),
        source_id=source["id"],
        original_text=item.get("evidence", statement),
        statement=statement,
        kind=item.get("kind", kind),
        categories=cats,
        priority=item.get(
            "priority", "Must" if "shall" in statement.lower() or "must" in statement.lower() else "Should"
        ),
        acceptance_criteria=item.get("acceptance_criteria", acceptance(statement, cats)),
        justification="Stakeholder-provided requirement; business justification requires confirmation.",
        dependencies=[],
        assumptions=[
            "Acceptance criteria are draft templates; the analyst must confirm concrete preconditions and expected outcomes."
        ],
        risk=rate(cats),
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
