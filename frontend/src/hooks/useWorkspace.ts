import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import type {
  Mutate,
  Project,
  ProjectSummary,
  Role,
  Session,
  View,
} from "../types";
import { ApiError, request, response, revisionHeader } from "../lib/api";
import {
  readProject,
  readSession,
  saveProject,
  saveSession,
} from "../lib/session";

function summary(project: Project): ProjectSummary {
  return {
    id: project.id,
    name: project.name,
    description: project.description,
    jurisdiction: project.jurisdiction,
    synthetic: project.synthetic,
    created_at: project.created_at,
    requirement_count: project.requirements.length,
    approved_count: project.requirements.filter((r) => r.status === "approved")
      .length,
  };
}

/** Coordinates remote state without allowing responses from an old identity to leak into a new one. */
export function useWorkspace() {
  const [session, setSession] = useState<Session | null>(readSession);
  const [loginRole, setLoginRole] = useState<Role>("ba");
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [view, setView] = useState<View>("overview");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [llmAvailable, setLlmAvailable] = useState(false);
  const [formRevision, setFormRevision] = useState(0);
  const operation = useRef(0);
  const token = session?.token;

  const clearSession = useCallback((message = "") => {
    operation.current++;
    saveSession(null);
    setSession(null);
    setProject(null);
    setProjects([]);
    setCreateOpen(false);
    setLlmAvailable(false);
    setBusy(false);
    setError(message);
    setSuccess("");
  }, []);

  const replaceProject = useCallback((updated: Project) => {
    setProject(updated);
    setProjects((current) =>
      current.map((p) => (p.id === updated.id ? summary(updated) : p)),
    );
  }, []);

  const handleError = useCallback(
    async (failure: unknown, ticket: number, projectId?: string) => {
      if (operation.current !== ticket) return;
      if (failure instanceof ApiError && failure.status === 401) {
        clearSession("Your demo session expired. Choose a role to continue.");
        return;
      }
      const message =
        failure instanceof Error
          ? failure.message
          : "The request failed. Please try again.";
      if (
        failure instanceof ApiError &&
        failure.status === 409 &&
        projectId &&
        token
      ) {
        // Unmount editor state before refetching, even if that refetch subsequently fails.
        setProject(null);
        setFormRevision((revision) => revision + 1);
        try {
          const latest = await request<Project>(
            `/projects/${projectId}`,
            token,
          );
          if (operation.current !== ticket) return;
          replaceProject(latest);
          setError(
            `${message} The latest project has been loaded and unsaved edits cleared. Review the current values before retrying.`,
          );
        } catch (refreshError) {
          if (operation.current !== ticket) return;
          if (refreshError instanceof ApiError && refreshError.status === 401) {
            clearSession(
              "Your demo session expired. Choose a role to continue.",
            );
          } else {
            setError(
              `${message} Refresh failed. Select the project again to continue; the stale editor has been cleared.`,
            );
          }
        }
        return;
      }
      setError(message);
    },
    [clearSession, replaceProject, token],
  );

  const load = useCallback(
    async (selected: string | undefined, ticket: number) => {
      if (!token) return;
      const list = await request<ProjectSummary[]>("/projects", token);
      const id =
        selected && list.some((p) => p.id === selected)
          ? selected
          : list[0]?.id;
      const loaded = id
        ? await request<Project>(`/projects/${id}`, token)
        : null;
      if (operation.current !== ticket) return;
      setProjects(list);
      setProject(loaded);
      if (id) saveProject(id);
    },
    [token],
  );

  useEffect(() => {
    if (!token) return;
    const ticket = ++operation.current;
    let active = true;
    setBusy(true);
    load(readProject(), ticket)
      .catch((failure) => {
        if (active) return handleError(failure, ticket);
      })
      .finally(() => {
        if (active && operation.current === ticket) setBusy(false);
      });
    request<{ llm_available: boolean }>("/health")
      .then((health) => {
        if (active) setLlmAvailable(health.llm_available);
      })
      .catch(() => {});
    return () => {
      active = false;
      if (operation.current === ticket) operation.current++;
    };
  }, [handleError, load, token]);

  useEffect(() => {
    if (!success) return;
    const timeout = setTimeout(() => setSuccess(""), 5000);
    return () => clearTimeout(timeout);
  }, [success]);

  function begin() {
    const ticket = ++operation.current;
    setBusy(true);
    setError("");
    setSuccess("");
    return ticket;
  }
  function finish(ticket: number) {
    if (operation.current === ticket) setBusy(false);
  }

  async function login(nextRole: Role) {
    const ticket = begin();
    try {
      const next = await request<Session>("/session", undefined, {
        method: "POST",
        body: JSON.stringify({ role: nextRole }),
      });
      if (operation.current !== ticket) return;
      saveSession(next);
      setSession(next);
      setProject(null);
      setView("overview");
    } catch (failure) {
      await handleError(failure, ticket);
    } finally {
      finish(ticket);
    }
  }

  async function logout() {
    const formerToken = token;
    clearSession();
    const ticket = operation.current;
    // Prevent a second login until revocation finishes, avoiding an unreported retained token.
    setBusy(true);
    try {
      if (formerToken)
        await request<{ ok: boolean }>("/session", formerToken, {
          method: "DELETE",
        });
    } catch (failure) {
      if (
        operation.current === ticket &&
        !(failure instanceof ApiError && failure.status === 401)
      ) {
        setError(
          "You are signed out locally, but the server could not confirm session revocation. The former token may remain valid until expiry.",
        );
      }
    } finally {
      finish(ticket);
    }
  }

  async function selectProject(id: string) {
    if (!id) return;
    const ticket = begin();
    setProject(null);
    try {
      await load(id, ticket);
      if (operation.current === ticket) setView("overview");
    } catch (failure) {
      await handleError(failure, ticket);
    } finally {
      finish(ticket);
    }
  }

  const mutate: Mutate = async (
    path,
    data = {},
    method = "POST",
    message = "Changes saved.",
  ) => {
    if (!project || !token) return false;
    const ticket = begin();
    try {
      const updated = await request<Project>(
        `/projects/${project.id}${path}`,
        token,
        {
          method,
          headers: revisionHeader(project.updated_at),
          body: data instanceof FormData ? data : JSON.stringify(data),
        },
      );
      if (operation.current !== ticket) return false;
      replaceProject(updated);
      setSuccess(message);
      return true;
    } catch (failure) {
      await handleError(failure, ticket, project.id);
      return false;
    } finally {
      finish(ticket);
    }
  };

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const ticket = begin();
    try {
      const created = await request<Project>("/projects", token, {
        method: "POST",
        body: JSON.stringify({
          name: form.get("name"),
          description: form.get("description"),
          jurisdiction: form.get("jurisdiction"),
        }),
      });
      if (operation.current !== ticket) return;
      setProject(created);
      saveProject(created.id);
      setProjects((current) => [summary(created), ...current]);
      setCreateOpen(false);
      setView("gather");
      setSuccess("Project created. Add your first source.");
    } catch (failure) {
      await handleError(failure, ticket);
    } finally {
      finish(ticket);
    }
  }

  async function download(format: "markdown" | "json", final: boolean) {
    if (!project) return;
    const ticket = begin();
    try {
      const result = await response(
        `/projects/${project.id}/export?format=${format}&final=${final}`,
        token,
        { headers: revisionHeader(project.updated_at) },
      );
      const blob = await result.blob();
      if (operation.current !== ticket) return;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${project.name.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}-${final ? "approved" : "draft"}.${format === "json" ? "json" : "md"}`;
      anchor.click();
      URL.revokeObjectURL(url);
      const updated = await request<Project>(`/projects/${project.id}`, token);
      if (operation.current !== ticket) return;
      replaceProject(updated);
      setSuccess(`${final ? "Approved" : "Draft"} documentation downloaded.`);
    } catch (failure) {
      await handleError(failure, ticket, project.id);
    } finally {
      finish(ticket);
    }
  }

  return {
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
  };
}
