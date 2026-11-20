"""Regression checks for evidence freshness, question revisions and baseline boundaries."""

import copy
from datetime import date

import pytest

from backend import exports, rules, storage


@pytest.fixture
def project():
    result = storage.new_project("Reviewed project", "Synthetic test case", "India", synthetic=True)
    source = {
        "id": "SRC-1",
        "text": "The system shall authenticate staff before opening records.",
        "extracted": False,
        "source_name": "Test interview",
        "stakeholder": "Test analyst",
        "created_at": storage.now(),
    }
    result["sources"].append(source)
    rules.extract_source(result, source)
    result["requirements"][0]["status"] = "approved"
    rules.compliance(result)
    for mapping in result["mappings"]:
        mapping["status"] = "approved" if mapping["source"] and mapping["requirement_ids"] else "rejected"
    rules.recommend(result, dict.fromkeys(rules.FACTORS, 3))
    result["sdlc"]["status"] = "approved"
    return result


def test_unchanged_evidence_remains_usable_after_human_review(project):
    assert rules.blockers(project) == []
    assert rules.compliance_freshness_reason(project) is None
    assert len(project["compliance_snapshot"]["corpus_sha256"]) == 64


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", "2.0"),
        ("text", "A materially changed authentication control."),
        ("effective_date", "2999-01-01"),
    ],
)
def test_changed_knowledge_content_blocks_previous_baseline(project, monkeypatch, field, value):
    policies = copy.deepcopy(rules.load_policies())
    policies[0][field] = value
    monkeypatch.setattr(rules, "load_policies", lambda: policies)
    assert any("Knowledge-base content" in reason for reason in rules.blockers(project))
    rules.compliance(project)
    assert rules.compliance_freshness_reason(project) is None
    assert any("disposition" in reason for reason in rules.blockers(project))


def test_same_corpus_becomes_stale_when_source_expires(project, monkeypatch):
    class Today(date):
        @classmethod
        def today(cls):
            return cls(2030, 1, 10)

    class Later(date):
        @classmethod
        def today(cls):
            return cls(2030, 1, 12)

    policies = copy.deepcopy(rules.load_policies())
    policies[0]["expires_on"] = "2030-01-11"
    monkeypatch.setattr(rules, "load_policies", lambda: policies)
    monkeypatch.setattr(rules, "date", Today)
    rules.compliance(project)
    digest_before = project["compliance_snapshot"]["corpus_sha256"]
    assert rules.compliance_freshness_reason(project) is None
    monkeypatch.setattr(rules, "date", Later)
    assert rules.knowledge_snapshot(project, policies)["corpus_sha256"] == digest_before
    assert "applicability has changed" in rules.compliance_freshness_reason(project)


def test_policy_that_becomes_effective_requires_new_review(project, monkeypatch):
    policies = copy.deepcopy(rules.load_policies())
    policies[0]["effective_date"] = "2030-02-01"
    monkeypatch.setattr(rules, "load_policies", lambda: policies)

    class Clock(date):
        value = date(2030, 1, 1)

        @classmethod
        def today(cls):
            return cls.value

    monkeypatch.setattr(rules, "date", Clock)
    rules.compliance(project)
    Clock.value = date(2030, 2, 1)
    assert rules.compliance_freshness_reason(project)


def test_missing_snapshot_fails_closed_for_old_saved_projects(project):
    del project["compliance_snapshot"]
    assert any("no knowledge-base snapshot" in reason for reason in rules.blockers(project))


def test_unreadable_knowledge_base_blocks_final_without_crashing(project, monkeypatch):
    def unreadable():
        raise OSError("File not found")

    monkeypatch.setattr(rules, "load_policies", unreadable)
    assert any("unavailable or invalid" in reason for reason in rules.blockers(project))


def test_changed_jurisdiction_invalidates_even_unchanged_corpus(project):
    project["jurisdiction"] = "United Kingdom"
    assert rules.compliance_freshness_reason(project)


def test_changed_requirement_reopens_same_question_without_erasing_answer(project):
    requirement = project["requirements"][0]
    requirement["statement"] = "The system shall display every application quickly."
    rules.quality(project)
    question = next(q for q in project["questions"] if "quickly" in q["text"])
    question.update(status="answered", answer="Use a target latency of two seconds.")
    rules.quality(project)
    assert next(q for q in project["questions"] if q["id"] == question["id"])["status"] == "answered"
    requirement["statement"] = "The system shall display every repayment status quickly."
    rules.quality(project)
    records = [q for q in project["questions"] if q["text"] == question["text"]]
    assert len(records) == 2
    renewed = next(q for q in records if q["status"] == "open")
    assert renewed["supersedes_question_id"] == question["id"]
    assert next(q for q in records if q["status"] == "answered")["answer"] == question["answer"]


def test_duplicate_questions_stay_bound_to_their_actual_requirement_pair(project):
    source = project["sources"][0]
    project["requirements"] = [
        rules.make_requirement("The system shall record every approval.", source) for _ in range(3)
    ]
    rules.quality(project)
    duplicate_questions = [
        q
        for q in project["questions"]
        if q["text"] == "Which requirement should remain the canonical record?"
    ]
    assert len(duplicate_questions) == 3
    duplicate_questions[0].update(status="answered", answer="Retain the first record in this pair.")
    rules.quality(project)
    duplicates = [q for q in project["questions"] if q["text"] == duplicate_questions[0]["text"]]
    assert len({q["id"] for q in duplicates}) == 3
    assert sum(q["status"] == "answered" for q in duplicates) == 1


def test_final_export_separates_rejected_records_from_implementation_baseline(project):
    rejected = rules.make_requirement("The system shall allow anonymous staff access.", project["sources"][0])
    rejected["status"] = "rejected"
    project["requirements"].append(rejected)
    data = exports.payload(project, final=True)
    assert all(r["status"] == "approved" for r in data["requirements"])
    assert data["excluded_requirements"] == [rejected]
    assert len(project["requirements"]) == 2  # Export must not mutate persisted records.
    report = exports.markdown(data, final=True)
    baseline, appendix = report.split("## Excluded requirements", 1)
    assert rejected["statement"] not in baseline
    assert rejected["statement"] in appendix
    assert "outside the approved implementation baseline" in appendix
    assert "Reviewed knowledge-base digest" in report


def test_excluded_pending_source_does_not_block_but_is_labelled_in_report(project):
    project["sources"][0].update(extracted=False, excluded=True)
    assert not any("pending sources" in b for b in rules.blockers(project))
    report = exports.markdown(project, final=True)
    assert "Source disposition: excluded from requirement extraction" in report


def test_draft_criteria_are_not_claimed_to_be_reviewed(project):
    project["requirements"][0]["status"] = "draft"
    report = exports.markdown(project)
    assert "Acceptance criteria (draft; human review required)" in report
    assert "analyst-reviewed" not in report
