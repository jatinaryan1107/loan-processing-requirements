# Implementation plan

The original problem statement and coursework context are preserved in `references/`. They define the scope of this MVP as software requirements for loan processing.

1. Read the complete specifications and inspect the workspace. Complete.
2. Implement a persistent API with server-side demo permissions, requirement provenance, analysis, cited compliance review, deterministic SDLC selection, approvals and exports. Complete.
3. Build an accessible React interface for all six stages and the four seeded roles. Complete.
4. Integrate optional, explicitly enabled, masked LLM extraction with schema validation and failure handling. Complete; provider boundary tested with mocks, no live key supplied.
5. Add UML and requirement traceability documentation, runnable setup instructions and automated workflow/security tests. Complete.
6. Install dependencies, run type/build checks and tests, start the app and exercise an end-to-end browser workflow. Complete; 105 tests passed, frontend checks passed and the four-role browser workflow passed. See VALIDATION.md.

No actual lending functions or authoritative regulatory determinations are in scope. The included policy is explicitly synthetic; missing legal evidence must remain visible. Production identity, encrypted storage, semantic retrieval and empirical research evaluation are later work.
