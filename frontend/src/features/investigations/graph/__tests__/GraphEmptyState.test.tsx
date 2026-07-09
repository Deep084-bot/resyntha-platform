import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { GraphEmptyState } from "../components/GraphEmptyState";

afterEach(cleanup);

describe("GraphEmptyState", () => {
  it("renders the empty state message", () => {
    render(<GraphEmptyState />);
    expect(
      screen.getByText("Research graph will appear once the investigation finishes."),
    ).toBeInTheDocument();
  });

  it("renders the hint text", () => {
    render(<GraphEmptyState />);
    expect(
      screen.getByText(/Run an investigation/),
    ).toBeInTheDocument();
  });

  it("has a status role", () => {
    render(<GraphEmptyState />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
