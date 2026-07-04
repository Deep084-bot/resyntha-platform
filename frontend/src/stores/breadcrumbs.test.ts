import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { useBreadcrumbStore } from "./breadcrumbs";

describe("useBreadcrumbStore", () => {
  afterEach(() => {
    useBreadcrumbStore.setState({ labels: {} });
  });

  it("starts with empty labels", () => {
    const { result } = renderHook(() => useBreadcrumbStore());
    expect(result.current.labels).toEqual({});
  });

  it("setLabel adds a label override", () => {
    const { result } = renderHook(() => useBreadcrumbStore());
    act(() => result.current.setLabel("inv-1", "My Investigation"));
    expect(result.current.labels).toEqual({ "inv-1": "My Investigation" });
  });

  it("setLabel overwrites an existing label", () => {
    const { result } = renderHook(() => useBreadcrumbStore());
    act(() => result.current.setLabel("inv-1", "First"));
    act(() => result.current.setLabel("inv-1", "Second"));
    expect(result.current.labels["inv-1"]).toBe("Second");
  });

  it("clearLabel removes a label override", () => {
    const { result } = renderHook(() => useBreadcrumbStore());
    act(() => result.current.setLabel("inv-1", "My Investigation"));
    act(() => result.current.clearLabel("inv-1"));
    expect(result.current.labels).toEqual({});
  });

  it("clearLabel does nothing for non-existent key", () => {
    const { result } = renderHook(() => useBreadcrumbStore());
    act(() => result.current.setLabel("inv-1", "My Investigation"));
    act(() => result.current.clearLabel("non-existent"));
    expect(result.current.labels).toEqual({ "inv-1": "My Investigation" });
  });
});
