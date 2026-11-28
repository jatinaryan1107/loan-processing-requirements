"""HTTP adapters for project capture, analysis, review and export."""

import hashlib
import json
import os
import secrets
import time
from typing import Literal
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from . import llm, retrieval, rules, storage
from .agents import (
    classification_agent,
    compliance_agent,
    coordinator_agent,
    documentation_agent,
    extraction_agent,
    quality_agent,
    risk_agent,
    sdlc_agent,
)
from .auth import ROLES, allowed, user
from .ingestion import parse_document
from .schemas import (
    Login,
    ProjectInput,
    SourceInput,
    AnalyseInput,
    RequirementEdit,
    Review,
    MappingReview,
    Answer,
    SdlcInput,
    SdlcDecision,
)
from .services import load, find, projection, invalidate, add_source, edit_project, check_version
from .schemas import ExcludeSource

router = APIRouter()


@router.get("/api/health")
def health():
    return dict(status="ok", mode="deterministic demo", llm_available=llm.enabled(), version="1.0.0")


@router.post("/api/session")
def session(body: Login):
    if os.getenv("ENABLE_DEMO_LOGIN", "true").lower() != "true":
        raise HTTPException(
            403, "Demo login disabled. This MVP does not provide a production identity adapter."
        )
    token = secrets.token_urlsafe(32)
    with storage.connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires <= ?", (time.time(),))
        conn.execute(
            "INSERT INTO sessions VALUES (?,?,?)",
            (hashlib.sha256(token.encode()).hexdigest(), body.role, time.time() + 8 * 3600),
        )
    return dict(
        token=token,
        user=dict(id="demo-" + body.role, name=ROLES[body.role], role=body.role),
        mode="Local demo login â€” identity is selected, not verified",
    )


@router.get("/api/projects")
def projects(current=Depends(user)):
    with storage.connect() as conn:
        items = [json.loads(row[0]) for row in conn.execute("SELECT document FROM projects")]
    return [
        {
            **{k: p[k] for k in ("id", "name", "description", "jurisdiction", "synthetic", "created_at")},
            "requirement_count": len(p["requirements"])
            if current["role"] != "developer"
            else sum(r["status"] == "approved" for r in p["requirements"]),
            "approved_count": sum(r["status"] == "approved" for r in p["requirements"]),
        }
        for p in items
    ]


@router.delete("/api/session")
def logout(current=Depends(user)):
    with storage.connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash=?", (current["token_hash"],))
    return {"ok": True}


@router.post("/api/projects")
def create_project(body: ProjectInput, current=Depends(allowed("ba"))):
    project = storage.new_project(body.name, body.description, body.jurisdiction)
    storage.audit(project, current, "project_created", project["name"])
    with storage.transaction() as conn:
        storage.save_project(conn, project)
    return projection(project, current)


@router.get("/api/projects/{project_id}")
def project_detail(project_id: str, current=Depends(user)):
    with storage.connect() as conn:
        return projection(load(conn, project_id), current)


@router.put("/api/projects/{project_id}/context")
def update_project(project_id: str, body: ProjectInput, current=Depends(allowed("ba"))):
    with edit_project(project_id) as project:
        changes = {key: value for key, value in body.model_dump().items() if project[key] != value}
        if changes:
            previous = {key: project[key] for key in changes}
            if changes.keys() & {"description", "jurisdiction"}:
                invalidate(project, current, "Project context or jurisdiction changed")
            project.update(changes)
            storage.audit(
                project, current, "project_edited", json.dumps({"before": previous, "after": changes})
            )
    return projection(project, current)


@router.post("/api/projects/{project_id}/sources")
def source_input(project_id: str, body: SourceInput, current=Depends(allowed("ba"))):
    with edit_project(project_id) as project:
        invalidate(project, current, "New stakeholder input")
        source = add_source(project, body.text, body.source_name, body.stakeholder)
        storage.audit(project, current, "source_added", source["id"])
    return projection(project, current)


@router.post("/api/projects/{project_id}/upload")
def upload(project_id: str, file: UploadFile = File(...), current=Depends(allowed("ba"))):
    data = file.file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "File exceeds the 5 MB limit.")
    text, name = parse_document(data, file.filename)
    with edit_project(project_id) as project:
        invalidate(project, current, "New uploaded source")
        source = add_source(project, text.strip(), name, current["name"])
        storage.audit(project, current, "document_uploaded", source["id"] + ": " + name)
    return projection(project, current)


@router.post("/api/projects/{project_id}/sources/{source_id}/exclude")
def exclude_source(project_id: str, source_id: str, body: ExcludeSource, current=Depends(allowed("ba"))):
    with edit_project(project_id) as project:
        source = find(project["sources"], source_id)
        if source["extracted"]:
            raise HTTPException(
                409, "This source has already been analysed. Review or reject its requirements individually."
            )
        source.update(excluded=True, exclusion_note=body.note, excluded_at=storage.now())
        invalidate(project, current, "Pending source excluded: " + source_id)
        storage.audit(project, current, "source_excluded", source_id + ": " + body.note)
    return projection(project, current)


@router.post("/api/projects/{project_id}/analyse")
def analyse(project_id: str, body: AnalyseInput, current=Depends(allowed("ba"))):
    # Preflight external calls outside the write lock; concurrent source changes are checked below.
    with storage.connect() as conn:
        before = load(conn, project_id)
    check_version(before)
    pending = [s for s in before["sources"] if not s["extracted"] and not s.get("excluded")]
    model_results = {}
    if body.use_llm:
        if not llm.enabled():
            raise HTTPException(400, "LLM mode needs a configured key, model and both explicit opt-in flags.")
        if not pending:
            raise HTTPException(422, "Add an unanalysed source to run model extraction.")
        try:
            for source in pending:
                model_results[source["id"]] = llm.extract(source["text"])
        except ValueError as exc:
            with storage.transaction() as conn:
                project = load(conn, project_id)
                storage.audit(project, current, "analysis_failed", str(exc))
                storage.run(
                    project,
                    "ExtractionAgent",
                    [s["id"] for s in pending],
                    str(exc),
                    0,
                    provider="configured-llm",
                )
                storage.save_project(conn, project)
            raise HTTPException(502, str(exc)) from exc
    with edit_project(project_id) as project:
        if project["updated_at"] != before["updated_at"]:
            raise HTTPException(409, "Project changed during analysis; refresh and retry.")
        invalidate(project, current, "Analysis rerun")
        try:
            coordinator_agent.analyse_pending(project, pending, model_results, body.use_llm)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        storage.audit(
            project,
            current,
            "analysis_completed",
            f"{'LLM' if body.use_llm else 'Deterministic'} extraction; {len(project['flags'])} quality flags.",
        )
    return projection(project, current)


@router.patch("/api/projects/{project_id}/requirements/{requirement_id}")
def edit_requirement(
    project_id: str, requirement_id: str, body: RequirementEdit, current=Depends(allowed("ba"))
):
    changes = body.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(422, "Supply at least one editable field.")
    with edit_project(project_id) as project:
        req = find(project["requirements"], requirement_id)
        req["history"].append(
            dict(
                at=storage.now(),
                actor=current["name"],
                decision="edited",
                note="Changed: " + ", ".join(changes),
                previous={k: v for k, v in req.items() if k != "history"},
            )
        )
        req.update(changes)
        if "statement" in changes:
            req["kind"], req["categories"] = classification_agent.classify(req["statement"])
            req["risk"] = risk_agent.rate(req["categories"])
            if "acceptance_criteria" not in changes:
                req["acceptance_criteria"] = extraction_agent.acceptance(req["statement"], req["categories"])
        req["status"], req["updated_at"] = "draft", storage.now()
        invalidate(project, current, "Requirement changed: " + requirement_id)
        quality_agent.quality(project)
        storage.audit(project, current, "requirement_edited", requirement_id)
    return projection(project, current)


@router.post("/api/projects/{project_id}/requirements/{requirement_id}/review")
def review_requirement(project_id: str, requirement_id: str, body: Review, current=Depends(allowed("ba"))):
    with edit_project(project_id) as project:
        req = find(project["requirements"], requirement_id)
        req["status"] = body.decision
        req["history"].append(dict(at=storage.now(), actor=current["name"], **body.model_dump()))
        req["updated_at"] = storage.now()
        invalidate(project, current, "Requirement review: " + requirement_id)
        quality_agent.quality(project)
        storage.audit(project, current, "requirement_" + body.decision, requirement_id + ": " + body.note)
    return projection(project, current)


@router.post("/api/projects/{project_id}/questions/{question_id}/answer")
def answer(project_id: str, question_id: str, body: Answer, current=Depends(allowed("ba"))):
    with edit_project(project_id) as project:
        q = find(project["questions"], question_id)
        source = add_source(project, body.answer, "Clarification: " + question_id, current["name"])
        if len(body.answer) < 12:
            source["extracted"] = True
            storage.run(
                project,
                "ClarificationAgent",
                [source["id"]],
                "Recorded a short clarification answer as context, without inventing a requirement.",
            )
        q.update(status="answered", answer=body.answer, source_id=source["id"])
        invalidate(project, current, "New clarification answer")
        storage.audit(project, current, "clarification_answered", question_id + " â†’ " + source["id"])
    return projection(project, current)


@router.post("/api/projects/{project_id}/compliance")
def check_compliance(project_id: str, current=Depends(allowed("ba", "compliance"))):
    with edit_project(project_id) as project:
        if project["mappings"]:
            storage.audit(project, current, "compliance_previous_snapshot", json.dumps(project["mappings"]))
        try:
            compliance_agent.compliance(project, use_vectors=True)
        except retrieval.SearchUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc
        if project["sdlc"]:
            project["sdlc"]["status"] = "draft"
        storage.audit(
            project,
            current,
            "compliance_checked",
            "Local versioned source retrieval; all mappings require officer disposition.",
        )
    return projection(project, current)


@router.post("/api/projects/{project_id}/mappings/{mapping_id}/review")
def review_mapping(
    project_id: str, mapping_id: str, body: MappingReview, current=Depends(allowed("compliance"))
):
    with edit_project(project_id) as project:
        mapping = find(project["mappings"], mapping_id)
        stale = compliance_agent.compliance_freshness_reason(project)
        if stale:
            raise HTTPException(409, stale)
        if body.decision == "approved" and not mapping["source"]:
            raise HTTPException(
                409,
                compliance_agent.UNSUPPORTED
                + " Reject with a review note; do not mark unsupported content as verified.",
            )
        if body.decision == "approved" and not mapping["requirement_ids"]:
            raise HTTPException(
                409,
                "No requirement supports this control. Add a requirement or reject the proposed mapping with a review note.",
            )
        mapping["status"] = body.decision
        if body.interpretation:
            mapping["interpretation"] = body.interpretation
        mapping["history"].append(dict(at=storage.now(), actor=current["name"], **body.model_dump()))
        if project["sdlc"]:
            project["sdlc"]["status"] = "draft"
        storage.audit(project, current, "mapping_" + body.decision, mapping_id + ": " + body.note)
    return projection(project, current)


@router.post("/api/projects/{project_id}/sdlc")
def sdlc(project_id: str, body: SdlcInput, current=Depends(allowed("pm"))):
    with edit_project(project_id) as project:
        if project["sdlc"]:
            storage.audit(project, current, "sdlc_previous_snapshot", json.dumps(project["sdlc"]))
        sdlc_agent.recommend(project, body.factors.model_dump())
        storage.audit(
            project,
            current,
            "sdlc_ranked",
            "Applied nine-factor target-profile-v1, equal weights; score out of 36.",
        )
    return projection(project, current)


@router.post("/api/projects/{project_id}/sdlc/decision")
def decide_sdlc(project_id: str, body: SdlcDecision, current=Depends(allowed("pm"))):
    with edit_project(project_id) as project:
        sdlc_result = project["sdlc"]
        if not sdlc_result or body.model not in [r["model"] for r in sdlc_result["rankings"]]:
            raise HTTPException(409, "Rank lifecycle options first and select one of the ranked models.")
        sdlc_result["selected_model"], sdlc_result["status"] = body.model, body.decision
        sdlc_result["workflow"] = sdlc_agent.workflow(project, body.model)
        sdlc_result["history"].append(dict(at=storage.now(), actor=current["name"], **body.model_dump()))
        storage.audit(project, current, "sdlc_" + body.decision, body.model + ": " + body.note)
    return projection(project, current)


@router.get("/api/projects/{project_id}/export")
def export(
    project_id: str,
    format: Literal["markdown", "json"] = "markdown",
    final: bool = False,
    current=Depends(user),
):
    with edit_project(project_id) as project:
        if final:
            if current["role"] != "pm":
                raise HTTPException(403, "Only the Project Manager may export an approved baseline.")
            if rules.blockers(project):
                raise HTTPException(409, "Final export blocked: " + " ".join(rules.blockers(project)))
        storage.run(
            project,
            "DocumentationAgent",
            [r["id"] for r in project["requirements"]],
            f"Generated {'approved baseline' if final else 'draft'} {format} export.",
        )
        storage.audit(project, current, "export_generated", f"format={format}, final={final}")
    result = projection(project, current)
    result["export_metadata"] = {
        "status": "approved baseline" if final else "draft",
        "generated_at": storage.now(),
        "generated_by": current["name"],
        "compliance_is_advisory": True,
    }
    if format == "json":
        return documentation_agent.payload(result, final)
    return PlainTextResponse(
        documentation_agent.markdown(result, final),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{project_id}-srs.md"'},
    )
