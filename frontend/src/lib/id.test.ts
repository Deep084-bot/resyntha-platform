import { describe, expect, it } from "vitest";

import { isUuid, makeClientId, prefixedId, shortId } from "./id";

describe("isUuid", () => {
  it("returns true for valid UUIDs", () => {
    expect(isUuid("550e8400-e29b-41d4-a716-446655440000")).toBe(true);
    expect(isUuid("00000000-0000-0000-0000-000000000000")).toBe(true);
  });

  it("returns true for mixed case UUIDs", () => {
    expect(isUuid("550E8400-E29B-41D4-A716-446655440000")).toBe(true);
  });

  it("returns false for invalid strings", () => {
    expect(isUuid("not-a-uuid")).toBe(false);
    expect(isUuid("")).toBe(false);
    expect(isUuid("550e8400-e29b-41d4-a716")).toBe(false);
  });

  it("returns false for null and undefined", () => {
    expect(isUuid(null)).toBe(false);
    expect(isUuid(undefined)).toBe(false);
  });
});

describe("shortId", () => {
  it("returns first 8 characters by default", () => {
    expect(shortId("550e8400-e29b-41d4-a716-446655440000")).toBe("550e8400");
  });

  it("respects custom length", () => {
    expect(shortId("550e8400-e29b-41d4-a716-446655440000", 4)).toBe("550e");
  });

  it("handles empty string", () => {
    expect(shortId("")).toBe("");
  });
});

describe("prefixedId", () => {
  it("combines prefix and short ID", () => {
    const result = prefixedId("Investigation", "550e8400-e29b-41d4-a716-446655440000");
    expect(result).toBe("investigation_550e8400");
  });
});

describe("makeClientId", () => {
  it("returns a string with the default prefix", () => {
    const id = makeClientId();
    expect(id).toMatch(/^id_[0-9a-f]{16}$/);
  });

  it("uses a custom prefix", () => {
    const id = makeClientId("tmp");
    expect(id).toMatch(/^tmp_[0-9a-f]{16}$/);
  });

  it("generates unique IDs", () => {
    const ids = new Set(Array.from({ length: 100 }, () => makeClientId()));
    expect(ids.size).toBe(100);
  });
});
