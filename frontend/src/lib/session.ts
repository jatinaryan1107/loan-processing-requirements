import type { Session } from "../types";
import { roles } from "../config/workspace";

const SESSION_KEY = "lr-session";
const PROJECT_KEY = "lr-project";

export function readSession(): Session | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(SESSION_KEY) || "null");
    return value &&
      typeof value.token === "string" &&
      value.token.length > 0 &&
      typeof value.user?.name === "string" &&
      typeof value.user?.id === "string" &&
      roles.some((role) => role.id === value.user.role)
      ? (value as Session)
      : null;
  } catch {
    return null;
  }
}

export function saveSession(value: Session | null): void {
  try {
    if (value) sessionStorage.setItem(SESSION_KEY, JSON.stringify(value));
    else sessionStorage.removeItem(SESSION_KEY);
  } catch {
    /* The active in-memory session still works when storage is unavailable. */
  }
}

export function readProject(): string | undefined {
  try {
    return sessionStorage.getItem(PROJECT_KEY) || undefined;
  } catch {
    return undefined;
  }
}

export function saveProject(id: string): void {
  try {
    sessionStorage.setItem(PROJECT_KEY, id);
  } catch {
    /* Remembering the last project is optional. */
  }
}
