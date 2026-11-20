import { useState } from "react";
import { CircleHelp, FileText, ShieldCheck } from "lucide-react";
import type { Mapping, Project, Role, Mutate } from "../types";
import { label } from "../lib/format";
import {
  Badge,
  Empty,
  Notice,
  Panel,
  History,
  DecisionForm,
} from "../components/ui";

export function Compliance({
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
  return (
    <>
      <Notice>
        All mappings are advisory. Only the local, versioned knowledge base is
        used. Synthetic demonstration policies are not regulations or evidence
        of legal compliance.
      </Notice>
      <div className="section-intro">
        <div>
          <h2>Controls and source evidence</h2>
          <p>
            {project.mappings.filter((m) => m.source).length} source-backed
            proposals · {project.mappings.filter((m) => !m.source).length}{" "}
            without verified sources
          </p>
        </div>
        {["ba", "compliance"].includes(role) && (
          <button
            className="button primary"
            disabled={busy}
            onClick={() =>
              mutate(
                "/compliance",
                {},
                "POST",
                "Compliance proposals refreshed. Review each mapping and its evidence.",
              )
            }
          >
            <ShieldCheck size={17} />
            Run verification
          </button>
        )}
      </div>
      {project.mappings.length ? (
        <div className="mapping-list">
          {project.mappings.map((mapping) => (
            <MappingCard
              key={mapping.id}
              mapping={mapping}
              role={role}
              busy={busy}
              mutate={mutate}
            />
          ))}
        </div>
      ) : (
        <Panel>
          <Empty title="No compliance mappings yet">
            Run verification after gathering requirements to review control
            coverage and missing source evidence.
          </Empty>
        </Panel>
      )}
    </>
  );
}
function MappingCard({
  mapping: m,
  role,
  busy,
  mutate,
}: {
  mapping: Mapping;
  role: Role;
  busy: boolean;
  mutate: Mutate;
}) {
  const [interpretation, setInterpretation] = useState(m.interpretation || "");
  return (
    <article className="panel mapping-card">
      <div className="mapping-heading">
        <span className={`mapping-icon ${m.source ? "" : "unknown"}`}>
          <ShieldCheck size={22} />
        </span>
        <div>
          <span className="mono">{m.id}</span>
          <h3>{label(m.control)}</h3>
        </div>
        <Badge
          tone={
            m.status === "approved"
              ? "teal"
              : m.status === "rejected"
                ? "rose"
                : m.source
                  ? "neutral"
                  : "amber"
          }
        >
          {m.status}
        </Badge>
      </div>
      <p>{m.reason}</p>
      <p className="muted">
        Requirements:{" "}
        <span className="mono">
          {m.requirement_ids.join(", ") || "Project-level control gap"}
        </span>
      </p>
      {m.source ? (
        <div className="policy-source">
          <div className="policy-title">
            <FileText size={17} />
            <strong>{m.source.title}</strong>
            {m.source.synthetic && <Badge tone="amber">Synthetic policy</Badge>}
          </div>
          <blockquote>{m.source.text}</blockquote>
          <dl className="source-metadata">
            <div>
              <dt>Clause</dt>
              <dd>{m.source.clause}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{m.source.version}</dd>
            </div>
            <div>
              <dt>Jurisdiction</dt>
              <dd>{m.source.jurisdiction}</dd>
            </div>
            <div>
              <dt>Effective date</dt>
              <dd>{m.source.effective_date}</dd>
            </div>
          </dl>
          <p>
            <strong>Applicability:</strong> {m.source.applicability}
          </p>
          <small className="mono">Source: {m.source.id}</small>
        </div>
      ) : (
        <div className="unknown-source">
          <CircleHelp size={20} />
          <div>
            <strong>
              No verified source available / requires compliance officer review.
            </strong>
            <p>
              An unsupported mapping cannot be approved as verified. Record a
              review decision and obtain an authorised source.
            </p>
          </div>
        </div>
      )}
      {m.interpretation && (
        <p>
          <strong>Interpretation:</strong> {m.interpretation}
        </p>
      )}
      {role === "compliance" && (
        <DecisionForm
          title="Compliance officer review"
          disabled={busy}
          approveDisabled={!m.source}
          onDecision={(decision, note) =>
            mutate(
              `/mappings/${m.id}/review`,
              {
                decision,
                note,
                ...(interpretation.trim() ? { interpretation } : {}),
              },
              "POST",
              `Compliance mapping ${decision}.`,
            )
          }
        >
          <label>
            Amended interpretation
            <textarea
              rows={2}
              value={interpretation}
              onChange={(e) => setInterpretation(e.target.value)}
              maxLength={3000}
              placeholder="Describe applicability and limitations of the cited clause."
            />
          </label>
        </DecisionForm>
      )}
      <History records={m.history} />
    </article>
  );
}
