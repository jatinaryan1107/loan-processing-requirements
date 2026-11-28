"""Apply extraction results and run downstream requirement checks on a single project revision."""

from .. import storage
from . import extraction_agent, quality_agent, risk_agent


def analyse_pending(project, pending, model_results, use_llm):
    storage.run(
        project,
        "CoordinatorAgent",
        [s["id"] for s in pending],
        "Extract and classify drafts, triage risk, check quality and prepare follow-up questions.",
    )
    for source in project["sources"]:
        if source["extracted"] or source.get("excluded"):
            continue
        if use_llm:
            result, metadata = model_results[source["id"]]
            for item in result.requirements:
                project["requirements"].append(
                    extraction_agent.make_requirement(item.statement, source, item.model_dump())
                )
            source["extracted"] = True
            storage.run(
                project,
                "ExtractionAgent",
                [source["id"]],
                f"Validated {len(result.requirements)} model drafts and exact evidence quotes.",
                0.65,
                [source["id"]],
                metadata["provider"] + "/" + metadata.get("response_model", metadata["model"]),
            )
            project["runs"][-1]["prompt_record"] = metadata
            for question in result.questions:
                project["questions"].append(
                    dict(
                        id=storage.uid("Q"),
                        requirement_ids=[],
                        text=question,
                        status="open",
                        origin="llm",
                    )
                )
        else:
            extraction_agent.extract_source(project, source)
        if len(project["requirements"]) > 500:
            raise ValueError(
                "This MVP supports up to 500 requirements per project. Split larger scopes into separate projects.",
            )
    storage.run(
        project,
        "ClassificationAgent",
        [r["id"] for r in project["requirements"]],
        "Stored model-proposed types, categories and priorities for the new drafts."
        if use_llm
        else "Assigned draft types, categories and priorities using local rules.",
    )
    risk_agent.assess(project)
    quality_agent.quality(project)
