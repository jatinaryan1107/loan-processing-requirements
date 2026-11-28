import { useState } from "react";
import type { FormEvent } from "react";
import {
  ArrowRight,
  ChevronDown,
  FileText,
  MessageSquareText,
  Plus,
  ListChecks,
  Upload,
} from "lucide-react";
import type { Project, Role, Mutate } from "../types";
import { formatDate } from "../lib/format";
import { Badge, Empty, Notice, Panel } from "../components/ui";

export function Gather({
  project,
  role,
  busy,
  mutate,
  llmAvailable,
}: {
  project: Project;
  role: Role;
  busy: boolean;
  mutate: Mutate;
  llmAvailable: boolean;
}) {
  const [useLlm, setUseLlm] = useState(false);
  const [upload, setUpload] = useState<File | null>(null);
  const [uploadKey, setUploadKey] = useState(0);
  async function addSource(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    if (
      await mutate(
        "/sources",
        Object.fromEntries(data),
        "POST",
        "Source saved. Run analysis to extract draft requirements.",
      )
    )
      form.reset();
  }
  async function uploadFile(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!upload) return;
    const data = new FormData();
    data.set("file", upload);
    if (
      await mutate(
        "/upload",
        data,
        "POST",
        "Document imported. Run analysis to extract requirements.",
      )
    ) {
      setUpload(null);
      setUploadKey((k) => k + 1);
    }
  }
  const unanswered = project.sources.filter(
    (s) => !s.extracted && !s.excluded,
  ).length;
  return (
    <>
      {role === "ba" ? (
        <div className="gather-grid">
          <Panel
            title="Stakeholder input"
            description="Paste a requirement, interview note or project document."
          >
            <form onSubmit={addSource}>
              <div className="form-row">
                <label>
                  Source name
                  <input
                    name="source_name"
                    required
                    minLength={2}
                    maxLength={200}
                    placeholder="Operations interview · 06 Nov"
                  />
                </label>
                <label>
                  Stakeholder
                  <input
                    name="stakeholder"
                    required
                    minLength={2}
                    maxLength={100}
                    placeholder="Operations lead"
                  />
                </label>
              </div>
              <label>
                Original input
                <textarea
                  name="text"
                  rows={7}
                  required
                  minLength={12}
                  maxLength={50000}
                  placeholder="The system shall allow an analyst to review an application and record the reason for every status change…"
                />
              </label>
              <div className="form-footer">
                <small>Original text is retained as evidence.</small>
                <button className="button primary" disabled={busy}>
                  <Plus size={16} />
                  Add source
                </button>
              </div>
            </form>
          </Panel>
          <Panel title="Import a document">
            <form className="upload-form" onSubmit={uploadFile}>
              <label className="upload-zone">
                <Upload size={27} />
                <strong>
                  {upload ? upload.name : "Choose a project document"}
                </strong>
                <span>TXT, PDF or DOCX · up to 5 MB</span>
                <input
                  key={uploadKey}
                  type="file"
                  accept=".txt,.pdf,.docx"
                  onChange={(e) => setUpload(e.target.files?.[0] || null)}
                />
              </label>
              <button
                className="button secondary full-width"
                disabled={busy || !upload}
              >
                Import document
                <ArrowRight size={16} />
              </button>
            </form>
            <Notice>
              Use synthetic or de-identified information. Scanned PDFs require
              text extraction before upload.
            </Notice>
          </Panel>
        </div>
      ) : (
        <Notice>
          Gathering and clarification responses are managed by a Business
          Analyst.{" "}
          {role === "developer" &&
            "Source documents are restricted in the developer view."}
        </Notice>
      )}
      <section className="analysis-banner">
        <div>
          <span className="analysis-icon">
            <ListChecks size={23} />
          </span>
          <div>
            <h3>From source text to structured drafts</h3>
            <p className="analysis-progress" role="status">
              {unanswered
                ? `${unanswered} source${unanswered === 1 ? "" : "s"} ready for analysis.`
                : project.sources.some(
                      (source) => source.extracted && !source.excluded,
                    )
                  ? "Analysis up to date. See drafts in Analyse & validate."
                  : "Add a source to start analysis."}
            </p>
          </div>
        </div>
        {role === "ba" && (
          <div className="analysis-actions">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={useLlm}
                disabled={!llmAvailable || busy}
                onChange={(e) => setUseLlm(e.target.checked)}
              />
              {llmAvailable
                ? "Use configured LLM (masked input)"
                : "LLM unavailable · local rules active"}
            </label>
            <button
              className="button primary"
              disabled={
                busy || !project.sources.length || (useLlm && !unanswered)
              }
              onClick={() =>
                mutate(
                  "/analyse",
                  { use_llm: useLlm },
                  "POST",
                  "Analysis complete. Review the drafts and clarification questions.",
                )
              }
            >
              <ListChecks size={16} />
              Run analysis
            </button>
          </div>
        )}
      </section>
      <Panel
        title="Clarify what’s missing"
        description="Questions adapt to the gaps and conflicts found in the current requirements."
        action={
          <Badge tone="amber">
            {project.questions.filter((q) => q.status === "open").length} open
          </Badge>
        }
      >
        {project.questions.length ? (
          <div className="question-list">
            {project.questions.map((q) => (
              <div className="question" key={q.id}>
                <div className="question-heading">
                  <span>
                    <MessageSquareText size={18} />
                    {q.text}
                  </span>
                  <Badge tone={q.status === "answered" ? "teal" : "amber"}>
                    {q.status}
                  </Badge>
                </div>
                <small className="mono">
                  {q.requirement_ids.join(" · ") || "Project-level question"}
                </small>
                {q.answer && <p className="answer">{q.answer}</p>}
                {role === "ba" && q.status === "open" && (
                  <form
                    className="answer-form"
                    onSubmit={async (e) => {
                      e.preventDefault();
                      const form = e.currentTarget;
                      const answer = String(new FormData(form).get("answer"));
                      if (
                        await mutate(
                          `/questions/${q.id}/answer`,
                          { answer },
                          "POST",
                          "Answer saved as a linked source. Run analysis to update the findings.",
                        )
                      )
                        form.reset();
                    }}
                  >
                    <label className="sr-only" htmlFor={`answer-${q.id}`}>
                      Answer: {q.text}
                    </label>
                    <input
                      id={`answer-${q.id}`}
                      name="answer"
                      required
                      minLength={3}
                      maxLength={5000}
                      placeholder="Add a specific, testable answer…"
                    />
                    <button className="button secondary" disabled={busy}>
                      Save answer
                      <ArrowRight size={15} />
                    </button>
                  </form>
                )}
              </div>
            ))}
          </div>
        ) : (
          <Empty title="Questions will appear after analysis">
            Add sources and run analysis to identify details that need
            clarification.
          </Empty>
        )}
      </Panel>
      <Panel
        title="Source library"
        description="Every extracted requirement links back to one of these records."
        action={<Badge>{project.sources.length} sources</Badge>}
      >
        {project.sources.length ? (
          <div className="source-list">
            {project.sources.map((s) => (
              <details className="source" key={s.id}>
                <summary>
                  <FileText size={21} />
                  <span>
                    <strong>{s.source_name}</strong>
                    <small>
                      {s.stakeholder} · {formatDate(s.created_at)}
                    </small>
                  </span>
                  <Badge
                    tone={
                      s.excluded ? "neutral" : s.extracted ? "teal" : "amber"
                    }
                  >
                    {s.excluded
                      ? "Excluded"
                      : s.extracted
                        ? "Analysed"
                        : "Awaiting analysis"}
                  </Badge>
                  {s.synthetic && <Badge>Synthetic</Badge>}
                  <ChevronDown size={16} />
                </summary>
                <div className="source-content">
                  <small className="mono">{s.id}</small>
                  <pre>{s.text}</pre>
                  {s.excluded && (
                    <p className="muted">
                      Excluded from analysis. The original source remains in the
                      evidence record.
                    </p>
                  )}
                  {role === "ba" && !s.extracted && !s.excluded && (
                    <form
                      onSubmit={async (event) => {
                        event.preventDefault();
                        const note = String(
                          new FormData(event.currentTarget).get("note"),
                        );
                        await mutate(
                          `/sources/${s.id}/exclude`,
                          { note },
                          "POST",
                          "Source excluded from analysis. Original evidence is retained.",
                        );
                      }}
                    >
                      <label>
                        Exclusion reason
                        <input
                          name="note"
                          required
                          minLength={3}
                          maxLength={2000}
                          placeholder="Explain why this source should not be analysed"
                        />
                      </label>
                      <button className="button secondary" disabled={busy}>
                        Exclude source
                      </button>
                    </form>
                  )}
                </div>
              </details>
            ))}
          </div>
        ) : (
          <Empty title="No source records yet">
            Add stakeholder input or import a document to begin.
          </Empty>
        )}
      </Panel>
    </>
  );
}
