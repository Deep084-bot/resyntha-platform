import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ArtifactErrorState } from "../components/ArtifactErrorState";

afterEach(cleanup);

describe("ArtifactErrorState", () => {
  it("renders error message", () => {
    render(<ArtifactErrorState />);
    expect(
      screen.getByText("Failed to load artifacts"),
    ).toBeInTheDocument();
  });

  it("renders retry button when onRetry provided", () => {
    render(<ArtifactErrorState onRetry={vi.fn()} />);
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("calls onRetry when clicked", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(<ArtifactErrorState onRetry={onRetry} />);
    await user.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
