import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Artifact, Execution, Paper, TimelineEvent } from "@/types";

afterEach(cleanup);

const mockPapers: Paper[] = [
  {
    id: "paper-1",
    title: "Deep Learning Review",
    abstract: "A comprehensive review",
    authors: ["Author A", "Author B"],
    doi: "10.1234/test",
    venue: "NeurIPS",
    year: 2024,
    citation_count: 42,
    url: null,
    source: "arxiv",
    score: 0.95,
    created_at: "2025-01-16T10:00:00Z",
    updated_at: "2025-01-16T10:00:00Z",
  },
];

const mockArtifacts: Artifact[] = [
  {
    id: "art-1",
    investigation_id: "inv-1",
    artifact_type: "paper_collection",
    version: 1,
    status: "ready",
    payload: null,
    created_at: "2025-01-17T10:00:00Z",
    updated_at: "2025-01-17T10:00:00Z",
  },
];

const mockExecutions: Execution[] = [
  {
    id: "exec-1",
    investigation_id: "inv-1",
    status: "completed",
    trigger: "manual",
    created_by: null,
    started_at: "2025-01-16T10:00:00Z",
    completed_at: "2025-01-16T11:00:00Z",
    created_at: "2025-01-16T09:00:00Z",
    updated_at: "2025-01-16T11:00:00Z",
    metadata: {},
  },
];

const mockTimeline: TimelineEvent[] = [
  {
    stage: "retrieving",
    status: "success",
    message: "Papers retrieved successfully",
    created_at: "2025-01-16T10:30:00Z",
  },
];

let usePapersResult = { data: mockPapers, isLoading: false, isError: false };
let useArtifactsResult = { data: mockArtifacts, isLoading: false, isError: false };
let useExecsResult = { data: mockExecutions, isLoading: false };
let useTimelineResult = { data: mockTimeline, isLoading: false };

vi.mock("@/hooks/useRetrieval", () => ({
  usePapers: vi.fn(() => usePapersResult),
}));

vi.mock("@/hooks/useArtifacts", () => ({
  useArtifacts: vi.fn(() => useArtifactsResult),
}));

vi.mock("@/hooks/useExecutions", () => ({
  useExecutions: vi.fn(() => useExecsResult),
  useLatestExecution: vi.fn(() => useExecsResult),
}));

vi.mock("@/hooks/useInvestigations", () => ({
  useTimeline: vi.fn(() => useTimelineResult),
}));

async function renderOverviewPage() {
  const { OverviewPage } = await import("../OverviewPage");
  return render(
    <MemoryRouter initialEntries={["/investigations/inv-1"]}>
      <Routes>
        <Route path="/investigations/:id" element={<OverviewPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OverviewPage", () => {
  it("renders stat cards", async () => {
    await renderOverviewPage();
    expect(screen.getByText("Papers Retrieved")).toBeInTheDocument();
    expect(screen.getByText("Artifacts Created")).toBeInTheDocument();
    expect(screen.getByText("Executions")).toBeInTheDocument();
    expect(screen.getByText("Avg. Execution Duration")).toBeInTheDocument();
  });

  it("displays correct paper count", async () => {
    await renderOverviewPage();
    const allOnes = screen.getAllByText("1");
    expect(allOnes.length).toBeGreaterThanOrEqual(2);
  });

  it("renders latest execution section", async () => {
    await renderOverviewPage();
    expect(screen.getByText("Latest Execution")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("renders recent artifacts section", async () => {
    await renderOverviewPage();
    expect(screen.getByText("Recent Artifacts")).toBeInTheDocument();
    expect(screen.getByText("paper_collection")).toBeInTheDocument();
  });

  it("renders recent activity section", async () => {
    await renderOverviewPage();
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    expect(
      screen.getByText("Papers retrieved successfully"),
    ).toBeInTheDocument();
  });

  it("shows empty state when no executions exist", async () => {
    useExecsResult = { data: [], isLoading: false };
    useTimelineResult = { data: [], isLoading: false };

    const { OverviewPage } = await import("../OverviewPage");
    render(
      <MemoryRouter initialEntries={["/investigations/inv-1"]}>
        <Routes>
          <Route path="/investigations/:id" element={<OverviewPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText("No executions have been run yet."),
    ).toBeInTheDocument();
  });
});
