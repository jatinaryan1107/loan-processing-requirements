"""Shared project operations and role-safe response views."""

import copy
import json
from contextlib import contextmanager
from fastapi import HTTPException
from . import rules, storage


def check_version(project):
    expected = storage.expected_version.get()
    if expected and expected.strip('"') != project["updated_at"]:
        raise HTTPException(
            409,
            "This project changed in another session. The latest version must be reviewed before retrying.",
        )


@contextmanager
def edit_project(project_id):
    """Compute on a snapshot, then commit only if no other request changed it.

    Rule checks and generation run without holding SQLite's global writer lock.
    The final comparison and write share one short atomic transaction.
    """
    with storage.connect() as conn:
        project = load(conn, project_id)
    check_version(project)
    version = project["updated_at"]
    yield project
    with storage.transaction() as conn:
        latest = load(conn, project_id)
        if latest["updated_at"] != version:
            raise HTTPException(
                409, "This project changed while the operation was running. Refresh and retry."
            )
        storage.save_project(conn, project)


def load(conn, project_id):
    project = storage.get_project(conn, project_id)
    if project is None:
        raise HTTPException(404, "Project not found.")
    return project


def find(items, identifier):
    item = next((i for i in items if i["id"] == identifier), None)
    if item is None:
        raise HTTPException(404, "Record not found in this project.")
    return item


def projection(project, current):
    result = copy.deepcopy(project)
    result["final_blockers"] = rules.blockers(project)
    result["final_ready"] = not result["final_blockers"]
    if current["role"] == "developer":
        result["requirements"] = [r for r in result["requirements"] if r["status"] == "approved"]
        for requirement in result["requirements"]:
            approvals = [h for h in requirement["history"] if h.get("decision") == "approved"]
            requirement["history"] = approvals[-1:]
        ids = {r["id"] for r in result["requirements"]}
        # Do not leak drafts through raw source documents, audit histories or agent prompts.
        result["sources"], result["audit"], result["runs"], result["questions"] = [], [], [], []
        result["flags"] = [
            f for f in result["flags"] if f["requirement_ids"] and all(i in ids for i in f["requirement_ids"])
        ]
        result["mappings"] = [
            m
            for m in result["mappings"]
            if m["status"] == "approved" and all(i in ids for i in m["requirement_ids"])
        ]
        if result["sdlc"] and result["sdlc"]["status"] != "approved":
            result["sdlc"] = None
    return result


def invalidate(project, current, why):
    if project["mappings"] or project["sdlc"]:
        storage.audit(
            project,
            current,
            "derived_reviews_invalidated",
            json.dumps(
                {
                    "reason": why,
                    "previous_mappings": project["mappings"],
                    "previous_sdlc": project["sdlc"],
                    "compliance_snapshot": project.get("compliance_snapshot"),
                }
            ),
        )
    project["mappings"] = []
    project.pop("compliance_snapshot", None)
    if project["sdlc"]:
        project["sdlc"]["status"] = "draft"


def add_source(project, text, source_name, stakeholder, synthetic=False):
    if (
        len(project["sources"]) >= 100
        or sum(len(s["text"]) for s in project["sources"]) + len(text) > 1000000
    ):
        raise HTTPException(
            422,
            "This MVP supports up to 100 sources and 1,000,000 source characters per project. Split larger work into projects.",
        )
    source = dict(
        id=storage.uid("SRC"),
        source_name=source_name,
        stakeholder=stakeholder,
        text=text,
        created_at=storage.now(),
        extracted=False,
        synthetic=synthetic,
    )
    project["sources"].append(source)
    return source
