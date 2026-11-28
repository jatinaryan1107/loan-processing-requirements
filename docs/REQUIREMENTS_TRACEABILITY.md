# Requirements traceability

The authority for the requirements below is the complete `references/Problem Statement.docx`, followed by `references/PROJECT_CONTEXT.md` and the implementation brief. Section numbers refer to the numbered headings in the original Word document, not inferred page numbers.

**Implemented** means an executable MVP behavior exists. **Partial** means a bounded version exists with material limitations. **Deferred** means the capability is outside this iteration. Neither a passing automated test nor a human demo approval proves legal compliance or production readiness.

## Four mandatory functionalities

| Functionality | Implementation and API | Interface and verification | Scope |
| --- | --- | --- | --- |
| Requirement Gathering | `backend/routes.py`: project creation, `POST /api/projects/{id}/sources`, `/upload`, `/questions/{qid}/answer`; `storage.py` retains originals, IDs and timestamps. | Projects and Gather screens; API workflow and document parsing tests. | Implemented for text, TXT/PDF/DOCX and clarification answers. No OCR or email/meeting integration. |
| Requirement Analysis and Validation | `agents/extraction_agent.py`, `classification_agent.py` and `quality_agent.py`; `llm.py` optional provider; `/analyse`, requirement PATCH and `/review`; `agents/documentation_agent.py`. | Analyse screen with source evidence, edits, acceptance criteria and decisions; rule and workflow tests. | Implemented baseline. Semantic comprehension and testability of suggestions remain subject to human review. |
| Compliance Verification | `agents/compliance_agent.py` and `retrieval.py` local clause matching; `/compliance` and `/mappings/{mid}/review`; versioned local knowledge fixture and citation snapshots. | Compliance screen; cited-source, unsupported-source and role tests. | Implemented advisory mechanics using synthetic policy evidence. No approved legal corpus or legal determination. |
| SDLC Model Recommendation | `agents/sdlc_agent.py` deterministic ranking and workflow generation; `/sdlc`, `/sdlc/decision`. | SDLC screen; ranking stability and permission tests. | Implemented for nine factors, multiple models and hybrids. Scores are uncalibrated suitability points. |

## Original problem statement sections

| Section | Requirement | Module, endpoint or record | Status and limitations |
| --- | --- | --- | --- |
| 1 Define the system scope | Financial-domain requirements and standard deliverables | Project model; `agents/documentation_agent.py`; all six interface stages. | **Partial by design:** loan-processing software requirements only, following §18 and coursework context. No lending operations. |
| 2 Identify stakeholders | Stakeholder inputs and role-specific participation | `/api/session`; server-side role checks; source `stakeholder`; four demo identities. | **Partial:** BA, Compliance Officer, PM and Developer. Other stakeholder roles and a full interview-template library are deferred. |
| 3 Define input sources | Structured/unstructured content and masking | `/sources`, `/upload`, `/questions/{qid}/answer`; `llm.py` masking boundary. | **Partial:** pasted text and three document formats. No mailbox/API connectors, OCR or guaranteed complete sensitive-data detection. |
| 4 Design the multi-agent architecture | Orchestration, narrow agent responsibilities and approval gates | `routes.py` pipeline and `services.py` project operations; `agents/coordinator_agent.py`, `llm.py`, `agents/`; persisted `runs` and `audit`. | **Partial:** named logical stages in one application, not independent autonomous processes. Rules provide the keyless baseline. |
| 5 Build the financial knowledge base | Approved, versioned, attributable knowledge | Local knowledge fixture; mapping `source` records with clause, jurisdiction, version, effective date and applicability. | **Partial:** synthetic organisational policy fixture only. No authoritative financial regulation collection or knowledge administration UI. |
| 6 Implement retrieval-grounded generation | Evidence retrieval, citations, confidence and escalation | Compliance clause matching; mapping evidence; requirement source links; run evidence and provider fields. | **Partial:** ChromaDB clause retrieval with keyword evidence, cosine distances and explicit unsupported cases. General retrieval-augmented legal generation is outside the MVP. |
| 7 Design requirement-gathering conversations | Adaptive questions and follow-up | Quality flags produce questions; `/questions/{qid}/answer` stores answers as linked sources; Gather/Analyse UI. | **Partial:** rule-triggered follow-up, not a fully autonomous natural-language interviewer. |
| 8 Extract and structure requirements | Stable ID, statement, category, source, justification, priority, dependencies, assumptions, acceptance criteria, risk, confidence and status | Requirement records populated by analysis and edited/reviewed through protected routes. | **Implemented baseline:** automatically proposed metadata must be reviewed; dependencies and assumptions are not exhaustively inferred. |
| 9 Classify the requirements | Functional/non-functional and multiple categories | `agents/classification_agent.py`; requirement `kind` and `categories`. | **Partial:** lexical multi-label rules with optional model extraction, not a trained or evaluated classifier. |
| 10 Analyse requirement quality | Ambiguity, incompleteness, inconsistency, duplication, testability and missing controls | `agents/quality_agent.py` quality checks; `flags`, `questions`; Analyse screen. | **Partial:** bounded heuristics; arbitrary semantic conflict, feasibility and undefined terminology are not comprehensively solved. |
| 11 Perform compliance and security analysis | Applicable evidence, controls, gaps and authorised interpretation | `/compliance`, `/mappings/{mid}/review`; versioned cited-source snapshots and history. | **Partial:** real review workflow, synthetic evidence. Missing approved sources stay unsupported; no legal conclusion. |
| 12 Generate requirement artefacts | SRS, stories, criteria, use cases, traceability, risk and open issues | `agents/documentation_agent.py`; `/export?format=markdown|json`; Export screen. | **Partial:** generated Markdown/JSON package from recorded data. Rich standalone DOCX/PDF, detailed process models and complete expert risk registers are deferred. |
| 13 Extract SDLC decision factors | Project stability, risk, complexity, legacy, change and delivery/testing needs | `/sdlc` factor form and persisted `factors`. | **Partial:** nine factors entered explicitly on a 1–5 scale. System size, budget, schedule, formal verification and failure consequences are not independent inputs. |
| 14 Design the SDLC selection engine | Explainable ranked alternatives and human decision | `agents/sdlc_agent.py`; `/sdlc`; `/sdlc/decision`; ranked rationale and decision history. | **Implemented MVP baseline:** deterministic scoring for named models and hybrids. PM decision implemented; separate architect/security/compliance adoption signatures deferred. |
| 15 Generate a project-specific SDLC workflow | Phases, activities, roles, outputs, checks and gates | SDLC `workflow` with entry/exit criteria, security checkpoint and approval gate. | **Partial:** tailored templates based on model/project factors. Gates describe a future software project; the app does not operate a CI/CD release system. |
| 16 Implement human-in-the-loop controls | Review, modify, reject and reapprove changed outputs | Requirement and mapping reviews; PM decisions; histories; server-side final export gates. | **Partial:** four-role review and approval invalidation. Separate architecture-critical/production-readiness approvals and a formal consensus workflow are deferred. |
| 17 Secure the Agentic AI platform | Identity, access, masking, injection boundaries, audit and model/KB versions | Opaque demo sessions; route permissions; bounded parsing; `llm.py`; `runs`; `audit`. | **Partial:** local demonstration controls only. MFA, TLS deployment, encrypted storage, tenant isolation, immutable external audit and retention enforcement are deferred. |
| 18 Develop the prototype | Relational storage, rules, workflow UI and document generation, starting with one use case | FastAPI + SQLite + React/TypeScript; README setup and start scripts. | **Implemented MVP architecture:** local loan requirements domain. ChromaDB stores policy vectors locally. Distributed workflow execution and enterprise IAM are outside the MVP. |
| 19 Test and evaluate the system | Accuracy, completeness, coverage, suitability, corrections, time and satisfaction | `tests/`, integration tests, frontend type/build checks; `docs/EVALUATION.md`; `VALIDATION.md`. | **Partial:** automated functional verification and synthetic walkthrough. Empirical quality metrics and comparative studies have not been measured. |
| 20 Deploy, monitor and improve | Advisory rollout, evidence, updates, repeat evaluation | Local launch; synthetic demo; persisted sources, decisions, runs and audit; draft/final exports. | **Partial:** advisory local use. Production monitoring, automatic regulatory updates, deployment governance and broader financial domains are deferred. |

## Verification evidence

`VALIDATION.md` records the commands actually run, test results and the browser workflow observed during integration. Test names and assertions are the executable evidence; this table is the specification-to-code index. The [API contract](API_CONTRACT.md) gives payload shapes and roles, and [UML](UML.md) connects the coursework model to those calls.

The public API tests in `tests/test_boundaries.py` cover these specification boundaries:

| Boundary | Test |
| --- | --- |
| Server-side identity and permission checks | `test_authentication_and_role_spoofing`, `test_non_manager_cannot_select_lifecycle` |
| Approval invalidation and developer visibility | `test_approved_text_is_hidden_again_after_edit` |
| Unsupported compliance evidence | `test_unknown_evidence_cannot_be_approved` |
| Human approval before final export | `test_final_export_cannot_bypass_review`, `test_complete_review_workflow_and_later_invalidation` |
| Safe parse failures and bounded document handling | `test_bad_upload_has_human_readable_error`, `test_docx_uncompressed_size_is_bounded` |
| Prompt-injection boundary and stable requirement IDs | `test_ingested_instructions_stay_untrusted_drafts` |

`tests/test_uploads.py::test_document_upload_analysis_and_review_survive_restart` runs independently for TXT, PDF and DOCX. It verifies successful parsing, DOCX table text, source metadata, extraction provenance, stable requirement IDs, approval-history persistence, application restart and JSON export. `tests/test_llm_boundary.py` exercises explicit provider opt-in, masking, literal evidence validation and malformed responses using mocked calls; it does not call an external model.

## Important interpretation boundaries

- A verified local citation proves which stored clause was used; it does not prove the source is legally authoritative, current or applicable to a real institution.
- An approved requirement records an analyst decision; it does not make heuristic analysis complete.
- A lifecycle score records a deterministic rule calculation; it is not a prediction of project success.
- A final export records completion of implemented review gates. It does not certify regulatory compliance or authorise a production banking deployment.

