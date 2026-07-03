/**
 * Barrel for the API layer.
 *
 * Import everything the API layer exports from here so call sites
 * only need a single import:
 *
 *   import { api, AppError, withRetry } from "@/api";
 */

export { api, default, requestConfig } from "./http";
export {
  AppError,
  extractMessage,
  kindFromStatus,
  type ApiErrorKind,
  type Page,
  type ListResponse,
} from "./errors";
export {
  createCancellationToken,
  combineSignals,
  withTimeout,
  type CancellationToken,
} from "./cancellation";
export {
  withRetry,
  sleep,
  exponentialBackoff,
  constantDelay,
  defaultShouldRetry,
  type RetryOptions,
  type DelayFor,
  type ShouldRetry,
} from "./retry";
export { isCancelled, type CancelledResponse, type RequestLog } from "./types";
