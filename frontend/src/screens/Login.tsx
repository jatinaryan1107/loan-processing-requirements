import {
  ArrowRight,
  Check,
  GitBranch,
  Loader2,
  MessageSquareText,
  ShieldCheck,
} from "lucide-react";
import type { Role } from "../types";
import { Badge, Brand } from "../components/ui";
import { roles } from "../config/workspace";

export function Login({
  loginRole,
  setLoginRole,
  busy,
  error,
  login,
}: {
  loginRole: Role;
  setLoginRole: (role: Role) => void;
  busy: boolean;
  error: string;
  login: (role: Role) => Promise<void>;
}) {
  return (
    <div className="login-shell">
      <div className="login-story">
        <Brand />
        <div>
          <span className="eyebrow light">REQUIREMENTS, WITH CONTEXT</span>
          <h1>
            Build the right
            <br />
            system from
            <br />
            <em>the first question.</em>
          </h1>
          <p>
            A shared workspace for defining loan-processing software, reviewing
            evidence and choosing a development lifecycle.
          </p>
          <div className="story-path">
            <span>
              <MessageSquareText />
              Gather
            </span>
            <i />
            <span>
              <ShieldCheck />
              Review
            </span>
            <i />
            <span>
              <GitBranch />
              Plan
            </span>
          </div>
        </div>
        <small>AI-Based Loan Processing Requirements Management</small>
      </div>
      <div className="login-form">
        <div className="login-form-inner">
          <Badge tone="teal">LOCAL DEMO</Badge>
          <h2>Your workspace awaits.</h2>
          <p>Choose a seeded role to explore its review responsibilities.</p>
          <div className="role-options">
            {roles.map((r) => (
              <button
                key={r.id}
                className={`role-option ${loginRole === r.id ? "selected" : ""}`}
                onClick={() => setLoginRole(r.id)}
                aria-pressed={loginRole === r.id}
              >
                <span className="avatar">{r.initials}</span>
                <span>
                  <strong>{r.name}</strong>
                  <small>{r.description}</small>
                </span>
                {loginRole === r.id && <Check size={18} />}
              </button>
            ))}
          </div>
          {error && (
            <div className="alert error" role="alert">
              {error}
            </div>
          )}
          <button
            className="button primary login-button"
            disabled={busy}
            onClick={() => login(loginRole)}
          >
            {busy ? (
              <Loader2 className="spin" size={18} />
            ) : (
              <>
                Open workspace <ArrowRight size={18} />
              </>
            )}
          </button>
          <p className="login-disclaimer">
            Demo identities have server-enforced permissions. This local login
            is for demonstration and is not production authentication. Use
            synthetic information only.
          </p>
        </div>
      </div>
    </div>
  );
}
