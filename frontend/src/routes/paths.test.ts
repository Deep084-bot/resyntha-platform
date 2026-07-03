import { describe, expect, it } from "vitest";

import { ROUTES } from "./paths";

describe("ROUTES", () => {
  it("HOME is /", () => {
    expect(ROUTES.HOME).toBe("/");
  });

  it("PIPELINE is /pipeline", () => {
    expect(ROUTES.PIPELINE).toBe("/pipeline");
  });

  it("SETTINGS is /settings", () => {
    expect(ROUTES.SETTINGS).toBe("/settings");
  });

  it("INVESTIGATION builds a path with id", () => {
    expect(ROUTES.INVESTIGATION("abc-123")).toBe("/investigations/abc-123");
  });

  it("INVESTIGATION_TIMELINE builds a path with id", () => {
    expect(ROUTES.INVESTIGATION_TIMELINE("abc")).toBe("/investigations/abc/timeline");
  });

  it("INVESTIGATION_ARTIFACTS builds a path with id", () => {
    expect(ROUTES.INVESTIGATION_ARTIFACTS("abc")).toBe("/investigations/abc/artifacts");
  });

  it("INVESTIGATION_PAPERS builds a path with id", () => {
    expect(ROUTES.INVESTIGATION_PAPERS("abc")).toBe("/investigations/abc/papers");
  });

  it("INVESTIGATION_EXECUTIONS builds a path with id", () => {
    expect(ROUTES.INVESTIGATION_EXECUTIONS("abc")).toBe("/investigations/abc/executions");
  });

  it("INVESTIGATION_VALIDATION builds a path with id", () => {
    expect(ROUTES.INVESTIGATION_VALIDATION("abc")).toBe("/investigations/abc/validation");
  });

  it("INVESTIGATION_KNOWLEDGE builds a path with id", () => {
    expect(ROUTES.INVESTIGATION_KNOWLEDGE("abc")).toBe("/investigations/abc/knowledge");
  });

  it("INVESTIGATION_ANALYSIS builds a path with id", () => {
    expect(ROUTES.INVESTIGATION_ANALYSIS("abc")).toBe("/investigations/abc/analysis");
  });

  it("INVESTIGATION_GAPS builds a path with id", () => {
    expect(ROUTES.INVESTIGATION_GAPS("abc")).toBe("/investigations/abc/gaps");
  });

  it("INVESTIGATION_COPILOT builds a path with id", () => {
    expect(ROUTES.INVESTIGATION_COPILOT("abc")).toBe("/investigations/abc/copilot");
  });
});
