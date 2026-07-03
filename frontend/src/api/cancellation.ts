/**
 * Cancellation helpers built on the standard `AbortController`.
 *
 * React Query passes its own `signal` to every query, so most
 * callers never need this. These helpers exist for ad-hoc
 * cancellations (e.g. user clicks "Cancel" on a long copilot
 * request) and for composing multiple signals.
 */

/**
 * A tiny "abort bag" that wraps a controller with a stable handle.
 * Use {@link cancel} to abort, {@link signal} to pass to fetch/axios.
 */
export interface CancellationToken {
  readonly signal: AbortSignal;
  cancel: (reason?: unknown) => void;
  readonly aborted: boolean;
}

export function createCancellationToken(): CancellationToken {
  const controller = new AbortController();
  return {
    get signal() {
      return controller.signal;
    },
    cancel(reason?: unknown) {
      if (!controller.signal.aborted) controller.abort(reason);
    },
    get aborted() {
      return controller.signal.aborted;
    },
  };
}

/**
 * Compose multiple signals into a single one. The returned signal
 * aborts as soon as *any* of the inputs abort.
 */
export function combineSignals(signals: ReadonlyArray<AbortSignal>): AbortSignal {
  const controller = new AbortController();

  const onAbort = (event: Event) => {
    const target = event.target as AbortSignal | null;
    if (target) controller.abort(target.reason);
  };

  for (const s of signals) {
    if (s.aborted) {
      controller.abort(s.reason);
      break;
    }
    s.addEventListener("abort", onAbort, { once: true });
  }

  return controller.signal;
}

/**
 * Run a callback with an AbortSignal that auto-aborts after
 * `ms` milliseconds. Useful for "give up after N seconds" on top
 * of axios's own timeout.
 */
export function withTimeout(ms: number): { signal: AbortSignal; clear: () => void } {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(new Error("timeout")), ms);
  return {
    signal: controller.signal,
    clear: () => clearTimeout(id),
  };
}
