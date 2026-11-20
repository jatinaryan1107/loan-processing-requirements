import { useEffect } from "react";
import type { FormEvent } from "react";
import type { Project } from "../types";
import { ArrowRight, X } from "lucide-react";
import { Notice } from "../components/ui";

export function ProjectDialog({
  project,
  busy,
  error,
  onSubmit,
  onClose,
}: {
  project?: Project;
  busy: boolean;
  error: string;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onClose: () => void;
}) {
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
      if (event.key !== "Tab") return;
      const elements = Array.from(
        document.querySelectorAll<HTMLElement>(
          ".modal button:not(:disabled), .modal input, .modal textarea, .modal select",
        ),
      );
      const first = elements[0];
      const last = elements.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    }
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("keydown", handleKey);
      previous?.focus();
    };
  }, []);
  return (
    <div
      className="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-project-title"
      >
        <div className="panel-heading">
          <h2 id="new-project-title">
            {project ? "Edit project details" : "Create a requirements project"}
          </h2>
          <button
            className="icon-button"
            aria-label="Close"
            onClick={() => onClose()}
          >
            <X />
          </button>
        </div>
        {error && (
          <div className="alert error" role="alert">
            {error}
          </div>
        )}
        <form onSubmit={onSubmit}>
          <label>
            Project name
            <input
              name="name"
              defaultValue={project?.name}
              required
              minLength={3}
              maxLength={120}
              placeholder="Loan servicing modernisation"
              autoFocus
            />
          </label>
          <label>
            Project context
            <textarea
              name="description"
              defaultValue={project?.description}
              rows={3}
              maxLength={4000}
              placeholder="Describe the software goals, users and boundaries."
            />
          </label>
          <label>
            Jurisdiction
            <input
              name="jurisdiction"
              required
              defaultValue={project?.jurisdiction ?? "India"}
              minLength={2}
              maxLength={100}
            />
          </label>
          <Notice>
            Jurisdiction is context for review. It does not supply verified
            regulatory sources.
          </Notice>
          <button className="button primary" disabled={busy}>
            {project ? "Save changes" : "Create project"}{" "}
            <ArrowRight size={16} />
          </button>
        </form>
      </section>
    </div>
  );
}
