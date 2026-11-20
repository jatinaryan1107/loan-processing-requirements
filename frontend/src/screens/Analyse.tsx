import { useState } from "react";
import type { FormEvent } from "react";
import {
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleHelp,
  FileText,
  Search,
  Sparkles,
} from "lucide-react";
import type { Project, Requirement, Role, Mutate } from "../types";
import { label } from "../lib/format";
import {
  Badge,
  Empty,
  Notice,
  Panel,
  History,
  DecisionForm,
} from "../components/ui";

export function Analyse({
  project,
  role,
  busy,
  mutate,
}: {
  project: Project;
  role: Role;
  busy: boolean;
  mutate: Mutate;
}) {
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const filtered = project.requirements.filter(
    (r) =>
      (filter === "all" || r.status === filter) &&
      `${r.id} ${r.statement} ${r.categories.join(" ")}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const projectFlags = project.flags.filter((f) => !f.requirement_ids.length);
  return (
    <>
      <div className="section-intro">
        <div>
          <h2>
            Requirement register{" "}
            <span className="count">{project.requirements.length}</span>
          </h2>
          <p>Drafts become a baseline through explicit human review.</p>
        </div>
        {role === "ba" && (
          <button
            className="button secondary"
            disabled={busy || !project.sources.length}
            onClick={() =>
              mutate("/analyse", {}, "POST", "Quality checks refreshed.")
            }
          >
            <Sparkles size={16} />
            Refresh analysis
          </button>
        )}
      </div>
      {role === "developer" && (
        <Notice>
          This view contains approved requirements only. Source evidence and
          internal review records are restricted.
        </Notice>
      )}
      {projectFlags.length > 0 && (
        <div className="project-findings">
          <h3>
            <CircleHelp size={18} />
            Project-wide findings
          </h3>
          {projectFlags.map((flag) => (
            <p key={flag.id}>
              <strong>{label(flag.type)}:</strong> {flag.message}
            </p>
          ))}
        </div>
      )}
      <div className="register-toolbar">
        <div
          className="filter-tabs"
          role="group"
          aria-label="Filter requirements"
        >
          {["all", "draft", "approved", "rejected"].map((value) => (
            <button
              key={value}
              className={filter === value ? "active" : ""}
              onClick={() => setFilter(value)}
            >
              {label(value)}
              <span>
                {value === "all"
                  ? project.requirements.length
                  : project.requirements.filter((r) => r.status === value)
                      .length}
              </span>
            </button>
          ))}
        </div>
        <label className="search-box">
          <Search size={17} />
          <span className="sr-only">Search requirements</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search requirements"
          />
        </label>
      </div>
      <div className="requirement-list">
        {filtered.map((r) => (
          <RequirementCard
            key={`${r.id}-${r.updated_at}`}
            requirement={r}
            project={project}
            role={role}
            busy={busy}
            mutate={mutate}
          />
        ))}
        {!filtered.length && (
          <Panel>
            <Empty title="No matching requirements">
              {project.requirements.length
                ? "Try another status or search term."
                : "Run analysis on a source to create the first draft requirements."}
            </Empty>
          </Panel>
        )}
      </div>
    </>
  );
}
function RequirementCard({
  requirement: r,
  project,
  role,
  busy,
  mutate,
}: {
  requirement: Requirement;
  project: Project;
  role: Role;
  busy: boolean;
  mutate: Mutate;
}) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const flags = project.flags.filter((f) => f.requirement_ids.includes(r.id));
  const source = project.sources.find((s) => s.id === r.source_id);
  async function edit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    if (
      await mutate(
        `/requirements/${r.id}`,
        {
          statement: data.get("statement"),
          priority: data.get("priority"),
          justification: data.get("justification"),
          acceptance_criteria: String(data.get("criteria"))
            .split("\n")
            .filter((s) => s.trim()),
        },
        "PATCH",
        "Requirement updated. Its approval has been reset for review.",
      )
    )
      setEditing(false);
  }
  return (
    <article className="requirement-card">
      <div className="requirement-top">
        <span className="mono requirement-id">{r.id}</span>
        <div className="badge-group">
          <Badge>{r.kind}</Badge>
          <Badge>{r.priority} priority</Badge>
          <Badge
            tone={
              r.status === "approved"
                ? "teal"
                : r.status === "rejected"
                  ? "rose"
                  : "neutral"
            }
          >
            {r.status}
          </Badge>
        </div>
      </div>
      <h3>{r.statement}</h3>
      <div className="requirement-meta">
        <span>{r.categories.join(" / ")}</span>
        <span>Risk: {r.risk}</span>
        <span>Heuristic confidence: {Math.round(r.confidence * 100)}%</span>
      </div>
      {flags.length > 0 && (
        <div className="requirement-flags">
          {flags.map((flag) => (
            <div key={flag.id}>
              <span className={`flag-type ${flag.severity}`}>
                <CircleHelp size={13} />
                {label(flag.type)}
              </span>
              <p>{flag.message}</p>
              {flag.question && <small>{flag.question}</small>}
            </div>
          ))}
        </div>
      )}
      <div className="requirement-bottom">
        <span>
          <FileText size={14} />
          {source?.source_name || `Source ${r.source_id}`}
        </span>
        <button
          className="text-button"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
        >
          {expanded ? "Hide details" : "Review requirement"}
          <ChevronDown size={15} className={expanded ? "rotated" : ""} />
        </button>
      </div>
      {expanded && (
        <div className="requirement-detail">
          {editing ? (
            <form onSubmit={edit}>
              <label>
                Requirement statement
                <textarea
                  name="statement"
                  defaultValue={r.statement}
                  required
                  minLength={12}
                  maxLength={5000}
                  rows={3}
                />
              </label>
              <div className="form-row">
                <label>
                  Priority
                  <select name="priority" defaultValue={r.priority}>
                    {["Must", "Should", "Could"].map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Business justification
                  <input
                    name="justification"
                    defaultValue={r.justification}
                    required
                    minLength={3}
                    maxLength={2000}
                  />
                </label>
              </div>
              <label>
                Acceptance criteria · one per line
                <textarea
                  name="criteria"
                  defaultValue={r.acceptance_criteria.join("\n")}
                  rows={4}
                  required
                />
              </label>
              <div className="button-row">
                <button className="button primary" disabled={busy}>
                  Save changes
                </button>
                <button
                  type="button"
                  className="button ghost"
                  onClick={() => setEditing(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <>
              <div className="two-columns">
                <div>
                  <h4>Acceptance criteria</h4>
                  <ul className="criteria-list">
                    {r.acceptance_criteria.map((criterion, i) => (
                      <li key={i}>
                        <Check size={14} />
                        {criterion}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4>Context and assumptions</h4>
                  <p>
                    {r.justification ||
                      "Business justification needs confirmation."}
                  </p>
                  <p className="muted">
                    Dependencies: {r.dependencies.join(", ") || "None recorded"}
                  </p>
                  <p className="muted">
                    Assumptions: {r.assumptions.join("; ") || "None recorded"}
                  </p>
                </div>
              </div>
              <details className="original-evidence">
                <summary>Original source statement</summary>
                <blockquote>{r.original_text}</blockquote>
                <small>{r.source_id}</small>
              </details>
              {role === "ba" && (
                <>
                  <button
                    className="text-button edit-link"
                    onClick={() => setEditing(true)}
                  >
                    Edit statement and acceptance criteria
                    <ArrowUpRight size={14} />
                  </button>
                  <DecisionForm
                    disabled={busy}
                    title="Requirement decision"
                    onDecision={(decision, note) =>
                      mutate(
                        `/requirements/${r.id}/review`,
                        { decision, note },
                        "POST",
                        `Requirement ${decision}.`,
                      )
                    }
                  />
                </>
              )}
              <History records={r.history} />
            </>
          )}
        </div>
      )}
    </article>
  );
}
