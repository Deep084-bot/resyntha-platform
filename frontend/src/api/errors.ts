/**
 * API error taxonomy.
 *
 * The HTTP client normalises every transport-level failure into an
 * {@link AppError} with a discriminating {@link ApiErrorKind}. The
 * rest of the application never sees a raw AxiosError; it switches
 * on `kind` to decide how to render a region.
 *
 * Keeping the shape stable means tests and components can do
 * `if (err.kind === "not_found") …` without sniffing status codes.
 */

export type ApiErrorKind =
  /** Offline, DNS, CORS, or other no-response transport error. */
  | "network"
  /** Request exceeded its timeout. */
  | "timeout"
  /** Caller aborted via AbortController. */
  | "cancelled"
  /** 401 — no valid credentials. */
  | "unauthorized"
  /** 403 — authenticated but not permitted. */
  | "forbidden"
  /** 404 — resource does not exist. */
  | "not_found"
  /** 400 / 422 — request payload rejected. */
  | "validation"
  /** 409 — conflict with current state. */
  | "conflict"
  /** 429 — too many requests. */
  | "rate_limited"
  /** 5xx — backend fault. */
  | "server"
  /** Anything else. */
  | "unknown";

/** A paginated list response from the API. */
export interface Page<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

/** A simple list response. */
export interface ListResponse<T> {
  items: T[];
}

/**
 * Application-level error thrown by every service.
 *
 * Constructed exclusively by the response interceptor in
 * `api/http.ts` so that service code can rely on a single error
 * shape.
 */
export class AppError extends Error {
  public readonly kind: ApiErrorKind;
  public readonly status?: number;
  public readonly details?: unknown;

  constructor(
    kind: ApiErrorKind,
    message: string,
    status?: number,
    details?: unknown,
  ) {
    super(message);
    this.name = "AppError";
    this.kind = kind;
    this.status = status;
    this.details = details;
  }

  /** True for any 4xx response. */
  get isClient(): boolean {
    return this.status !== undefined && this.status >= 400 && this.status < 500;
  }

  /** True for any 5xx response. */
  get isServer(): boolean {
    return this.status !== undefined && this.status >= 500;
  }

  /** True when the request can be safely retried. */
  get isRetryable(): boolean {
    return (
      this.kind === "network" ||
      this.kind === "timeout" ||
      this.kind === "server" ||
      this.kind === "rate_limited"
    );
  }

  /**
   * Render as a plain object — useful for structured logging and
   * error-boundary payloads.
   */
  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      kind: this.kind,
      message: this.message,
      status: this.status,
      details: this.details,
    };
  }
}

/**
 * Map an HTTP status code to a {@link ApiErrorKind}.
 *
 * Single place to express the status → kind mapping so the response
 * interceptor stays small.
 */
export function kindFromStatus(status: number | undefined): ApiErrorKind {
  if (status === undefined) return "unknown";
  if (status === 401) return "unauthorized";
  if (status === 403) return "forbidden";
  if (status === 404) return "not_found";
  if (status === 409) return "conflict";
  if (status === 429) return "rate_limited";
  if (status === 400 || status === 422) return "validation";
  if (status >= 500) return "server";
  if (status >= 400) return "unknown";
  return "unknown";
}

/**
 * Extract a human-readable error message from a backend error body.
 * Backend responses follow FastAPI's shape (`{ detail: ... }`), but we
 * tolerate a few other shapes defensively.
 */
export function extractMessage(payload: unknown, fallback: string): string {
  if (typeof payload === "string" && payload.trim().length > 0) return payload;
  if (payload && typeof payload === "object") {
    const obj = payload as Record<string, unknown>;
    if (typeof obj.detail === "string") return obj.detail;
    if (Array.isArray(obj.detail)) {
      // FastAPI 422 — flatten field errors.
      return obj.detail
        .map((d) => {
          if (d && typeof d === "object" && "msg" in d) {
            const msg = (d as { msg?: unknown }).msg;
            return typeof msg === "string" ? msg : JSON.stringify(d);
          }
          return JSON.stringify(d);
        })
        .join("; ");
    }
    if (typeof obj.message === "string") return obj.message;
  }
  return fallback;
}
