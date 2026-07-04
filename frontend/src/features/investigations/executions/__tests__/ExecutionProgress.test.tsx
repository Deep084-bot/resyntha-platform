import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { Execution, ExecutionStage } from "@/types";

import { ExecutionProgress } from "../components/ExecutionProgress";

afterEach(cleanup);

const RUNNING_EXECUTION: Execution = {
  id: "e1",
  investigation_id: "inv1",
  status: "running",
  trigger: "manual",
  created_by: null,
  started_at: "2025-01-01T10:00:00Z",
  completed_at: null,
  created_at: "2025-01-01T10:00:00Z",
  updated_at: "2025-01-01T10:00:00Z",
  metadata: {},
};

function makeStage(id: string, status: ExecutionStage["status"]): ExecutionStage {
  return {
    id,
    execution_id: "e1",
    stage_name: `stage-${id}`,
    status,
    attempt: 1,
    started_at: "2025-01-01T10:00:00Z",
    completed_at: status === "running" ? null : "2025-01-01T10:05:00Z",
    duration_ms: status === "running" ? null : 300000,
    error_message: status === "failed" ? "Error" : null,
    created_at: "2025-01-01T10:00:00Z",
  };
}

describe("ExecutionProgress", () => {
  it("renders progress label", () => {
    const stages = [makeStage("1", "completed"), makeStage("2", "running")];
    render(<ExecutionProgress execution={RUNNING_EXECUTION} stages={stages} />);
    expect(screen.getByText("In Progress")).toBeInTheDocument();
  });

  it("shows completed label for terminal executions", () => {
    const stages = [makeStage("1", "completed"), makeStage("2", "completed")];
    const completedExecution = { ...RUNNING_EXECUTION, status: "completed" as const, completed_at: "2025-01-01T10:30:00Z" };
    render(<ExecutionProgress execution={completedExecution} stages={stages} />);
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it("renders stage count", () => {
    const stages = [makeStage("1", "completed"), makeStage("2", "running")];
    render(<ExecutionProgress execution={RUNNING_EXECUTION} stages={stages} />);
    expect(screen.getByText(/1\/2 stages/)).toBeInTheDocument();
  });

  it("shows failed count when stages have failed", () => {
    const stages = [
      makeStage("1", "completed"),
      makeStage("2", "failed"),
    ];
    render(<ExecutionProgress execution={RUNNING_EXECUTION} stages={stages} />);
    expect(screen.getByText(/1 failed/)).toBeInTheDocument();
  });

  it("renders progress bar with correct aria attributes", () => {
    const stages = [makeStage("1", "completed"), makeStage("2", "running")];
    render(<ExecutionProgress execution={RUNNING_EXECUTION} stages={stages} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "50");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("renders percentage text", () => {
    const stages = [makeStage("1", "completed")];
    const completedExecution = { ...RUNNING_EXECUTION, status: "completed" as const, completed_at: "2025-01-01T10:30:00Z" };
    render(<ExecutionProgress execution={completedExecution} stages={stages} />);
    expect(screen.getByText("100% complete")).toBeInTheDocument();
  });

  it("handles zero stages gracefully", () => {
    render(<ExecutionProgress execution={RUNNING_EXECUTION} stages={[]} />);
    expect(screen.getByText("0% complete")).toBeInTheDocument();
  });
});
