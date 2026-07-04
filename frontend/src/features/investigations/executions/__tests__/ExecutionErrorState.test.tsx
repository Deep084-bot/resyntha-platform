import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ExecutionErrorState } from "../components/ExecutionErrorState";

afterEach(cleanup);

describe("ExecutionErrorState", () => {
  it("renders error message", () => {
    render(<ExecutionErrorState />);
    expect(
      screen.getByText("Failed to load execution data"),
    ).toBeInTheDocument();
  });

  it("renders explanation text", () => {
    render(<ExecutionErrorState />);
    expect(
      screen.getByText(/error occurred while fetching execution details/i),
    ).toBeInTheDocument();
  });

  it("renders retry button when onRetry provided", () => {
    render(<ExecutionErrorState onRetry={vi.fn()} />);
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("does not render retry button without onRetry", () => {
    render(<ExecutionErrorState />);
    expect(
      screen.queryByRole("button", { name: /retry/i }),
    ).not.toBeInTheDocument();
  });

  it("calls onRetry when retry clicked", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(<ExecutionErrorState onRetry={onRetry} />);
    await user.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
