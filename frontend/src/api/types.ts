/**
 * Generic API types shared by services and hooks.
 *
 * Concrete DTOs (Investigation, Paper, …) live in `src/types/`.
 * This file holds shapes that are not domain-specific.
 */

import type { ApiErrorKind } from "./errors";

/**
 * The shape of a `cancel` event raised by Axios when the request
 * is aborted via AbortController. Exposed so tests can fabricate
 * cancelled responses.
 */
export interface CancelledResponse {
  __isCancel: true;
}

/**
 * Runtime check — is this an Axios cancellation?
 */
export function isCancelled(value: unknown): value is CancelledResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { __isCancel?: unknown }).__isCancel === true
  );
}

/** Structured log payload emitted by the HTTP client. */
export interface RequestLog {
  method: string;
  url: string;
  status?: number;
  durationMs: number;
  kind?: ApiErrorKind;
  message?: string;
}
