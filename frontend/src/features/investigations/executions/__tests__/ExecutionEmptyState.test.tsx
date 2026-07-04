import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ExecutionEmptyState } from "../components/ExecutionEmptyState";

afterEach(cleanup);

describe("ExecutionEmptyState", () => {
  it("renders empty state title", () => {
    render(<ExecutionEmptyState />);
    expect(screen.getByText("No executions yet")).toBeInTheDocument();
  });

  it("renders hint text", () => {
    render(<ExecutionEmptyState />);
    expect(
      screen.getByText(/Run the retrieval pipeline/),
    ).toBeInTheDocument();
  });
});
