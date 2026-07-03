import { afterEach, describe, expect, it, vi } from "vitest";

import { AppError } from "./errors";
import {
  constantDelay,
  defaultShouldRetry,
  exponentialBackoff,
  sleep,
  withRetry,
} from "./retry";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("exponentialBackoff", () => {
  it("returns baseMs for attempt 1", () => {
    const delay = exponentialBackoff(500, 3);
    expect(delay(1)).toBe(500);
  });

  it("increases by factor each attempt", () => {
    const delay = exponentialBackoff(500, 3);
    expect(delay(2)).toBe(1500);
    expect(delay(3)).toBe(4500);
  });

  it("uses defaults", () => {
    const delay = exponentialBackoff();
    expect(delay(1)).toBe(500);
    expect(delay(2)).toBe(1500);
  });
});

describe("constantDelay", () => {
  it("always returns the same value", () => {
    const delay = constantDelay(1000);
    expect(delay(1)).toBe(1000);
    expect(delay(5)).toBe(1000);
  });
});

describe("defaultShouldRetry", () => {
  it("returns true for network errors", () => {
    expect(defaultShouldRetry(new AppError("network", ""), 1)).toBe(true);
  });

  it("returns true for timeout", () => {
    expect(defaultShouldRetry(new AppError("timeout", ""), 1)).toBe(true);
  });

  it("returns true for server errors", () => {
    expect(defaultShouldRetry(new AppError("server", ""), 1)).toBe(true);
  });

  it("returns true for rate limited", () => {
    expect(defaultShouldRetry(new AppError("rate_limited", ""), 1)).toBe(true);
  });

  it("returns false for client errors", () => {
    expect(defaultShouldRetry(new AppError("not_found", ""), 1)).toBe(false);
  });

  it("returns false for cancelled", () => {
    expect(defaultShouldRetry(new AppError("cancelled", ""), 1)).toBe(false);
  });

  it("retries unknown errors once", () => {
    expect(defaultShouldRetry(new Error("generic"), 1)).toBe(true);
    expect(defaultShouldRetry(new Error("generic"), 2)).toBe(false);
  });
});

describe("sleep", () => {
  it("resolves true after the given time", async () => {
    vi.useFakeTimers();
    const promise = sleep(100);
    vi.advanceTimersByTime(100);
    await expect(promise).resolves.toBe(true);
    vi.useRealTimers();
  });

  it("resolves false when aborted", async () => {
    vi.useFakeTimers();
    const ctrl = new AbortController();
    const promise = sleep(1000, ctrl.signal);
    ctrl.abort();
    await expect(promise).resolves.toBe(false);
    vi.useRealTimers();
  });

  it("resolves false when signal already aborted", async () => {
    const ctrl = new AbortController();
    ctrl.abort();
    await expect(sleep(1000, ctrl.signal)).resolves.toBe(false);
  });
});

describe("withRetry", () => {
  it("returns the result of a successful operation", async () => {
    const result = await withRetry(() => Promise.resolve("ok"), { maxRetries: 2 });
    expect(result).toBe("ok");
  });

  it("retries on failure and eventually succeeds", async () => {
    let attempts = 0;
    const result = await withRetry(
      async () => {
        attempts += 1;
        if (attempts < 3) throw new AppError("server", "not yet", 500);
        return "ok";
      },
      { maxRetries: 3, delayFor: constantDelay(0) },
    );
    expect(result).toBe("ok");
    expect(attempts).toBe(3);
  });

  it("fails after exhausting retries", async () => {
    const fn = vi.fn().mockRejectedValue(new AppError("server", "always fails", 500));

    await expect(
      withRetry(fn, { maxRetries: 2, delayFor: constantDelay(0) }),
    ).rejects.toThrow("always fails");

    expect(fn).toHaveBeenCalledTimes(3);
  });

  it("does not retry non-retryable errors", async () => {
    const fn = vi.fn().mockRejectedValue(new AppError("not_found", "missing", 404));

    await expect(
      withRetry(fn, { maxRetries: 3, delayFor: constantDelay(0) }),
    ).rejects.toThrow("missing");

    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("passes the attempt number to the operation", async () => {
    const attempts: number[] = [];
    await withRetry(
      async (attempt) => {
        attempts.push(attempt);
        if (attempt < 2) throw new AppError("server", "", 500);
        return "ok";
      },
      { maxRetries: 2, delayFor: constantDelay(0) },
    );
    expect(attempts).toEqual([1, 2]);
  });

  it("stops retrying when signal aborts", async () => {
    const ctrl = new AbortController();
    const fn = vi.fn().mockRejectedValue(new AppError("server", "", 500));

    setTimeout(() => ctrl.abort(), 10);

    await expect(
      withRetry(fn, { maxRetries: 5, delayFor: constantDelay(1000), signal: ctrl.signal }),
    ).rejects.toThrow();
  });
});
