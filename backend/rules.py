"""Review gates and public entry points for the analysis rules."""

from .agents.compliance_agent import (
    UNSUPPORTED as UNSUPPORTED,
    load_policies as load_policies,
    policy_applicable as policy_applicable,
    knowledge_snapshot as knowledge_snapshot,
    compliance_freshness_reason as compliance_freshness_reason,
    compliance as compliance,
)
from .agents.classification_agent import CATEGORIES as CATEGORIES, classify as classify
from .agents.extraction_agent import (
    acceptance as acceptance,
    make_requirement as make_requirement,
    extract_source as extract_source,
)
from .agents.quality_agent import (
    quality as quality,
)
from .agents.sdlc_agent import (
    FACTORS as FACTORS,
    PROFILES as PROFILES,
    recommend as recommend,
    workflow as workflow,
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
