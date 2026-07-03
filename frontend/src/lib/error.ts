/**
 * Error utilities.
 *
 * Re-exports from `@/api/errors` for callers that want a stable
 * "lib" surface for utilities while still using the canonical
 * error model.
 */

export { AppError, extractMessage, kindFromStatus, type ApiErrorKind } from "@/api/errors";

/** Coerce an unknown thrown value into a printable string. */
export function errorMessage(err: unknown, fallback = "Unexpected error"): string {
  if (err instanceof Error && err.message) return err.message;
  if (typeof err === "string") return err;
  return fallback;
}

/** Type-narrowing predicate: is `err` an AppError? */
export function isAppError(err: unknown): err is import("@/api/errors").AppError {
  return err instanceof Error && err.name === "AppError";
}
