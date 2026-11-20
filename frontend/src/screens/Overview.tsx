import type { ReactNode } from "react";
import { useState } from "react";
import { ProjectDialog } from "../components/ProjectDialog";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCheck,
  CircleHelp,
  ClipboardCheck,
  FileText,
  GitBranch,
  MessageSquareText,
  ShieldCheck,
} from "lucide-react";
import type { Mutate, Project, Role, View } from "../types";
import { formatDate, label } from "../lib/format";
import { Panel } from "../components/ui";
import { navigation } from "../config/workspace";

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
  const next: View =
    role === "compliance"
      ? "compliance"
      : role === "pm"
        ? "sdlc"
        : role === "developer"
          ? "analyse"
          : "gather";
  const stages = [
    {
      title: "Gather",
      caption: `${project.sources.length} source records`,
      done: project.sources.length > 0,
      view: "gather",
    },
    {
      title: "Validate",
      caption: `${approved} requirements approved`,
      done: approved > 0 && approved === project.requirements.length,
      view: "analyse",
    },
    {
      title: "Review evidence",
      caption: `${project.mappings.length} control mappings`,
      done:
        project.mappings.length > 0 &&
        project.mappings.every((m) =>
          ["approved", "rejected"].includes(m.status),
        ),
      view: "compliance",
    },
    {
      title: "Choose a lifecycle",
      caption: project.sdlc?.selected_model || "Selection pending",
      done: project.sdlc?.status === "approved",
      view: "sdlc",
    },
  ];
  return (
    <>
      <section className="overview-hero">
        <div>
          <div className="hero-kicker">
            <span className="status-dot" /> REQUIREMENTS ENGINEERING
          </div>
          <h2>{project.name}</h2>
          <p>
            {project.description ||
              "Define a loan-processing software system with traceable requirements, reviewed evidence and a justified delivery plan."}
          </p>
          <button className="button primary" onClick={() => setView(next)}>
            Continue to{" "}
            {navigation.find((n) => n.id === next)?.title.toLowerCase()}
            <ArrowRight size={17} />
          </button>
          {role === "ba" && (
            <button
              className="button"
              disabled={busy}
              onClick={() => setEditing(true)}
            >
              Edit project details
            </button>
          )}
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="art-orbit orbit-one" />
          <div className="art-orbit orbit-two" />
          <div className="art-node top">
            <MessageSquareText size={25} />
          </div>
          <div className="art-node middle">
            <ShieldCheck size={30} />
          </div>
          <div className="art-node bottom">
            <GitBranch size={25} />
          </div>
          <span className="art-dot dot-one" />
          <span className="art-dot dot-two" />
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
      <div className="stats-grid">
        <Stat
          label="Requirements"
          value={project.requirements.length}
          note="Original sources preserved"
          icon={<FileText />}
        />
        <Stat
          label="Approved"
          value={approved}
          note="Reviewed by a Business Analyst"
          icon={<CheckCheck />}
        />
        <Stat
          label="Quality findings"
          value={project.flags.length}
          note="Rule-based checks, not a quality score"
          icon={<ClipboardCheck />}
        />
        <Stat
          label="Open questions"
          value={open}
          note="Clarifications to work through"
          icon={<MessageSquareText />}
        />
      </div>
      <Panel
        title="Your path to a reviewed baseline"
        description="Each stage keeps its evidence and human decisions together."
      >
        <div className="stage-grid">
          {stages.map((stage, i) => (
            <button
              className={`stage ${stage.done ? "complete" : ""}`}
              key={stage.title}
              onClick={() => setView(stage.view as View)}
            >
              <span className="stage-number">
                {stage.done ? <Check size={18} /> : `0${i + 1}`}
              </span>
              <h3>{stage.title}</h3>
              <p>{stage.caption}</p>
              <ArrowUpRight size={16} />
            </button>
          ))}
        </div>
      </Panel>
      <div className="two-columns">
        <Panel
          title="Recent decisions"
          action={
            <button className="text-button" onClick={() => setView("export")}>
              View audit <ArrowRight size={14} />
            </button>
          }
        >
          {project.audit.length ? (
            <div className="activity-list">
              {project.audit
                .slice(-5)
                .reverse()
                .map((item) => (
                  <div className="activity" key={item.id}>
                    <span className="activity-dot" />
                    <div>
                      <strong>{label(item.action)}</strong>
                      <p>
                        {item.actor} · {formatDate(item.at)}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <p className="muted">
              Activity appears here as the project develops.
            </p>
          )}
        </Panel>
        <Panel title="Know what the system knows">
          <div className="assurance-row">
            <ShieldCheck size={21} />
            <div>
              <h3>Evidence is explicit</h3>
              <p>
                Policy mappings cite local, versioned source clauses. Missing
                evidence stays marked for review.
              </p>
            </div>
          </div>
          <div className="assurance-row">
            <GitBranch size={21} />
            <div>
              <h3>Recommendations are explainable</h3>
              <p>
                SDLC rankings use deterministic factors and scores. A Project
                Manager makes the selection.
              </p>
            </div>
          </div>
          <div className="assurance-row">
            <CircleHelp size={21} />
            <div>
              <h3>This is a software planning tool</h3>
              <p>
                It defines requirements. It does not process loans or make legal
                determinations.
              </p>
            </div>
          </div>
        </Panel>
      </div>
    </>
  );
}
function Stat({
  label: title,
  value,
  note,
  icon,
}: {
  label: string;
  value: number;
  note: string;
  icon: ReactNode;
}) {
  return (
    <div className="stat">
      <div>
        <span>{title}</span>
        {icon}
      </div>
      <strong>{value.toString().padStart(2, "0")}</strong>
      <small>{note}</small>
    </div>
  );
}
