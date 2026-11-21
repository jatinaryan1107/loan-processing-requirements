import { useState } from "react";
import { ArrowRight, ChevronRight } from "lucide-react";
import { ProjectDialog } from "../components/ProjectDialog";
import { Panel } from "../components/ui";
import { formatDate, label } from "../lib/format";
import type { Mutate, Project, Role, View } from "../types";

export function Overview({
  project,
  role,
  setView,
  busy,
  error,
  mutate,
}: {
  project: Project;
  role: Role;
  busy: boolean;
  error: string;
  mutate: Mutate;
  setView: (view: View) => void;
}) {
  const [editing, setEditing] = useState(false);
  const approved = project.requirements.filter(
    (r) => r.status === "approved",
  ).length;
  const open = project.questions.filter((q) => q.status === "open").length;
  const drafts = project.requirements.filter(
    (r) => r.status === "draft",
  ).length;
  const reviewed = project.mappings.filter((m) =>
    ["approved", "rejected"].includes(m.status),
  ).length;
  const sections: { view: View; title: string; detail: string }[] = [];
  if (role !== "developer") {
    sections.push({
      view: "gather",
      title: "Source documents and notes",
      detail: `${project.sources.length} captured`,
    });
  }
  sections.push(
    {
      view: "analyse",
      title: "Requirement register",
      detail:
        role === "developer"
          ? `${approved} approved`
          : `${approved} approved · ${drafts} awaiting review`,
    },
    {
      view: "compliance",
      title: "Compliance mappings",
      detail:
        role === "developer"
          ? `${reviewed} approved`
          : `${reviewed} of ${project.mappings.length} reviewed`,
    },
    {
      view: "sdlc",
      title: "Development lifecycle",
      detail: project.sdlc
        ? `${project.sdlc.selected_model} · ${label(project.sdlc.status)}`
        : "No selection yet",
    },
    {
      view: "export",
      title: "Requirements specification",
      detail: project.final_ready ? "Ready for final export" : "Draft",
    },
  );

  return (
    <>
      <section className="project-context" aria-label="Project context">
        {project.description && <p>{project.description}</p>}
        <div className="context-meta">
          <span>
            Jurisdiction <strong>{project.jurisdiction}</strong>
          </span>
          {role === "ba" && (
            <button
              className="text-button"
              disabled={busy}
              onClick={() => setEditing(true)}
            >
              Edit project details
            </button>
          )}
        </div>
      </section>
      {editing && (
        <ProjectDialog
          project={project}
          busy={busy}
          error={error}
          onClose={() => setEditing(false)}
          onSubmit={async (event) => {
            event.preventDefault();
            const fields = Object.fromEntries(
              new FormData(event.currentTarget),
            );
            if (
              await mutate(
                "/context",
                fields,
                "PUT",
                "Project details updated.",
              )
            )
              setEditing(false);
          }}
        />
      )}
      <div className="overview-columns">
        <Panel title="Project records">
          <ul className="record-list">
            {sections.map((section) => (
              <li key={section.view}>
                <button onClick={() => setView(section.view)}>
                  <span>
                    <strong>{section.title}</strong>
                    <small>{section.detail}</small>
                  </span>
                  <ChevronRight size={17} aria-hidden="true" />
                </button>
              </li>
            ))}
          </ul>
        </Panel>
        {role !== "developer" && (
          <div>
            <Panel
              title="Analysis findings"
              action={
                <button
                  className="text-button"
                  onClick={() => setView("analyse")}
                >
                  Review <ArrowRight size={14} />
                </button>
              }
            >
              <dl className="review-totals">
                <div>
                  <dt>Quality findings</dt>
                  <dd>{project.flags.length}</dd>
                </div>
                <div>
                  <dt>Open questions</dt>
                  <dd>{open}</dd>
                </div>
              </dl>
            </Panel>
            <Panel
              title="Recent activity"
              action={
                <button
                  className="text-button"
                  onClick={() => setView("export")}
                >
                  View audit <ArrowRight size={14} />
                </button>
              }
            >
              {project.audit.length ? (
                <ol className="audit-feed">
                  {project.audit
                    .slice(-3)
                    .reverse()
                    .map((item) => (
                      <li key={item.id}>
                        <strong>{label(item.action)}</strong>
                        <span>{item.actor}</span>
                        <time dateTime={item.at}>{formatDate(item.at)}</time>
                      </li>
                    ))}
                </ol>
              ) : (
                <p className="muted">No activity recorded.</p>
              )}
            </Panel>
          </div>
        )}
      </div>
    </>
  );
}
