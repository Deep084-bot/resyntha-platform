import { describe, expect, it } from "vitest";

import { AppError, extractMessage, kindFromStatus } from "./errors";

describe("AppError", () => {
  it("constructs with kind and message", () => {
    const err = new AppError("not_found", "Investigation not found", 404);
    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe("AppError");
    expect(err.kind).toBe("not_found");
    expect(err.message).toBe("Investigation not found");
    expect(err.status).toBe(404);
  });

  it("defaults to undefined status and details", () => {
    const err = new AppError("network", "offline");
    expect(err.status).toBeUndefined();
    expect(err.details).toBeUndefined();
  });

  describe("isClient", () => {
    it("returns true for 4xx", () => {
      expect(new AppError("not_found", "", 404).isClient).toBe(true);
      expect(new AppError("validation", "", 400).isClient).toBe(true);
    });

    it("returns false for 5xx", () => {
      expect(new AppError("server", "", 500).isClient).toBe(false);
    });

    it("returns false without status", () => {
      expect(new AppError("network", "").isClient).toBe(false);
    });
  });

  describe("isServer", () => {
    it("returns true for 5xx", () => {
      expect(new AppError("server", "", 500).isServer).toBe(true);
      expect(new AppError("server", "", 503).isServer).toBe(true);
    });

    it("returns false for 4xx", () => {
      expect(new AppError("not_found", "", 404).isServer).toBe(false);
    });
  });

  describe("isRetryable", () => {
    it("returns true for network errors", () => {
      expect(new AppError("network", "").isRetryable).toBe(true);
    });

    it("returns true for timeout", () => {
      expect(new AppError("timeout", "").isRetryable).toBe(true);
    });

    it("returns true for server errors", () => {
      expect(new AppError("server", "", 500).isRetryable).toBe(true);
    });

    it("returns true for rate limited", () => {
      expect(new AppError("rate_limited", "", 429).isRetryable).toBe(true);
    });

    it("returns false for client errors", () => {
      expect(new AppError("not_found", "", 404).isRetryable).toBe(false);
      expect(new AppError("validation", "", 422).isRetryable).toBe(false);
      expect(new AppError("unauthorized", "", 401).isRetryable).toBe(false);
    });

    it("returns false for cancelled", () => {
      expect(new AppError("cancelled", "").isRetryable).toBe(false);
    });
  });

  describe("toJSON", () => {
    it("returns plain object with all fields", () => {
      const err = new AppError("server", "boom", 500, { trace: "abc" });
      expect(err.toJSON()).toEqual({
        name: "AppError",
        kind: "server",
        message: "boom",
        status: 500,
        details: { trace: "abc" },
      });
    });
  });

  describe("error inheritance", () => {
    it("works with instanceof Error", () => {
      const err = new AppError("unknown", "test");
      expect(err instanceof Error).toBe(true);
    });

    it("has a stack trace", () => {
      const err = new AppError("unknown", "test");
      expect(typeof err.stack).toBe("string");
    });
  });
});

describe("kindFromStatus", () => {
  it("maps 401 to unauthorized", () => expect(kindFromStatus(401)).toBe("unauthorized"));
  it("maps 403 to forbidden", () => expect(kindFromStatus(403)).toBe("forbidden"));
  it("maps 404 to not_found", () => expect(kindFromStatus(404)).toBe("not_found"));
  it("maps 409 to conflict", () => expect(kindFromStatus(409)).toBe("conflict"));
  it("maps 429 to rate_limited", () => expect(kindFromStatus(429)).toBe("rate_limited"));
  it("maps 400 to validation", () => expect(kindFromStatus(400)).toBe("validation"));
  it("maps 422 to validation", () => expect(kindFromStatus(422)).toBe("validation"));
  it("maps 500 to server", () => expect(kindFromStatus(500)).toBe("server"));
  it("maps 503 to server", () => expect(kindFromStatus(503)).toBe("server"));
  it("maps 418 to unknown", () => expect(kindFromStatus(418)).toBe("unknown"));
  it("maps 200 to unknown", () => expect(kindFromStatus(200)).toBe("unknown"));
  it("maps undefined to unknown", () => expect(kindFromStatus(undefined)).toBe("unknown"));
});

describe("extractMessage", () => {
  it("returns a string payload directly", () => {
    expect(extractMessage("error occurred", "fallback")).toBe("error occurred");
  });

  it("does not trim whitespace from string payload", () => {
    expect(extractMessage("  error  ", "fallback")).toBe("  error  ");
  });

  it("returns fallback for empty string", () => {
    expect(extractMessage("", "fallback")).toBe("fallback");
  });

  it("extracts detail from object", () => {
    expect(extractMessage({ detail: "not found" }, "fallback")).toBe("not found");
  });

  it("extracts detail array with msg fields", () => {
    const payload = {
      detail: [
        { loc: ["body", "title"], msg: "field required", type: "value_error" },
      ],
    };
    expect(extractMessage(payload, "fallback")).toBe("field required");
  });

  it("joins multiple detail errors", () => {
    const payload = {
      detail: [
        { msg: "first error" },
        { msg: "second error" },
      ],
    };
    expect(extractMessage(payload, "fallback")).toBe("first error; second error");
  });

  it("extracts message key as fallback", () => {
    expect(extractMessage({ message: "something broke" }, "fallback")).toBe("something broke");
  });

  it("prefers detail over message", () => {
    expect(extractMessage({ detail: "detail error", message: "msg error" }, "fallback")).toBe("detail error");
  });

  it("returns fallback when nothing matches", () => {
    expect(extractMessage({ foo: "bar" }, "fallback")).toBe("fallback");
  });

  it("returns fallback for null", () => {
    expect(extractMessage(null, "fallback")).toBe("fallback");
  });

  it("returns fallback for undefined", () => {
    expect(extractMessage(undefined, "fallback")).toBe("fallback");
  });

  it("returns fallback for number", () => {
    expect(extractMessage(42, "fallback")).toBe("fallback");
  });
});
