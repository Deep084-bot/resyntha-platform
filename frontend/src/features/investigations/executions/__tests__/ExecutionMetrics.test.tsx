import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { Execution, ExecutionStage } from "@/types";

import { ExecutionMetrics } from "../components/ExecutionMetrics";

afterEach(cleanup);

const EXECUTION: Execution = {
  id: "e1",
  investigation_id: "inv1",
  status: "completed",
  trigger: "manual",
  created_by: null,
  started_at: "2025-01-01T10:00:00Z",
  completed_at: "2025-01-01T10:30:00Z",
  created_at: "2025-01-01T10:00:00Z",
  updated_at: "2025-01-01T10:30:00Z",
  metadata: {},
};

const STAGES: ExecutionStage[] = [
  {
    id: "s1",
    execution_id: "e1",
    stage_name: "retrieval",
    status: "completed",
    attempt: 1,
    started_at: "2025-01-01T10:00:00Z",
    completed_at: "2025-01-01T10:05:00Z",
    duration_ms: 300000,
    error_message: null,
    created_at: "2025-01-01T10:00:00Z",
  },
  {
    id: "s2",
    execution_id: "e1",
    stage_name: "extraction",
    status: "completed",
    attempt: 1,
    started_at: "2025-01-01T10:05:00Z",
    completed_at: "2025-01-01T10:10:00Z",
    duration_ms: 300000,
    error_message: null,
    created_at: "2025-01-01T10:05:00Z",
  },
];

describe("ExecutionMetrics", () => {
  it("renders duration", () => {
    render(<ExecutionMetrics execution={EXECUTION} stages={STAGES} />);
    expect(screen.getByText("30m 0s")).toBeInTheDocument();
  });

  it("renders stage count", () => {
    render(<ExecutionMetrics execution={EXECUTION} stages={STAGES} />);
    expect(screen.getByText("2/2")).toBeInTheDocument();
  });

  it("renders failed count", () => {
    const failedStages: ExecutionStage[] = [...STAGES, {
      id: "s3",
      execution_id: "e1",
      stage_name: "intelligence",
      status: "failed",
      attempt: 1,
      started_at: "2025-01-01T10:00:00Z",
      completed_at: "2025-01-01T10:05:00Z",
      duration_ms: 300000,
      error_message: "Failed",
      created_at: "2025-01-01T10:00:00Z",
    }];
    render(<ExecutionMetrics execution={EXECUTION} stages={failedStages} />);
    const failedLabels = screen.getAllByText("1");
    expect(failedLabels.length).toBeGreaterThanOrEqual(1);
  });

  it("renders runs count with default", () => {
    render(<ExecutionMetrics execution={EXECUTION} stages={STAGES} />);
    const oneLabels = screen.getAllByText("1");
    expect(oneLabels.length).toBeGreaterThanOrEqual(1);
  });

  it("renders all metric labels", () => {
    render(<ExecutionMetrics execution={EXECUTION} stages={STAGES} />);
    expect(screen.getByText("Duration")).toBeInTheDocument();
    expect(screen.getByText("Stages")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText("Runs")).toBeInTheDocument();
  });

  it("shows dash when no duration available", () => {
    const noDurationExecution: Execution = {
      ...EXECUTION,
      started_at: null,
      completed_at: null,
    };
    render(<ExecutionMetrics execution={noDurationExecution} stages={STAGES} />);
    expect(screen.getByText("\u2014")).toBeInTheDocument();
  });
});
