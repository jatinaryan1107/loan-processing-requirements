"""Triage requirement review risk from its recorded categories."""

from ..storage import run

HIGH_RISK_CATEGORIES = {"security", "privacy", "compliance"}


def rate(categories):
    return "high" if HIGH_RISK_CATEGORIES.intersection(categories) else "medium"


def assess(project):
    active = [r for r in project["requirements"] if r["status"] != "rejected"]
    for req in active:
        if req["status"] == "draft":
            req["risk"] = rate(req["categories"])
    high = sum(r["risk"] == "high" for r in active)
    run(
        project,
        "RiskAgent",
        [r["id"] for r in active],
        f"{high} of {len(active)} active requirements need high-priority risk review. Security, privacy or compliance categories trigger high risk; other categories receive medium.",
    )
