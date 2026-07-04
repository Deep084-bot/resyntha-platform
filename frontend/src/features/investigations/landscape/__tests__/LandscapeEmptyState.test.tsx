import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { LandscapeEmptyState } from "../components/LandscapeEmptyState";

afterEach(cleanup);

describe("LandscapeEmptyState", () => {
  it("renders empty state message", () => {
    render(<LandscapeEmptyState />);
    expect(
      screen.getByText("No landscape data yet"),
    ).toBeInTheDocument();
  });

  it("renders explanation text", () => {
    render(<LandscapeEmptyState />);
    expect(
      screen.getByText(/landscape analysis becomes available/i),
    ).toBeInTheDocument();
  });

  it("has status role", () => {
    render(<LandscapeEmptyState />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
