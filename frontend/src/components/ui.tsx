import { useState } from "react";
import type { ReactNode } from "react";
import { Check, CircleHelp, Layers3 } from "lucide-react";
import { formatDate, label } from "../lib/format";

export function Badge({
  children,
  tone = "",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <Layers3 size={30} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Notice({ children }: { children: ReactNode }) {
  return (
    <div className="notice">
      <CircleHelp size={17} />
      <div>{children}</div>
    </div>
  );
}
export function Panel({
  title,
  description,
  action,
  children,
  className = "",
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {title && (
        <div className="panel-heading">
          <div>
            <h2>{title}</h2>
            {description && <p>{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
export function History({ records }: { records: Record<string, unknown>[] }) {
  return (
    records.length > 0 && (
      <details className="history">
        <summary>Decision history · {records.length}</summary>
        {[...records]
          .reverse()
          .map(({ decision, actor, at, note, ...evidence }, i) => (
            <div className="history-entry" key={i}>
              <strong>
                {typeof decision === "string" ? label(decision) : "Review"}
              </strong>
              <p>{String(note ?? "")}</p>
              <small>
                {[actor, typeof at === "string" && formatDate(at)]
                  .filter(Boolean)
                  .join(" · ")}
              </small>
              {Object.keys(evidence).length > 0 && (
                <details>
                  <summary>Recorded details</summary>
                  <pre>{JSON.stringify(evidence, null, 2)}</pre>
                </details>
              )}
            </div>
          ))}
      </details>
    )
  );
}

export function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <Layers3 size={25} strokeWidth={1.7} />
      </span>
      <div>
        Loan Processing<small>REQUIREMENTS</small>
      </div>
    </div>
  );
}

export function DecisionForm({
  title,
  disabled,
  onDecision,
  approveDisabled = false,
  children,
}: {
  title: string;
  disabled: boolean;
  onDecision: (decision: string, note: string) => Promise<boolean>;
  approveDisabled?: boolean;
  children?: ReactNode;
}) {
  const [note, setNote] = useState("");
  return (
    <form
      className="decision-form"
      onSubmit={async (e) => {
        e.preventDefault();
        const button = (e.nativeEvent as SubmitEvent).submitter;
        if (!(button instanceof HTMLButtonElement) || button.disabled) return;
        const decision = button.value;
        if (await onDecision(decision, note)) setNote("");
      }}
    >
      <h4>{title}</h4>
      {children}
      <label>
        Review note
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          required
          minLength={3}
          maxLength={2000}
          placeholder="Record the evidence and reason for this decision"
        />
      </label>
      <div className="button-row">
        <button
          className="button primary small"
          type="submit"
          disabled={disabled || approveDisabled}
          value="approved"
        >
          <Check size={15} />
          Approve
        </button>
        <button
          className="button danger small"
          type="submit"
          disabled={disabled}
          value="rejected"
        >
          Reject
        </button>
      </div>
    </form>
  );
}
