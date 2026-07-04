import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { InvestigationTabs } from "../InvestigationTabs";
import type { TabDefinition } from "../InvestigationTabs";

afterEach(cleanup);

const TABS: TabDefinition[] = [
  { label: "Overview", to: "" },
  { label: "Papers", to: "papers" },
  { label: "Landscape", to: "landscape" },
  { label: "Artifacts", to: "artifacts" },
  { label: "Executions", to: "executions" },
];

function renderTabs(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/investigations/:id" element={<InvestigationTabs tabs={TABS} />}>
          <Route path="papers" element={<div>Papers Content</div>} />
          <Route path="landscape" element={<div>Landscape Content</div>} />
          <Route path="artifacts" element={<div>Artifacts Content</div>} />
          <Route path="executions" element={<div>Executions Content</div>} />
          <Route index element={<div>Overview Content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("InvestigationTabs", () => {
  it("renders all tab labels", () => {
    renderTabs("/investigations/test-123");
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Papers")).toBeInTheDocument();
    expect(screen.getByText("Landscape")).toBeInTheDocument();
    expect(screen.getByText("Artifacts")).toBeInTheDocument();
    expect(screen.getByText("Executions")).toBeInTheDocument();
  });

  it("marks the Overview tab as selected by default", () => {
    renderTabs("/investigations/test-123");
    const overviewTab = screen.getByText("Overview");
    expect(overviewTab).toHaveAttribute("aria-selected", "true");
    const papersTab = screen.getByText("Papers");
    expect(papersTab).toHaveAttribute("aria-selected", "false");
  });

  it("marks the correct tab as selected based on current path", () => {
    renderTabs("/investigations/test-123/papers");
    const papersTab = screen.getByText("Papers");
    expect(papersTab).toHaveAttribute("aria-selected", "true");
    const overviewTab = screen.getByText("Overview");
    expect(overviewTab).toHaveAttribute("aria-selected", "false");
  });

  it("links each tab to the correct href", () => {
    renderTabs("/investigations/test-123");

    const papersLink = screen.getByText("Papers").closest("a");
    expect(papersLink).toHaveAttribute("href", "/investigations/test-123/papers");

    const overviewLink = screen.getByText("Overview").closest("a");
    expect(overviewLink).toHaveAttribute("href", "/investigations/test-123");

    const landscapeLink = screen.getByText("Landscape").closest("a");
    expect(landscapeLink).toHaveAttribute("href", "/investigations/test-123/landscape");
  });

  it("shows active indicator for selected tab", () => {
    renderTabs("/investigations/test-123/artifacts");

    const artifactsTab = screen.getByText("Artifacts");
    const parentContainer = artifactsTab.closest('[role="tab"]');
    expect(parentContainer?.querySelector(".rounded-full")).toBeTruthy();
  });
});
