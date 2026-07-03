import { describe, expect, it } from "vitest";

import { buildQuery, mergeQuery, parseQuery, withQuery } from "./url";

describe("buildQuery", () => {
  it("builds a simple query string", () => {
    expect(buildQuery({ q: "ai", page: "2" })).toBe("q=ai&page=2");
  });

  it("skips null and undefined values", () => {
    expect(buildQuery({ q: "ai", empty: null, missing: undefined })).toBe("q=ai");
  });

  it("skips empty string values", () => {
    expect(buildQuery({ q: "" })).toBe("");
  });

  it("handles array values", () => {
    expect(buildQuery({ tags: ["a", "b"] })).toBe("tags=a&tags=b");
  });

  it("skips null/undefined items in arrays", () => {
    expect(buildQuery({ tags: ["a", null, "b", undefined] })).toBe("tags=a&tags=b");
  });

  it("percent-encodes special characters", () => {
    expect(buildQuery({ q: "deep learning" })).toBe("q=deep%20learning");
    expect(buildQuery({ url: "https://example.com" })).toBe("url=https%3A%2F%2Fexample.com");
  });

  it("supports boolean values", () => {
    expect(buildQuery({ active: true })).toBe("active=true");
  });

  it("supports numeric values", () => {
    expect(buildQuery({ page: 2 })).toBe("page=2");
  });

  it("returns empty string for empty params", () => {
    expect(buildQuery({})).toBe("");
  });
});

describe("withQuery", () => {
  it("returns path unchanged when no params", () => {
    expect(withQuery("/items")).toBe("/items");
  });

  it("appends query string to path", () => {
    expect(withQuery("/items", { page: "1" })).toBe("/items?page=1");
  });

  it("appends to existing query string", () => {
    expect(withQuery("/items?sort=asc", { page: "1" })).toBe("/items?sort=asc&page=1");
  });
});

describe("parseQuery", () => {
  it("parses a query string", () => {
    expect(parseQuery("?q=ai&page=2")).toEqual({ q: "ai", page: "2" });
  });

  it("parses a query string without leading ?", () => {
    expect(parseQuery("q=ai")).toEqual({ q: "ai" });
  });

  it("returns empty object for empty string", () => {
    expect(parseQuery("")).toEqual({});
  });

  it("handles URLSearchParams input", () => {
    const params = new URLSearchParams("a=1&b=2");
    expect(parseQuery(params)).toEqual({ a: "1", b: "2" });
  });

  it("preserves the last value for duplicate keys", () => {
    expect(parseQuery("a=1&a=2")).toEqual({ a: "2" });
  });
});

describe("mergeQuery", () => {
  it("adds new params", () => {
    expect(mergeQuery("?existing=true", { new: "value" })).toBe("?existing=true&new=value");
  });

  it("overrides existing params", () => {
    expect(mergeQuery("?page=1&sort=asc", { page: "2" })).toBe("?page=2&sort=asc");
  });

  it("removes params set to null", () => {
    expect(mergeQuery("?page=1&sort=asc", { page: null })).toBe("?sort=asc");
  });

  it("removes params set to undefined", () => {
    expect(mergeQuery("?page=1", { page: undefined })).toBe("");
  });

  it("handles empty current query", () => {
    expect(mergeQuery("", { page: "1" })).toBe("?page=1");
  });

  it("handles URLSearchParams input", () => {
    const current = new URLSearchParams("a=1");
    expect(mergeQuery(current, { b: "2" })).toBe("?a=1&b=2");
  });
});
