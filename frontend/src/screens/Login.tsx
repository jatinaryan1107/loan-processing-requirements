import { ArrowRight, Check, Loader2 } from "lucide-react";
import type { Role } from "../types";
import { Brand } from "../components/ui";
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
    <div className="signin">
      <header className="signin-masthead">
        <Brand />
        <span>Local demo</span>
      </header>
      <main className="signin-layout">
        <div className="signin-intro">
          <h1>Loan processing requirements</h1>
          <p>
            Review stakeholder requirements, check policy evidence and select a
            development lifecycle for the proposed loan system.
          </p>
        </div>
        <section className="role-picker" aria-labelledby="role-title">
          <h2 id="role-title">Choose your role</h2>
          <div className="role-options">
            {roles.map((r) => (
              <button
                key={r.id}
                className={`role-option ${loginRole === r.id ? "selected" : ""}`}
                onClick={() => setLoginRole(r.id)}
                aria-pressed={loginRole === r.id}
              >
                <span className="avatar" aria-hidden="true">
                  {r.initials}
                </span>
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
          <p className="signin-note">
            Demo roles use synthetic data and require no password.
          </p>
        </section>
      </main>
    </div>
  );
}
