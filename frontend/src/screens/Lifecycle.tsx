import { useEffect, useState } from "react";
import { ChevronDown, GitBranch, ShieldCheck } from "lucide-react";
import type { Factors, Project, Role, Mutate } from "../types";
import {
  Badge,
  Empty,
  Notice,
  Panel,
  History,
  DecisionForm,
} from "../components/ui";

const factorDefinitions: {
  key: keyof Factors;
  title: string;
  low: string;
  high: string;
}[] = [
  {
    key: "stability",
    title: "Requirement stability",
    low: "Uncertain",
    high: "Stable",
  },
  {
    key: "complexity",
    title: "Project complexity",
    low: "Simple",
    high: "Complex",
  },
  {
    key: "regulatory",
    title: "Regulatory criticality",
    low: "Low",
    high: "Critical",
  },
  { key: "security", title: "Security risk", low: "Low", high: "High" },
  {
    key: "stakeholders",
    title: "Stakeholder availability",
    low: "Limited",
    high: "Frequent",
  },
  {
    key: "change",
    title: "Expected change frequency",
    low: "Rare",
    high: "Frequent",
  },
  {
    key: "legacy",
    title: "Legacy dependencies",
    low: "Few",
    high: "Extensive",
  },
  {
    key: "testing",
    title: "Testing obligations",
    low: "Standard",
    high: "Formal",
  },
  {
    key: "cadence",
    title: "Delivery cadence",
    low: "Single release",
    high: "Continuous",
  },
];
export function Lifecycle({
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
  const [factors, setFactors] = useState<Factors>(
    project.sdlc?.factors || {
      stability: 3,
      complexity: 3,
      regulatory: 4,
      security: 4,
      stakeholders: 3,
      change: 3,
      legacy: 3,
      testing: 4,
      cadence: 3,
    },
  );
  const [selected, setSelected] = useState(
    project.sdlc?.selected_model || project.sdlc?.rankings[0]?.model || "",
  );
  useEffect(() => {
    if (project.sdlc) {
      setFactors(project.sdlc.factors);
      setSelected(
        project.sdlc.selected_model || project.sdlc.rankings[0]?.model || "",
      );
    }
  }, [project.sdlc]);
  return (
    <>
      <div className="lifecycle-grid">
        <Panel
          title="Project characteristics"
          description="Set each factor from 1 to 5. The engine shows how every choice affects the ranking."
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              mutate(
                "/sdlc",
                { factors },
                "POST",
                "Lifecycle rankings updated. Review the rationale before selecting a model.",
              );
            }}
          >
            <div className="factor-list">
              {factorDefinitions.map((f) => (
                <label className="factor" key={f.key}>
                  <span>
                    {f.title}
                    <strong>{factors[f.key]}</strong>
                  </span>
                  <input
                    aria-label={f.title}
                    type="range"
                    min={1}
                    max={5}
                    step={1}
                    value={factors[f.key]}
                    disabled={role !== "pm" || busy}
                    onChange={(e) =>
                      setFactors({
                        ...factors,
                        [f.key]: Number(e.target.value),
                      })
                    }
                  />
                  <small>
                    <span>1 · {f.low}</span>
                    <span>5 · {f.high}</span>
                  </small>
                </label>
              ))}
            </div>
            {role === "pm" ? (
              <button className="button primary full-width" disabled={busy}>
                <GitBranch size={16} />
                Rank lifecycle models
              </button>
            ) : (
              <p className="muted">
                A Project Manager sets the factors and approves the lifecycle.
              </p>
            )}
          </form>
        </Panel>
        <div>
          <Panel
            title="Ranked recommendations"
            description="Weighted rule scores, not probabilities or claims of suitability."
          >
            {project.sdlc ? (
              <>
                <div className="rankings">
                  {project.sdlc.rankings.map((ranking, i) => (
                    <details
                      className={`ranking ${i === 0 ? "top-ranked" : ""}`}
                      key={ranking.model}
                    >
                      <summary>
                        <span className="ranking-number">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <div>
                          <strong>{ranking.model}</strong>
                          <div className="score-track">
                            <span
                              style={{
                                width: `${Math.max(0, Math.min(100, (ranking.score / ranking.max_score) * 100))}%`,
                              }}
                            />
                          </div>
                        </div>
                        <span className="score">
                          {ranking.score}
                          <small> / {ranking.max_score}</small>
                        </span>
                        <ChevronDown size={15} />
                      </summary>
                      <ul>
                        {ranking.rationale.map((reason, index) => (
                          <li key={index}>{reason}</li>
                        ))}
                      </ul>
                    </details>
                  ))}
                </div>
                <Notice>{project.sdlc.uncertainty}</Notice>
              </>
            ) : (
              <Empty title="No recommendation yet">
                A Project Manager can set the project factors and run the
                deterministic scoring engine.
              </Empty>
            )}
          </Panel>
          {project.sdlc && (
            <Panel
              title="Lifecycle decision"
              action={
                <Badge
                  tone={project.sdlc.status === "approved" ? "teal" : "neutral"}
                >
                  {project.sdlc.status}
                </Badge>
              }
            >
              {role === "pm" ? (
                <DecisionForm
                  title="Project Manager approval"
                  disabled={busy}
                  onDecision={(decision, note) =>
                    mutate(
                      "/sdlc/decision",
                      { model: selected, decision, note },
                      "POST",
                      `Lifecycle selection ${decision}.`,
                    )
                  }
                >
                  <label>
                    Selected model
                    <select
                      value={selected}
                      onChange={(e) => setSelected(e.target.value)}
                      required
                    >
                      {project.sdlc.rankings.map((r) => (
                        <option key={r.model}>{r.model}</option>
                      ))}
                    </select>
                  </label>
                </DecisionForm>
              ) : (
                <p>
                  {project.sdlc.selected_model ||
                    "Awaiting Project Manager selection."}
                </p>
              )}
              <History records={project.sdlc.history} />
            </Panel>
          )}
        </div>
      </div>
      {project.sdlc && project.sdlc.workflow.length > 0 && (
        <Panel
          title="Your project delivery workflow"
          description={`${project.sdlc.selected_model || project.sdlc.rankings[0]?.model} · Roles, outputs and approval gates`}
        >
          <div className="workflow">
            {project.sdlc.workflow.map((phase, i) => (
              <div className="workflow-phase" key={`${phase.phase}-${i}`}>
                <span className="phase-number">{i + 1}</span>
                <div>
                  <h3>{phase.phase}</h3>
                  <div className="phase-grid">
                    <div>
                      <h4>Activities</h4>
                      <ul>
                        {phase.activities.map((v, n) => (
                          <li key={n}>{v}</li>
                        ))}
                      </ul>
                      <p>
                        <strong>Roles:</strong> {phase.roles.join(", ")}
                      </p>
                    </div>
                    <div>
                      <h4>Deliverables</h4>
                      <ul>
                        {phase.deliverables.map((v, n) => (
                          <li key={n}>{v}</li>
                        ))}
                      </ul>
                      <p>
                        <strong>Security checkpoint:</strong>{" "}
                        {phase.security_checkpoint}
                      </p>
                    </div>
                  </div>
                  <div className="phase-gate">
                    <ShieldCheck size={15} />
                    <strong>Approval gate:</strong> {phase.approval_gate}
                  </div>
                  <div className="phase-boundaries">
                    <span>
                      <strong>Entry:</strong> {phase.entry}
                    </span>
                    <span>
                      <strong>Exit:</strong> {phase.exit}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </>
  );
}
