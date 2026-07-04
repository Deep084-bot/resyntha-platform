import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { ExecutionStage } from "@/types";

import { ExecutionTimeline } from "../components/ExecutionTimeline";

afterEach(cleanup);

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
    status: "running",
    attempt: 1,
    started_at: "2025-01-01T10:05:00Z",
    completed_at: null,
    duration_ms: null,
    error_message: null,
    created_at: "2025-01-01T10:05:00Z",
  },
];

describe("ExecutionTimeline", () => {
  it("renders all stages", () => {
    render(<ExecutionTimeline stages={STAGES} />);
    expect(screen.getByText("retrieval")).toBeInTheDocument();
    expect(screen.getByText("extraction")).toBeInTheDocument();
  });

  it("has list role", () => {
    render(<ExecutionTimeline stages={STAGES} />);
    expect(screen.getByRole("list")).toBeInTheDocument();
  });

  it("renders list items", () => {
    render(<ExecutionTimeline stages={STAGES} />);
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
  });

  it("shows empty state when no stages", () => {
    render(<ExecutionTimeline stages={[]} />);
    expect(screen.getByText("No stages recorded.")).toBeInTheDocument();
  });
});
