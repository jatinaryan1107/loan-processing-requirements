# AI-Based Loan Processing Requirements Management

A local requirements-engineering assistant for teams designing loan-processing software. Capture source material, review structured requirements, inspect policy evidence, choose a development lifecycle and export an auditable specification.

The application does not process loans, perform KYC, approve credit, move money or provide legal determinations. It runs without an API key using explicitly labelled deterministic rules. Optional LLM extraction produces drafts for human review.

## Run locally

Requirements: Python 3.11 or later, Node.js 20.19+ or 22.12+, and npm. Run the following once from the repository directory. Setup downloads the Python and frontend dependencies and a 79 MiB embedding model. Once cached, local analysis and policy search work offline. OpenRouter is used only when model-assisted extraction is selected.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m backend.retrieval
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
cd frontend
npm.cmd ci
npm.cmd run build
cd ..
.\start.ps1
```

### Linux or macOS

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m backend.retrieval
[ -f .env ] || cp .env.example .env
cd frontend
npm ci
npm run build
cd ..
sh start.sh
```

Open **http://127.0.0.1:8000**. The same server hosts the interface and API. API documentation is at `/docs` and the health endpoint is `/api/health`. Press Ctrl+C to stop. On later runs, use only `.\start.ps1` or `sh start.sh`; rebuild after changing the frontend.

If port 8000 is occupied, use `.\start.ps1 -Port 8100` or `sh start.sh --port 8100`, then open that port. To check prerequisites without starting a server, use `-Check` or `--check`. The launchers check the virtual environment, Python dependencies and built interface. They do not reinstall dependencies, reset data or claim the chosen port is free.

### During development

For live frontend updates, run the backend on port 8000 with `.\start.ps1` or `sh start.sh`. In a second terminal, enter `frontend` and run `npm run dev` (`npm.cmd run dev` in PowerShell), then open **http://127.0.0.1:5173**. Vite forwards API requests to port 8000. This development proxy uses port 8000 even if the built-app launcher supports another port.

The SQLite database is created on first startup at `data/requirements.db`; an empty database receives a synthetic demo project. Projects persist across restarts. Stop the server before backing up the database and its `-wal`/`-shm` companions if present. Startup preserves `.env` and existing data. Databases, secrets and dependency folders are excluded from Git.

`requirements-lock.txt` pins the application dependencies and ChromaDB version used for validation. `requirements.txt` lists the direct dependency constraints for deliberate upgrades; rerun the checks after updating either dependency set. The frontend lockfile records its tested dependency resolution.

## Demo identities

Choose a role on the login screen. There are no passwords or external accounts in this local demonstration. The API issues an opaque bearer session and checks the server-side role on every protected action. Selecting a role is intentionally available to anyone who can access the demo server; this is not production authentication.

| Role | API role | Available actions |
| --- | --- | --- |
| Business Analyst | `ba` | Create projects, add sources, upload documents, analyse, edit and review requirements, answer clarification questions and request compliance analysis. |
| Compliance Officer | `compliance` | Inspect evidence, run compliance analysis, amend interpretations and approve or reject mappings. |
| Project Manager | `pm` | Inspect analysis, enter project factors, rank and approve or reject an SDLC model, export a final package when its gates pass. |
| Software Developer | `developer` | Read the approved requirement view and its documentation; cannot change requirements or approve policy mappings. |

## Walk through the MVP

1. Sign in as **Business Analyst** and open the synthetic demo project. It includes vague language, conflicting retention requirements and policy review cases. Alternatively create a project with a name, description and jurisdiction.
2. In **Gather**, paste requirements or upload a TXT, PDF or DOCX file. Sources preserve the extracted text, source name, stakeholder and timestamp. Uploads are limited to 5 MB and 100,000 extracted characters; PDFs must be unencrypted, text-based and no longer than 100 pages. Image-only PDFs require manual transcription because OCR is not included.
3. Run **Analyse**. The app extracts draft requirements, classifies them, proposes acceptance criteria and flags rule-detectable problems. Follow the evidence back to the original source. Answer clarification questions, then run analysis again for answers that contain complete requirement statements. Short answers are retained as interview context; they do not create invented requirements. Review or edit the affected requirement explicitly rather than treating an answer as automatic approval.
4. Edit unclear statements and their acceptance criteria, then approve or reject each requirement with a review note. Edits require renewed review. Rule-based checks are intentionally conservative and incomplete; a clean screen does not establish completeness or correctness.
5. Run **Compliance**, then switch to **Compliance Officer**. Inspect the full clause, jurisdiction, version, effective date and applicability before reviewing a mapping. The bundled policy is synthetic. Unsupported legal or policy claims display **“No verified source available / requires compliance officer review.”** They cannot be approved as verified evidence.
6. Switch to **Project Manager** and enter the nine SDLC factors on a 1–5 scale. Compare the ranked models and factor-by-factor explanations. Approve or reject a selected model with a note; inspect its phases, activities, responsibilities, deliverables and gates.
7. In **Export**, download Markdown or JSON. Draft exports remain labelled as drafts. A final export requires the appropriate role and the recorded review gates. A completed demo review is not a legal compliance certificate or production-readiness approval.
8. Switch to **Software Developer** to inspect the approved view. Review the audit trail and agent-run records in the other authorised roles to see how sources, analyses and human decisions connect.

## Configuration

Copy `.env.example` to `.env` and keep it out of Git.

| Variable | Purpose |
| --- | --- |
| `DATABASE_PATH` | SQLite database location; defaults to `data/requirements.db`. |
| `ENABLE_DEMO_LOGIN` | Enables the openly selectable demo roles. Disable before replacing them with a real identity integration. |
| `ENABLE_LLM` | Defaults to `false`; external model calls require explicit opt-in. |
| `LLM_ALLOW_EXTERNAL` | A second explicit opt-in, also `false` by default. Must be `true` alongside `ENABLE_LLM` for model extraction. |
| `LLM_API_KEY` | Provider credential, loaded from the environment; never checked into source control. |
| `LLM_MODEL` | Model identifier accepted by the configured provider. |
| `LLM_BASE_URL` | Compatible provider API base URL. |

Without an LLM, extraction, classification, quality checks, clarification prompts, policy retrieval and SDLC ranking use deterministic rules. These are working baseline algorithms, not simulated model responses. The interface identifies this mode. Set both opt-in flags to `true`, supply a key and model, and use a compatible `/chat/completions` provider to enable model extraction. The base URL must use HTTPS, with loopback HTTP allowed for local providers. Returned data must pass schema and literal-evidence validation and still needs human approval. Provider failures are reported rather than silently presented as successful model output. The deterministic SDLC scores are never replaced by model-generated percentages.

For OpenRouter, use `LLM_BASE_URL=https://openrouter.ai/api/v1` and `LLM_MODEL=openrouter/free` with your own local key and both opt-in flags enabled. Restart the server, add a fresh synthetic source in **Gather requirements**, select **Use configured LLM (masked input)** and click **Run analysis**. Under **Documents & audit**, the extraction record shows the served model when the provider supplies it. Existing extracted sources are skipped.

Only synthetic or otherwise approved, non-confidential inputs should be used. Automatic masking cannot reliably identify names, account numbers, secrets or every form of sensitive information. Inspect and remove sensitive details before enabling external calls. Ingested text is treated as data and does not gain permission to change server instructions, execute tools or approve its own results.

On the Overview screen, a Business Analyst can edit the project details. A change to scope or jurisdiction reopens compliance and lifecycle review. The audit log retains the previous values and decisions.

## Architecture

```text
React / TypeScript interface
        | authenticated JSON + bounded document uploads
FastAPI application (app.py) and HTTP adapters (routes.py)
        | named analysis stages and recorded evidence
        +-- schemas.py / auth.py: input validation and role checks
        +-- services.py: project operations, revision checks and safe views
        +-- ingestion.py: TXT, DOCX and PDF extraction in worker threads
        +-- agents/: coordinator, extraction, classification, quality, clarification,
        |           risk, compliance, SDLC and documentation
        +-- rules.py: final export gates
        +-- retrieval.py: local MiniLM embeddings and persistent ChromaDB search
        +-- llm.py: optional provider boundary
        +-- storage.py: persistent SQLite project aggregates
```

The frontend separates screens, shared components, API/session helpers and the `useWorkspace` state hook. Project edits operate on a snapshot outside SQLite's writer lock; a short transaction compares the original revision before saving. The UI sends `If-Match` with the version the user reviewed. A stale edit receives HTTP 409 and reloads the current project rather than overwriting it. Logout revokes the session token on the server.

SQLite stores each project as an atomic JSON aggregate. This keeps source evidence and review decisions consistent for a local coursework demo; a larger multi-user deployment should separate event history and introduce queryable entity tables. Document parsing runs off the event loop but is not isolated in a resource-limited process. Use trusted synthetic documents for the demo.

Compliance reviews record a knowledge-base fingerprint and applicability snapshot. Changes to that evidence, source expiry or rule versions require fresh review before final export. Final exports separate approved requirements from rejected records retained for traceability. If a pending source fails analysis, use its **Exclude source** action with a reason, then add a smaller corrected source; the original remains in the evidence record.

Each project retains original sources, stable requirement IDs, source links, review history, clarification answers, policy mapping snapshots, lifecycle decisions, audit entries and named agent runs. Logical agents have narrow responsibilities inside one process; the prototype does not claim a distributed autonomous agent platform.

### Follow a request in the backend

The screen calls an endpoint in `backend/routes.py`. The implementation of each stage is in `backend/agents/`.

| Agent file | Function to open | Observable result |
| --- | --- | --- |
| `coordinator_agent.py` | `analyse_pending` | Processes the pending sources and runs the downstream checks on one project revision. |
| `extraction_agent.py` | `extract_source`, `make_requirement` | Creates drafts with source IDs and evidence. For live extraction the route calls `backend/llm.py: extract` to obtain and validate the model response first. |
| `classification_agent.py` | `classify` | Assigns type and categories in rules mode. Model-assisted drafts retain their validated model classifications. |
| `risk_agent.py` | `rate`, `assess` | A security, privacy or compliance category triggers high review risk. Other requirements receive medium risk. |
| `quality_agent.py` | `quality` | Flags vague terms, duplicated statements, conflicting values and gaps, with links to the affected requirements. |
| `clarification_agent.py` | `prepare` | Turns findings into questions, retains prior answers and tracks changes in the evidence. |
| `compliance_agent.py` | `policy_applicable`, `compliance` | Filters eligible sources, calls `backend/retrieval.py`, and saves source-backed proposals for officer review. |
| `sdlc_agent.py` | `recommend`, `workflow` | Ranks model profiles, records each factor contribution and produces lifecycle phases for PM review. |
| `documentation_agent.py` | `payload`, `markdown` | Builds a draft or approved specification from stored records after the route checks the caller and export gates. |

To bound local processing, each project accepts at most 100 sources, 1,000,000 source characters in total and 500 extracted requirements. Deterministic extraction accepts at most 150 candidate statements in one source. Exceeding an extraction limit stops the operation without saving a partial batch; split larger inputs into scoped projects or smaller documents. DOCX expanded contents are limited to 20 MB and 1,000 archive entries.

The local knowledge base in `backend/knowledge/policies.json` contains an explicitly synthetic policy for demonstrating evidence handling. It is not an RBI, privacy, KYC or security-standard dataset. Synthetic clauses apply only to the seeded synthetic project. A non-synthetic entry additionally requires an `approved_by` record, an explicit `applicable_project_ids` allowlist and a jurisdiction matching the project. Complete citation metadata, an effective date that has arrived, and any expiry date are checked before retrieval. These are local metadata checks, not independent verification of source authority or reviewer identity. Adding approved source material requires careful versioning and qualified review. Running Compliance queries a local ChromaDB index of eligible clause texts with 384-dimensional MiniLM embeddings. For each requirement the two nearest clauses are considered. A cosine distance of 0.40 or less or a matching policy keyword proposes a link. Expand **How these requirements matched** to see the actual distance and matched terms. An officer reviews the exact clause and decides whether it covers the requirement. The initial demo snapshot uses keywords so first startup does not wait on the model. A live verification replaces that snapshot. The index lives in `policy_vectors/` beside the project database.

### How the SDLC ranking works

The baseline has a fixed target profile for each model. For each of nine factors, a model receives `4 - abs(entered_value - target_value)` points. Contributions are added with equal weights, giving a score from 0 to 36. The interface displays each entered value, target and contribution. Ties are ordered by model name; a small score difference should not be treated as a strong preference.

| Factor | 1 means | 5 means |
| --- | --- | --- |
| Requirement stability | Unsettled requirements | Stable requirements |
| Complexity | Simple project | High complexity |
| Regulatory criticality | Low regulatory significance | High regulatory significance |
| Security risk | Low risk | High risk |
| Stakeholder availability | Rarely available | Frequently available |
| Expected change | Little expected change | Frequent changes |
| Legacy dependence | Few dependencies | Strong dependencies |
| Testing obligations | Light verification needs | Extensive verification needs |
| Delivery cadence | Infrequent releases | Frequent delivery |

The Agile / V-Model hybrid is included when regulatory criticality and expected change are both at least 4. This condition gives the hybrid a concrete justification: evolving work with formal verification needs. Profiles and thresholds are inspectable in `backend/agents/sdlc_agent.py`; they are design choices for the prototype and need expert evaluation.

See [API contract](docs/API_CONTRACT.md), [UML](docs/UML.md), [requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md) and [evaluation plan](docs/EVALUATION.md).

## Test and build

From the repository root with the virtual environment active:

```sh
python -m pytest -q
cd frontend
npm run build
```

On Windows without activating the environment, use `.\.venv\Scripts\python.exe -m pytest -q` and `npm.cmd run build`. The suite covers authentication, role spoofing, final export gates, approval invalidation, malformed documents, embedded instructions and the optional provider boundary. `tests/test_uploads.py` verifies successful TXT/PDF/DOCX parsing and persistence of evidence, IDs and approval history across application restarts. The build performs TypeScript checking and writes the frontend bundle to `frontend/dist`. See `VALIDATION.md` for the actual integration results and any remaining failures.

## Scope adaptations and limitations

The original `Problem Statement.docx` is authoritative. `PROJECT_CONTEXT.md` narrows its financial-sector scope to loan-processing software requirements and four actors. The original documents are retained in `references/`. No separate UML image references were supplied. The diagrams describe implemented components and calls, preserving the coursework's four-function structure without introducing an operational `LoanApplication` entity.

The following are deliberate MVP limits:

- **Identity and deployment:** open demo role login, shared local projects and local bearer sessions. No MFA, enterprise identity, tenant/project membership, TLS termination, encrypted SQLite storage, tamper-proof audit service or full retention enforcement. Do not expose this server publicly or use it for confidential banking work.
- **Analysis:** heuristic extraction, lexical classification and limited ambiguity/conflict checks. Suggested acceptance criteria and generated use cases need analyst editing. Semantic contradictions, feasibility, exhaustive risk assessment and calibrated confidence remain unresolved research work.
- **Compliance:** bundled evidence is synthetic; no approved legal corpus was supplied. Human mapping approval means a reviewer accepted the recorded interpretation, not that the software meets a law or standard.
- **Approvals:** the four-role MVP uses BA requirement review, compliance-officer mapping review and PM lifecycle approval. The DOCX's separate architect/security-team signoffs and formal production-readiness workflow require additional roles and gates.
- **SDLC:** nine explicitly supplied factors and explainable rules. System size, budget, schedule and failure consequence are not independently modelled. Suitability scores are not probabilities or empirically calibrated recommendations.
- **Documents and integration:** TXT/PDF/DOCX ingestion and Markdown/JSON output. No OCR, mailbox connector, external issue tracker, native DOCX/PDF export, database migration framework or PostgreSQL adapter.
- **Evaluation:** automated checks and synthetic demonstrations do not measure extraction precision, hallucination rate, stakeholder satisfaction or time saved against manual practice. The required study design is documented separately.

Human stakeholders remain responsible for requirement baselines, high-impact interpretations and lifecycle adoption.
