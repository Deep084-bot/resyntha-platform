import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import type { ExecutionStage } from "@/types";

import { ExecutionLogPreview } from "../components/ExecutionLogPreview";

afterEach(cleanup);

function makeStage(
  id: string,
  status: ExecutionStage["status"],
  error_message: string | null = null,
): ExecutionStage {
  return {
    id,
    execution_id: "e1",
    stage_name: `stage-${id}`,
    status,
    attempt: 1,
    started_at: "2025-01-01T10:00:00Z",
    completed_at: status === "running" ? null : "2025-01-01T10:05:00Z",
    duration_ms: 300000,
    error_message,
    created_at: "2025-01-01T10:00:00Z",
  };
}

describe("ExecutionLogPreview", () => {
  it("renders log section heading", () => {
    const stages = [makeStage("1", "completed")];
    render(<ExecutionLogPreview stages={stages} />);
    expect(screen.getByText("Logs")).toBeInTheDocument();
  });

  it("renders completion message for completed stages", () => {
    const stages = [makeStage("1", "completed")];
    render(<ExecutionLogPreview stages={stages} />);
    expect(
      screen.getByText(/stage-1 completed successfully/),
    ).toBeInTheDocument();
  });

  it("renders running message for running stages", () => {
    const stages = [makeStage("1", "running")];
    render(<ExecutionLogPreview stages={stages} />);
    expect(
      screen.getByText(/stage-1 stage is running/),
    ).toBeInTheDocument();
  });

  it("renders error message for failed stages", () => {
    const stages = [makeStage("1", "failed", "Connection error")];
    render(<ExecutionLogPreview stages={stages} />);
    expect(screen.getByText("Connection error")).toBeInTheDocument();
  });

  it("shows expand button when more than 5 entries", () => {
    const stages = Array.from({ length: 6 }).map((_, i) =>
      makeStage(String(i), "completed"),
    );
    render(<ExecutionLogPreview stages={stages} />);
    expect(screen.getByText(/Show all \(6 entries\)/)).toBeInTheDocument();
  });

  it("expands all logs on click", async () => {
    const user = userEvent.setup();
    const stages = Array.from({ length: 6 }).map((_, i) =>
      makeStage(String(i), "completed"),
    );
    render(<ExecutionLogPreview stages={stages} />);
    const btn = screen.getByRole("button", { name: /show all logs/i });
    await user.click(btn);
    expect(screen.getByText(/Show fewer/)).toBeInTheDocument();
  });

  it("shows empty state when no loggable stages", () => {
    const stages = [makeStage("1", "pending")];
    render(<ExecutionLogPreview stages={stages} />);
    expect(
      screen.getByText("No log entries available."),
    ).toBeInTheDocument();
  });

  it("hides expand button when 5 or fewer entries", () => {
    const stages = Array.from({ length: 5 }).map((_, i) =>
      makeStage(String(i), "completed"),
    );
    render(<ExecutionLogPreview stages={stages} />);
    expect(
      screen.queryByRole("button", { name: /show all logs/i }),
    ).not.toBeInTheDocument();
  });
});
