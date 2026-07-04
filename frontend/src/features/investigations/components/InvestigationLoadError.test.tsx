import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InvestigationLoadError } from "./InvestigationLoadError";

afterEach(cleanup);

describe("InvestigationLoadError", () => {
  it("renders error message", () => {
    render(<InvestigationLoadError />);
    expect(
      screen.getByText("Failed to load investigation"),
    ).toBeInTheDocument();
  });

  it("renders default description when no message is provided", () => {
    render(<InvestigationLoadError />);
    expect(
      screen.getByText(/An error occurred while loading the investigation/),
    ).toBeInTheDocument();
  });

  it("renders custom message when provided", () => {
    render(<InvestigationLoadError message="Custom error message" />);
    expect(screen.getByText("Custom error message")).toBeInTheDocument();
  });

  it("renders retry button when onRetry is provided", () => {
    const onRetry = vi.fn();
    render(<InvestigationLoadError onRetry={onRetry} />);
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("calls onRetry when retry button is clicked", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(<InvestigationLoadError onRetry={onRetry} />);
    await user.click(screen.getByText("Try again"));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("does not render retry button when onRetry is not provided", () => {
    render(<InvestigationLoadError />);
    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
  });

  it("has an alert role", () => {
    render(<InvestigationLoadError />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
