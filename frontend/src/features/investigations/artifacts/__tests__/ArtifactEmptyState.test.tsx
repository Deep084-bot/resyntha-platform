import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ArtifactEmptyState } from "../components/ArtifactEmptyState";

afterEach(cleanup);

describe("ArtifactEmptyState", () => {
  it("renders empty state title", () => {
    render(<ArtifactEmptyState />);
    expect(screen.getByText("No artifacts yet")).toBeInTheDocument();
  });

  it("renders hint text", () => {
    render(<ArtifactEmptyState />);
    expect(
      screen.getByText(/Artifacts will appear here/),
    ).toBeInTheDocument();
  });
});
