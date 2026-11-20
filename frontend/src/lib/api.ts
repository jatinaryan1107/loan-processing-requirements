/** Transport errors keep their HTTP status for session and concurrency handling. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function response(
  path: string,
  token?: string,
  options: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  let result: Response;
  try {
    result = await fetch(`/api${path}`, { ...options, headers });
  } catch {
    throw new ApiError(
      0,
      "The API is unavailable. Start the backend on port 8000, then try again.",
    );
  }
  if (!result.ok) {
    const error = await result.json().catch(() => null);
    const detail = Array.isArray(error?.detail)
      ? error.detail.map((item: { msg: string }) => item.msg).join("; ")
      : error?.detail;
    throw new ApiError(
      result.status,
      typeof detail === "string"
        ? detail
        : `Request failed (${result.status}).`,
    );
  }
  return result;
}

export async function request<T>(
  path: string,
  token?: string,
  options: RequestInit = {},
): Promise<T> {
  return (await response(path, token, options)).json() as Promise<T>;
}

/** Every write/export is tied to the revision the user actually reviewed. */
export function revisionHeader(updatedAt: string): HeadersInit {
  return { "If-Match": updatedAt };
}
