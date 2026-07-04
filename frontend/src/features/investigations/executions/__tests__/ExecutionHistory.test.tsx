import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Execution } from "@/types";

import { ExecutionHistory } from "../components/ExecutionHistory";

afterEach(cleanup);

const EXECUTIONS: Execution[] = [
  {
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
  },
  {
    id: "e2",
    investigation_id: "inv1",
    status: "running",
    trigger: "scheduled",
    created_by: null,
    started_at: "2025-01-02T10:00:00Z",
    completed_at: null,
    created_at: "2025-01-02T10:00:00Z",
    updated_at: "2025-01-02T10:00:00Z",
    metadata: {},
  },
];

describe("ExecutionHistory", () => {
  it("renders section heading", () => {
    render(
      <ExecutionHistory
        executions={EXECUTIONS}
        selectedId={undefined}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByText("History")).toBeInTheDocument();
  });

  it("renders all executions", () => {
    render(
      <ExecutionHistory
        executions={EXECUTIONS}
        selectedId={undefined}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByText(/e1/)).toBeInTheDocument();
    expect(screen.getByText(/e2/)).toBeInTheDocument();
  });

  it("renders trigger info", () => {
    render(
      <ExecutionHistory
        executions={EXECUTIONS}
        selectedId={undefined}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByText("Trigger: manual")).toBeInTheDocument();
    expect(screen.getByText("Trigger: scheduled")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(
      <ExecutionHistory
        executions={EXECUTIONS}
        selectedId={undefined}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
  });

  it("calls onSelect when clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <ExecutionHistory
        executions={EXECUTIONS}
        selectedId={undefined}
        onSelect={onSelect}
      />,
    );
    await user.click(screen.getByText(/e1/));
    expect(onSelect).toHaveBeenCalledWith("e1");
  });

  it("marks selected execution as pressed", () => {
    render(
      <ExecutionHistory
        executions={EXECUTIONS}
        selectedId="e1"
        onSelect={vi.fn()}
      />,
    );
    // Get the first execution button (the one for e1)
    const btns = screen.getAllByRole("button");
    const e1Btn = btns.find((b) => b.textContent?.includes("e1"));
    expect(e1Btn).toBeDefined();
    expect(e1Btn).toHaveAttribute("aria-pressed", "true");
  });
});
