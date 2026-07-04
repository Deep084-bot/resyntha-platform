import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LandscapeErrorState } from "../components/LandscapeErrorState";

afterEach(cleanup);

describe("LandscapeErrorState", () => {
  it("renders error message", () => {
    render(<LandscapeErrorState />);
    expect(
      screen.getByText("Failed to load landscape"),
    ).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<LandscapeErrorState message="Custom error" />);
    expect(screen.getByText("Custom error")).toBeInTheDocument();
  });

  it("renders retry button when onRetry is provided", () => {
    render(<LandscapeErrorState onRetry={vi.fn()} />);
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("calls onRetry when retry button is clicked", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(<LandscapeErrorState onRetry={onRetry} />);
    await user.click(screen.getByText("Try again"));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("does not render retry button when onRetry is not provided", () => {
    render(<LandscapeErrorState />);
    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
  });

  it("has alert role", () => {
    render(<LandscapeErrorState />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
