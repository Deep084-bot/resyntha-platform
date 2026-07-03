/**
 * Retry policies for the API client and TanStack Query.
 *
 * The client-level retries are intentionally simple: they cover
 * the common "blip" cases without trying to be clever. Domain-level
 * retry logic (per-query, per-mutation) lives in the React Query
 * hooks and uses these helpers as the building blocks.
 */

import { AppError } from "./errors";

/** A predicate deciding whether an error is worth retrying. */
export type ShouldRetry = (err: unknown, attempt: number) => boolean;

/** Compute the delay (in ms) before attempt N. */
export type DelayFor = (attempt: number) => number;

export interface RetryOptions {
  /** Maximum number of retries (NOT counting the first attempt). */
  maxRetries: number;
  /** Backoff schedule. */
  delayFor?: DelayFor;
  /** Decide whether to retry a given error. */
  shouldRetry?: ShouldRetry;
  /** Optional abort signal — aborting cancels the sleep. */
  signal?: AbortSignal;
}

/** Exponential backoff: 500ms, 1500ms, 4500ms, … */
export const exponentialBackoff = (baseMs = 500, factor = 3): DelayFor => {
  return (attempt) => baseMs * Math.pow(factor, Math.max(0, attempt - 1));
};

/** Constant delay between retries. */
export const constantDelay = (ms: number): DelayFor => () => ms;

/** Default predicate: retry only on retryable error kinds. */
export const defaultShouldRetry: ShouldRetry = (err, attempt) => {
  if (err instanceof AppError) {
    return err.isRetryable;
  }
  // Unknown error shape — retry once, never blindly.
  return attempt <= 1;
};

/**
 * Sleep for `ms` milliseconds, or until `signal` aborts.
 * Resolves with `true` if slept fully, `false` if aborted.
 */
export async function sleep(ms: number, signal?: AbortSignal): Promise<boolean> {
  if (signal?.aborted) return false;
  return new Promise((resolve) => {
    const id = setTimeout(() => {
      cleanup();
      resolve(true);
    }, ms);
    const onAbort = () => {
      cleanup();
      resolve(false);
    };
    const cleanup = () => {
      clearTimeout(id);
      signal?.removeEventListener("abort", onAbort);
    };
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

/**
 * Execute `op` with retry. `op` is called with the 1-based attempt
 * number; if it throws a non-retryable error the loop exits early.
 */
export async function withRetry<T>(
  op: (attempt: number) => Promise<T>,
  options: RetryOptions,
): Promise<T> {
  const delay = options.delayFor ?? exponentialBackoff();
  const should = options.shouldRetry ?? defaultShouldRetry;

  let lastErr: unknown;
  for (let attempt = 1; attempt <= options.maxRetries + 1; attempt += 1) {
    try {
      return await op(attempt);
    } catch (err) {
      lastErr = err;
      const isLast = attempt > options.maxRetries;
      if (isLast || !should(err, attempt)) throw err;
      const ok = await sleep(delay(attempt), options.signal);
      if (!ok) throw err;
    }
  }
  // Unreachable, but keeps the type-checker happy.
  throw lastErr;
}
