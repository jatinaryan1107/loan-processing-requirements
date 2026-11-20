# Evaluation

This project is a working prototype for requirements engineering in the loan-processing domain. Automated checks establish specific software behavior; they do not establish regulatory compliance, extraction accuracy on unseen documents, or suitability for production use.

## Reproducible checks

From the repository root, activate the Python virtual environment and run:

```sh
python -m pytest -q
cd frontend
npm run build
```

The backend and public-API boundary tests use isolated temporary databases. The frontend build includes TypeScript checking. A demo walkthrough in the README exercises the combined interface and API. Actual execution results are recorded in `VALIDATION.md` after integration; this document does not substitute a proposed check for a measured result.

## Research evaluation still needed

The original problem statement, section 19, proposes comparative research evaluation. No real-bank corpus, expert-labelled dataset, user study, or manual baseline was supplied. The following metrics are therefore **not measured**:

| Metric | Required evaluation method |
| --- | --- |
| Extraction precision, recall and F1 | Two independent analysts annotate source statements and compare extracted atomic requirements against an adjudicated reference set. |
| Requirement completeness | Experts score required domain topics and acceptance details against an agreed checklist. |
| Ambiguity and conflict detection accuracy | Label both positive and negative cases; report precision, recall, false positives and false negatives by category. |
| Regulatory-control coverage and citation correctness | A qualified compliance reviewer checks mappings against an approved, versioned jurisdiction-specific corpus. Count unsupported claims separately. |
| Hallucination rate | Review every generated proposition against its source; distinguish unsupported additions from reasonable suggestions clearly marked as drafts. |
| SDLC recommendation suitability | Compare ranked recommendations with independent architect and project-manager assessments, including disagreement and sensitivity to input factors. |
| Human correction rate | Track edits and rejections on a consented study dataset without exposing confidential source content. |
| Time saved and stakeholder satisfaction | Conduct a controlled comparison with manual requirements engineering and collect a standard questionnaire. |
| Traceability coverage | Verify every output requirement, mapping and decision resolves to a source, run or human decision record. |

Do not report a test-suite pass percentage as model accuracy. Deterministic suitability scores are rule outputs, not calibrated probabilities. The synthetic policy fixture demonstrates citation and review mechanics; it provides no evidence of legal compliance.

## Suggested evaluation sequence

1. Freeze a rule and knowledge-base version, then construct a synthetic corpus covering contradictions, missing details, privacy concerns, malformed uploads and instruction-like source text.
2. Independently label the corpus and predefine scoring criteria before running the app.
3. Compare deterministic mode with a configured LLM on the same masked inputs, recording provider, model, timestamps, errors and human corrections.
4. Review failures and revise rules; retain a held-out dataset for the next iteration.
5. Conduct an advisory-only pilot with authorised participants after identity, data protection and retention controls are implemented.
