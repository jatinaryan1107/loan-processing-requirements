# Validation results

Verified on 21 November 2026 on Windows with Python 3.13.9 and Node.js 24.14.1. The application was run with synthetic input and without an LLM key.

## Automated checks

| Check | Observed result |
| --- | --- |
| `python -m pytest -q` | **110 passed** |
| `python -m ruff check backend tests` | Passed |
| `python -m ruff format --check backend tests` | Passed, 19 files formatted |
| `npm run typecheck` | Passed |
| `npm run build` | Passed; production bundle generated |
| `npm run format:check` | Passed |

Tests cover source provenance and stable IDs, successful TXT/PDF/DOCX parsing, database restart persistence, atomic extraction limits, malformed uploads, ambiguous wording, duplicates and numeric/negation conflicts, missing controls, source applicability, deterministic rankings, hybrid gating, factor-dependent workflows, role enforcement, draft visibility, database-instance isolation, review invalidation and final-export gates. Provider tests mock requests and check opt-in, masking, malformed responses and fabricated evidence rejection.

One upstream warning remains: the installed Starlette TestClient deprecates its current `httpx` transport in favour of `httpx2`. It does not fail the suite or affect the running API. The dependency lock records the tested versions. The restricted Windows test environment required loopback permission for Python's event loop; a normal local terminal uses the documented test command directly.

## Live browser workflow

The walkthrough used the production frontend and FastAPI on a separate localhost port with a fresh SQLite database. A headless Chrome walkthrough performed the following real UI actions:

1. Opened the seeded project as Business Analyst and inspected its quality findings.
2. Created a synthetic project, edited its context, entered a source and ran analysis.
3. Opened the extracted requirement and approved it with a review note, then read the saved decision in the expanded requirement.
4. Ran compliance verification and switched to Compliance Officer.
5. Confirmed approval was disabled for all six unsupported mappings; rejected each with a missing-evidence explanation.
6. Switched to Project Manager, ranked the lifecycle models, reviewed the resulting workflow and approved the selection.
7. Downloaded the approved Markdown SRS and checked its baseline label, traceability and missing-evidence dispositions.
8. Switched to Software Developer and confirmed the approved requirement was visible while editing and approval actions were unavailable.

**Result: passed, with zero browser runtime errors.** Screenshots of the observed interface are in `docs/screenshots/`. A separate browser regression held old load and mutation responses across a role switch and verified that they could not overwrite the new role's project. At 390 pixels wide, the role picker and all six workspace screens passed the horizontal overflow check. The login and overview were also inspected visually.

## Scope of the result

The four mandatory capabilities work end to end as a local advisory MVP. These checks do not establish analysis accuracy on unseen banking documents or legal compliance. No live external model request was made. Rich DOCX/PDF output, OCR, enterprise identity, encryption at rest, semantic retrieval, formal multi-party adoption approval and the original brief's empirical research evaluation remain deferred; see the README and requirements traceability document.

The final export records a reviewed requirements baseline. Rejection of an unsupported compliance mapping preserves an unresolved evidence limitation; it does not waive a legal obligation or approve production deployment.

## Architecture review

The follow-up review split application composition, API routes, request schemas, authentication, project services and ingestion into separate modules. The frontend now separates screens, shared components, transport and session state. Additional regression tests cover stale-tab rejection, concurrent snapshot commits, server-side logout, excluded-source recovery, changed/expired knowledge evidence, strict provider endpoints, bounded model responses and approved-only final baselines. The live four-role workflow was rerun after these changes and passed with no runtime errors.

SQLite project aggregates remain a deliberate local-MVP choice. Enterprise identity, tenant isolation, process-isolated untrusted file parsing and live provider verification remain outside this iteration.

Project context edits use the same role and revision checks as requirement edits. Regression cases cover renames that preserve evidence, jurisdiction changes that invalidate derived reviews, stale updates, and the distinction between a second reviewer and a response-time target.
