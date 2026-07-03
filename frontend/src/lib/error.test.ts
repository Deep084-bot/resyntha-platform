import { describe, expect, it } from "vitest";

import { AppError } from "@/api/errors";

import { errorMessage, isAppError } from "./error";

describe("errorMessage", () => {
  it("extracts message from Error instances", () => {
    expect(errorMessage(new Error("boom"))).toBe("boom");
  });

  it("returns string values directly", () => {
    expect(errorMessage("just a string")).toBe("just a string");
  });

  it("returns fallback for non-errors", () => {
    expect(errorMessage(42)).toBe("Unexpected error");
    expect(errorMessage(null)).toBe("Unexpected error");
    expect(errorMessage(undefined)).toBe("Unexpected error");
    expect(errorMessage({})).toBe("Unexpected error");
  });

  it("uses custom fallback", () => {
    expect(errorMessage(42, "custom")).toBe("custom");
  });
});

describe("isAppError", () => {
  it("returns true for AppError instances", () => {
    expect(isAppError(new AppError("not_found", "missing", 404))).toBe(true);
  });

  it("returns false for regular Errors", () => {
    expect(isAppError(new Error("regular"))).toBe(false);
  });

  it("returns false for non-errors", () => {
    expect(isAppError("string")).toBe(false);
    expect(isAppError(null)).toBe(false);
    expect(isAppError(undefined)).toBe(false);
  });

  it("returns false for Error-like objects without name", () => {
    expect(isAppError({ message: "test" })).toBe(false);
  });
});
