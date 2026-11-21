import { useWorkspace } from "./hooks/useWorkspace";
import { ProjectDialog } from "./components/ProjectDialog";
import { Login } from "./screens/Login";
import { Overview } from "./screens/Overview";
import { Gather } from "./screens/Gather";
import { Analyse } from "./screens/Analyse";
import { Compliance } from "./screens/Compliance";
import { Lifecycle } from "./screens/Lifecycle";
import { Documents } from "./screens/Documents";
import { roles, navigation } from "./config/workspace";
import { Badge, Brand, Empty, Panel } from "./components/ui";
import { Check, ChevronDown, LogOut, Plus, X } from "lucide-react";

export default function App() {
  const {
    session,
    loginRole,
    setLoginRole,
    projects,
    project,
    view,
    setView,
    busy,
    error,
    setError,
    success,
    createOpen,
    setCreateOpen,
    llmAvailable,
    formRevision,
    login,
    logout,
    selectProject,
    mutate,
    createProject,
    download,
  } = useWorkspace();
  if (!session)
    return (
      <Login
        loginRole={loginRole}
        setLoginRole={setLoginRole}
        busy={busy}
        error={error}
        login={login}
      />
    );
  const role = session.user.role;
  const roleInfo = roles.find((r) => r.id === role)!;
  const activeNav = navigation.find((n) => n.id === view)!;
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to project content
      </a>
      <aside className="sidebar">
        <Brand />
        <label className="project-select-label" htmlFor="project-select">
          Current project
        </label>
        <div className="project-select">
          <select
            id="project-select"
            value={project?.id || ""}
            onChange={(e) => selectProject(e.target.value)}
            disabled={busy || !projects.length}
          >
            {!project && (
              <option value="">
                {projects.length ? "Choose a project" : "No projects yet"}
              </option>
            )}
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <ChevronDown size={15} />
        </div>
        {role === "ba" && (
          <button className="new-project" onClick={() => setCreateOpen(true)}>
            <Plus size={15} /> New project
          </button>
        )}
        <nav aria-label="Project workflow">
          {navigation.map((item) => (
            <button
              key={item.id}
              className={view === item.id ? "active" : ""}
              aria-current={view === item.id ? "page" : undefined}
              onClick={() => setView(item.id)}
            >
              <item.icon size={19} />
              <span>{item.title}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="mode-note">
            <span className="status-dot" />
            <div>
              <strong>Local demo</strong>
              <small>
                {llmAvailable
                  ? "Model extraction available"
                  : "Rule-based analysis"}
              </small>
            </div>
          </div>
          <div className="user-row">
            <span className="avatar">{roleInfo.initials}</span>
            <div>
              <strong>{session.user.name}</strong>
            </div>
            <button
              className="icon-button"
              onClick={logout}
              title="Switch demo role"
              aria-label="Switch demo role"
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <main id="main-content">
          <div className="page-heading">
            <div>
              {project && (
                <p className="project-location">
                  {view === "overview" ? "Project overview" : project.name}
                </p>
              )}
              <h1>
                {view === "overview" && project
                  ? project.name
                  : activeNav.title}
              </h1>
            </div>
            {project?.synthetic && (
              <Badge tone="amber">Synthetic project</Badge>
            )}
          </div>
          {error && (
            <div className="alert error" role="alert">
              <span>{error}</span>
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {success && (
            <div className="alert success" role="status">
              <Check size={17} />
              <span>{success}</span>
            </div>
          )}
          {busy && (
            <div className="loading-bar" role="status" aria-label="Working" />
          )}
          <div
            aria-busy={busy}
            key={`${session.token}-${project?.id}-${formRevision}`}
          >
            {!project ? (
              <Panel>
                <Empty
                  title={
                    busy ? "Opening your workspace" : "Start with a project"
                  }
                >
                  {busy
                    ? "Loading project records…"
                    : "Create a project to gather software requirements and connect every decision to its source."}
                </Empty>
                {!busy && role === "ba" && (
                  <div className="center">
                    <button
                      className="button primary"
                      onClick={() => setCreateOpen(true)}
                    >
                      <Plus size={16} />
                      Create project
                    </button>
                  </div>
                )}
              </Panel>
            ) : (
              <>
                {view === "overview" && (
                  <Overview
                    project={project}
                    role={role}
                    setView={setView}
                    busy={busy}
                    error={error}
                    mutate={mutate}
                  />
                )}
                {view === "gather" && (
                  <Gather
                    project={project}
                    role={role}
                    busy={busy}
                    mutate={mutate}
                    llmAvailable={llmAvailable}
                  />
                )}
                {view === "analyse" && (
                  <Analyse
                    project={project}
                    role={role}
                    busy={busy}
                    mutate={mutate}
                  />
                )}
                {view === "compliance" && (
                  <Compliance
                    project={project}
                    role={role}
                    busy={busy}
                    mutate={mutate}
                  />
                )}
                {view === "sdlc" && (
                  <Lifecycle
                    key={project.id}
                    project={project}
                    role={role}
                    busy={busy}
                    mutate={mutate}
                  />
                )}
                {view === "export" && (
                  <Documents
                    project={project}
                    role={role}
                    busy={busy}
                    download={download}
                  />
                )}
              </>
            )}
          </div>
        </main>
      </div>
      {createOpen && (
        <ProjectDialog
          busy={busy}
          error={error}
          onSubmit={createProject}
          onClose={() => setCreateOpen(false)}
        />
      )}
    </div>
  );
}
