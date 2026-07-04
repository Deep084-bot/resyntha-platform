import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import type { Investigation } from "@/types";

import { InvestigationCard } from "./InvestigationCard";

afterEach(cleanup);

const mockInvestigation: Investigation = {
  id: "inv-1",
  title: "Test Investigation",
  topic: "Machine Learning",
  status: "completed",
  paper_limit: 10,
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-20T14:30:00Z",
  metadata: null,
};

function renderCard(inv: Investigation = mockInvestigation, onDelete?: () => void) {
  return render(
    <MemoryRouter>
      <InvestigationCard investigation={inv} onDelete={onDelete} />
    </MemoryRouter>,
  );
}

function getLinks() {
  return screen.getAllByRole("link").filter(
    (l) => l.getAttribute("href") === "/investigations/inv-1",
  );
}

describe("InvestigationCard", () => {
  it("renders title and topic", () => {
    renderCard();
    expect(screen.getByText("Test Investigation")).toBeInTheDocument();
    expect(screen.getByText("Machine Learning")).toBeInTheDocument();
  });

  it("renders created date", () => {
    renderCard();
    expect(screen.getByText(/Created Jan 15, 2025/)).toBeInTheDocument();
  });

  it("renders updated date", () => {
    renderCard();
    expect(screen.getByText(/Updated Jan 20, 2025/)).toBeInTheDocument();
  });

  it("renders status badge", () => {
    renderCard();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("links to investigation detail", () => {
    renderCard();
    expect(getLinks().length).toBeGreaterThanOrEqual(1);
  });

  it("shows delete trigger when onDelete is provided", () => {
    renderCard(mockInvestigation, () => {});
    expect(
      screen.getByRole("button", { name: /delete test investigation/i }),
    ).toBeInTheDocument();
  });

  it("does not show delete trigger when onDelete is not provided", () => {
    renderCard();
    expect(
      screen.queryByRole("button", { name: /delete/i }),
    ).not.toBeInTheDocument();
  });

  it("shows paper and execution counts when metadata has them", () => {
    const withCounts: Investigation = {
      ...mockInvestigation,
      metadata: { paper_count: 15, execution_count: 3 },
    };
    renderCard(withCounts);
    expect(screen.getByText("15 papers")).toBeInTheDocument();
    expect(screen.getByText("3 executions")).toBeInTheDocument();
  });

  it("does not show counts when metadata is null", () => {
    renderCard();
    expect(screen.queryByText(/papers/)).not.toBeInTheDocument();
    expect(screen.queryByText(/executions/)).not.toBeInTheDocument();
  });
});
