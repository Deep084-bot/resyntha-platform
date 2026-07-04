import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceErrorBoundary } from "./WorkspaceErrorBoundary";

afterEach(cleanup);

const ThrowError = ({ message }: { message?: string }) => {
  throw new Error(message ?? "Test error");
};

describe("WorkspaceErrorBoundary", () => {
  it("renders children when there is no error", () => {
    render(
      <WorkspaceErrorBoundary>
        <div>Normal content</div>
      </WorkspaceErrorBoundary>,
    );
    expect(screen.getByText("Normal content")).toBeInTheDocument();
  });

  it("renders error UI when a child throws", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <WorkspaceErrorBoundary>
        <ThrowError />
      </WorkspaceErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();

    vi.restoreAllMocks();
  });

  it("displays the error message when available", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <WorkspaceErrorBoundary>
        <ThrowError message="Custom error message" />
      </WorkspaceErrorBoundary>,
    );

    expect(screen.getByText("Custom error message")).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it("re-renders children after retry click when error resolves", async () => {
    const user = userEvent.setup();
    vi.spyOn(console, "error").mockImplementation(() => {});

    let shouldThrow = true;
    const FlakyComponent = () => {
      if (shouldThrow) {
        throw new Error("Flaky error");
      }
      return <div>Recovered content</div>;
    };

    render(
      <WorkspaceErrorBoundary key="boundary">
        <FlakyComponent />
      </WorkspaceErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    shouldThrow = false;
    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(screen.getByText("Recovered content")).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it("renders custom fallback when provided", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <WorkspaceErrorBoundary fallback={<div>Custom Fallback</div>}>
        <ThrowError />
      </WorkspaceErrorBoundary>,
    );

    expect(screen.getByText("Custom Fallback")).toBeInTheDocument();
    vi.restoreAllMocks();
  });
});
