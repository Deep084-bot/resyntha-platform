import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Investigation } from "@/types";

import { InvestigationHeader } from "../InvestigationHeader";

const runContextValue = {
  running: false,
  run: vi.fn(),
  isStarting: false,
  latestExecution: null,
  stages: [],
  error: null,
};

vi.mock("../InvestigationRunContext", () => ({
  useInvestigationRun: () => runContextValue,
}));

afterEach(cleanup);

const mockInvestigation: Investigation = {
  id: "inv-1",
  title: "Test Investigation",
  topic: "Machine Learning Research",
  status: "completed",
  paper_limit: 10,
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-20T14:30:00Z",
  metadata: null,
};

function renderHeader(props: Partial<Parameters<typeof InvestigationHeader>[0]> = {}) {
  return render(
    <MemoryRouter>
      <InvestigationHeader
        investigation={mockInvestigation}
        {...props}
      />
    </MemoryRouter>,
  );
}

describe("InvestigationHeader", () => {
  it("renders investigation title", () => {
    renderHeader();
    expect(screen.getByText("Test Investigation")).toBeInTheDocument();
  });

  it("renders investigation topic", () => {
    renderHeader();
    expect(screen.getByText("Machine Learning Research")).toBeInTheDocument();
  });

  it("renders status badge", () => {
    renderHeader();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("renders created date", () => {
    renderHeader();
    expect(screen.getByText(/Created Jan 15, 2025/)).toBeInTheDocument();
  });

  it("renders updated date", () => {
    renderHeader();
    expect(screen.getByText(/Updated Jan 20, 2025/)).toBeInTheDocument();
  });

  it("renders paper limit", () => {
    renderHeader();
    expect(screen.getByText(/Paper limit: 10/)).toBeInTheDocument();
  });

  it("calls onDelete when delete button is clicked", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    renderHeader({ onDelete });

    const deleteBtn = screen.getByRole("button", { name: /delete/i });
    await user.click(deleteBtn);
    expect(onDelete).toHaveBeenCalledOnce();
  });

  it("calls onEdit when edit button is clicked", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    renderHeader({ onEdit });

    const editBtn = screen.getByRole("button", { name: /edit/i });
    await user.click(editBtn);
    expect(onEdit).toHaveBeenCalledOnce();
  });

  it("shows run investigation when there has never been a completed execution", () => {
    renderHeader({ hasCompletedExecution: false });
    expect(screen.getByText("Run Investigation")).toBeInTheDocument();
  });

  it("shows rerun when a completed execution exists", () => {
    renderHeader({ hasCompletedExecution: true });
    expect(screen.getByText("Re-run")).toBeInTheDocument();
  });

  it("does not render edit/delete buttons when callbacks are not provided", () => {
    renderHeader();
    expect(screen.queryByRole("button", { name: /edit/i })).not.toBeInTheDocument();
    expect(screen.getByText("Run Investigation")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
  });
});
