import {
  ArrowDownToLine,
  Check,
  CheckCheck,
  Clock3,
  FileCheck2,
} from "lucide-react";
import type { Project, Role } from "../types";
import { formatDate, label } from "../lib/format";
import { Badge, Empty, Notice, Panel } from "../components/ui";
import { roles } from "../config/workspace";

export function Documents({
  project,
  role,
  busy,
  download,
}: {
  project: Project;
  role: Role;
  busy: boolean;
  download: (format: "markdown" | "json", final: boolean) => Promise<void>;
}) {
  return (
    <>
      <div className="two-columns">
        <Panel
          title="Project documentation"
          description="One connected package with the source and review state of every requirement."
        >
          <div className="document-preview">
            <span className="document-icon">
              <FileCheck2 size={32} />
            </span>
            <div>
              <h3>{project.name}</h3>
              <p>Software Requirements Specification</p>
              <small>Generated from the current project record</small>
            </div>
          </div>
          <ul className="export-contents">
            {[
              "SRS and requirement register",
              "Acceptance criteria and user stories",
              "Use cases and traceability matrix",
              "Compliance mappings and source evidence",
              "SDLC plan and approval gates",
              "Risk, assumptions and open issues",
              "Agent runs and decision audit trail",
            ].map((item) => (
              <li key={item}>
                <Check size={14} />
                {item}
              </li>
            ))}
          </ul>
          <div className="button-row">
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => download("markdown", false)}
            >
              <ArrowDownToLine size={16} />
              Draft Markdown
            </button>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => download("json", false)}
            >
              <ArrowDownToLine size={16} />
              Draft JSON
            </button>
          </div>
          {role === "developer" && (
            <p className="muted">
              Developer exports contain approved requirements only.
            </p>
          )}
        </Panel>
        <Panel
          title="Approval readiness"
          description="Final exports are gated by the server, using the current review state."
          action={
            <Badge tone={project.final_ready ? "teal" : "amber"}>
              {project.final_ready ? "Ready" : "In review"}
            </Badge>
          }
        >
          {project.final_ready ? (
            <div className="ready-state">
              <CheckCheck size={35} />
              <h3>Review gates are complete</h3>
              <p>A Project Manager can export the approved project baseline.</p>
            </div>
          ) : (
            <div className="blocker-list">
              {project.final_blockers.length ? (
                project.final_blockers.map((blocker, i) => (
                  <div key={i}>
                    <Clock3 size={16} />
                    <span>{blocker}</span>
                  </div>
                ))
              ) : (
                <p>
                  Complete the requirement, compliance and lifecycle reviews.
                </p>
              )}
            </div>
          )}
          <div className="button-row">
            <button
              className="button primary"
              disabled={busy || role !== "pm" || !project.final_ready}
              onClick={() => download("markdown", true)}
            >
              <ArrowDownToLine size={16} />
              Approved Markdown
            </button>
            <button
              className="button secondary"
              disabled={busy || role !== "pm" || !project.final_ready}
              onClick={() => download("json", true)}
            >
              JSON
            </button>
          </div>
          {role !== "pm" && (
            <p className="muted">
              Final approved exports are available to the Project Manager.
            </p>
          )}
          <Notice>
            An approved baseline records the team’s decisions. It is not a legal
            certification or production-readiness assessment.
          </Notice>
        </Panel>
      </div>
      <Panel
        title="Agent execution records"
        description="Inspect the rules, inputs and evidence behind generated outputs."
        action={<Badge>{project.runs.length} runs</Badge>}
      >
        {project.runs.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Agent / version</th>
                  <th>Outcome</th>
                  <th>Provider</th>
                  <th>Evidence</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {project.runs
                  .slice()
                  .reverse()
                  .map((run) => (
                    <tr key={run.id}>
                      <td>
                        <strong>{run.agent}</strong>
                        <small>{run.version}</small>
                      </td>
                      <td>
                        {run.outcome}
                        <small>
                          Confidence: {Math.round(run.confidence * 100)}%
                        </small>
                      </td>
                      <td>{run.provider}</td>
                      <td>
                        <details>
                          <summary>
                            {run.input_ids.length} inputs ·{" "}
                            {run.evidence.length} evidence records
                          </summary>
                          <p className="mono">{run.input_ids.join(", ")}</p>
                          <ul>
                            {run.evidence.map((e, i) => (
                              <li key={i}>{e}</li>
                            ))}
                          </ul>
                        </details>
                      </td>
                      <td>{formatDate(run.at)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty title="No agent runs yet">
            Run an analysis, compliance verification or lifecycle recommendation
            to inspect its execution record.
          </Empty>
        )}
      </Panel>
      <Panel
        title="Decision audit trail"
        description="Source changes, reviews and exports are recorded with their actor and time."
        action={<Badge>{project.audit.length} events</Badge>}
      >
        {project.audit.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Actor</th>
                  <th>Details</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {project.audit
                  .slice()
                  .reverse()
                  .map((event) => (
                    <tr key={event.id}>
                      <td>
                        <strong>{label(event.action)}</strong>
                        <small className="mono">{event.id}</small>
                      </td>
                      <td>
                        {event.actor}
                        <small>
                          {roles.find((r) => r.id === event.role)?.name ||
                            event.role}
                        </small>
                      </td>
                      <td>
                        <details>
                          <summary>View event</summary>
                          <pre>
                            {typeof event.details === "string"
                              ? event.details
                              : JSON.stringify(event.details, null, 2)}
                          </pre>
                        </details>
                      </td>
                      <td>{formatDate(event.at)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">No audit records are available to this role.</p>
        )}
      </Panel>
    </>
  );
}
