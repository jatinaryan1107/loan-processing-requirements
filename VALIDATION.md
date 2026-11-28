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

The four mandatory capabilities work end to end as a local advisory MVP. These checks do not establish analysis accuracy on unseen banking documents or legal compliance. Rich DOCX/PDF output, OCR, enterprise identity, encryption at rest, formal multi-party adoption approval and the original brief's empirical research evaluation remain deferred; see the README and requirements traceability document.

The final export records a reviewed requirements baseline. Rejection of an unsupported compliance mapping preserves an unresolved evidence limitation; it does not waive a legal obligation or approve production deployment.

## Architecture review

The follow-up review split application composition, API routes, request schemas, authentication, project services and ingestion into separate modules. The frontend now separates screens, shared components, transport and session state. Additional regression tests cover stale-tab rejection, concurrent snapshot commits, server-side logout, excluded-source recovery, changed/expired knowledge evidence, strict provider endpoints, bounded model responses and approved-only final baselines. The live four-role workflow was rerun after these changes and passed with no runtime errors.

SQLite project aggregates remain a deliberate local-MVP choice. Enterprise identity, tenant isolation, and process-isolated untrusted file parsing remain outside this iteration.

Project context edits use the same role and revision checks as requirement edits. Regression cases cover renames that preserve evidence, jurisdiction changes that invalidate derived reviews, stale updates, and the distinction between a second reviewer and a response-time target.


## Live model extraction, 26 November 2026

A browser session opened the Business Analyst workspace, added one synthetic workshop note about reasons for application status changes and an undefined history response time, selected **Use configured LLM (masked input)** and ran analysis. OpenRouter returned a completion from `nvidia/nemotron-3.5-super-vl:free` via `openrouter/free`. The application stored two drafts and one model clarification question. Both evidence quotes occurred verbatim in the input. The test checked the provider completion ID and the served model in the extraction record, then opened **Documents & audit** and verified the provider column. This verifies a single real provider exchange. The regression suite continues to use mocked model responses.

## Agent and retrieval verification, 28 November 2026

The backend suite passed all 115 tests on Python 3.13.9. Python lint and formatting, frontend formatting, the TypeScript production build and the Windows startup check passed.

A fresh browser run submitted a personal-loan workshop note asking for instant approvals and officer review of every application. OpenRouter returned six drafts and four clarification questions through `nvidia/nemotron-3.5-super-vl:free`. The test checked each evidence quote against the input, the provider completion ID, and the model shown in the audit screen. One question explicitly asked how instant approval could coexist with mandatory officer review.

ChromaDB 1.5.9 with local MiniLM embeddings retrieved authentication clause 1.1 for a paraphrase about proving identity before viewing restricted loan information. It had no matching keyword and a cosine distance of 0.242. An unrelated cafeteria requirement produced no match. A second verification reused the persistent policy collection. In Chrome the seeded Authentication card displayed the matching keyword and distance of 0.252. The four-role browser walkthrough passed through final Markdown export with zero browser runtime errors.
