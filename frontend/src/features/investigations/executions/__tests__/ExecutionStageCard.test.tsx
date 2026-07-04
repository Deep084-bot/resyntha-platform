import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { ExecutionStage } from "@/types";

import { ExecutionStageCard } from "../components/ExecutionStageCard";

afterEach(cleanup);

const BASE_STAGE: ExecutionStage = {
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
};

function renderCard(stage = BASE_STAGE, isLast = false) {
  return render(<ExecutionStageCard stage={stage} isLast={isLast} />);
}

describe("ExecutionStageCard", () => {
  it("renders stage name", () => {
    renderCard();
    expect(screen.getByText("retrieval")).toBeInTheDocument();
  });

  it("renders stage name with underscores replaced by spaces", () => {
    renderCard({ ...BASE_STAGE, stage_name: "knowledge_graph" });
    expect(screen.getByText("knowledge graph")).toBeInTheDocument();
  });

  it("renders duration", () => {
    renderCard();
    expect(screen.getByText("5m 0s")).toBeInTheDocument();
  });

  it("renders started label", () => {
    renderCard();
    expect(screen.getByText(/Started/)).toBeInTheDocument();
  });

  it("renders finished label", () => {
    renderCard();
    expect(screen.getByText(/Finished/)).toBeInTheDocument();
  });

  it("shows attempt badge when attempt > 1", () => {
    renderCard({ ...BASE_STAGE, attempt: 3 });
    expect(screen.getByText("Attempt 3")).toBeInTheDocument();
  });

  it("hides attempt badge when attempt is 1", () => {
    renderCard();
    expect(screen.queryByText("Attempt 1")).not.toBeInTheDocument();
  });

  it("renders error message for failed stage", () => {
    renderCard({
      ...BASE_STAGE,
      status: "failed",
      error_message: "Connection timeout",
    });
    expect(screen.getByText("Connection timeout")).toBeInTheDocument();
  });

  it("renders running state with ping animation", () => {
    const { container } = renderCard({
      ...BASE_STAGE,
      status: "running",
      completed_at: null,
      duration_ms: null,
    });
    const pingEl = container.querySelector(".animate-ping");
    expect(pingEl).toBeInTheDocument();
  });

  it("renders pending state", () => {
    renderCard({
      ...BASE_STAGE,
      status: "pending",
      completed_at: null,
      duration_ms: null,
    });
    expect(screen.getByText("retrieval")).toBeInTheDocument();
  });

  it("renders skipped state", () => {
    renderCard({
      ...BASE_STAGE,
      status: "skipped",
    });
    expect(screen.getByText("retrieval")).toBeInTheDocument();
  });
});
