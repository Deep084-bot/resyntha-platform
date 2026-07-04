import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ExecutionsPage } from "../pages/ExecutionsPage";

afterEach(cleanup);

vi.mock("@/hooks/useExecutions", () => ({
  useExecutions: vi.fn(),
  useExecutionStages: vi.fn(),
}));

import { useExecutions, useExecutionStages } from "@/hooks/useExecutions";

const mockExecutions = [
  {
    id: "e1",
    investigation_id: "inv1",
    status: "completed" as const,
    trigger: "manual",
    created_by: null,
    started_at: "2025-01-01T10:00:00Z",
    completed_at: "2025-01-01T10:30:00Z",
    created_at: "2025-01-01T10:00:00Z",
    updated_at: "2025-01-01T10:30:00Z",
    metadata: {},
  },
];

const mockStages = [
  {
    id: "s1",
    execution_id: "e1",
    stage_name: "retrieval",
    status: "completed" as const,
    attempt: 1,
    started_at: "2025-01-01T10:00:00Z",
    completed_at: "2025-01-01T10:05:00Z",
    duration_ms: 300000,
    error_message: null,
    created_at: "2025-01-01T10:00:00Z",
  },
];

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/investigations/inv1/executions"]}>
      <Routes>
        <Route
          path="/investigations/:id/executions"
          element={<ExecutionsPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ExecutionsPage", () => {
  beforeEach(() => {
    vi.mocked(useExecutions).mockReturnValue({
      data: mockExecutions,
      isLoading: false,
      isError: false,
      error: null,
    } as unknown as ReturnType<typeof useExecutions>);
    vi.mocked(useExecutionStages).mockReturnValue({
      data: mockStages,
      isLoading: false,
      isError: false,
      error: null,
    } as unknown as ReturnType<typeof useExecutionStages>);
  });

  it("renders section header", () => {
    renderPage();
    expect(screen.getByText("Executions")).toBeInTheDocument();
  });

  it("renders execution count", () => {
    renderPage();
    expect(screen.getByText("1 execution total")).toBeInTheDocument();
  });

  it("renders history section", () => {
    renderPage();
    expect(screen.getByText("History")).toBeInTheDocument();
  });

  it("renders pipeline stages heading", () => {
    renderPage();
    expect(screen.getByText("Pipeline Stages")).toBeInTheDocument();
  });

  it("renders stage name", () => {
    renderPage();
    expect(screen.getByText("retrieval")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    vi.mocked(useExecutions).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    } as unknown as ReturnType<typeof useExecutions>);
    renderPage();
    expect(screen.getByText("Executions")).toBeInTheDocument();
  });

  it("renders error state", () => {
    vi.mocked(useExecutions).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("Failed"),
    } as unknown as ReturnType<typeof useExecutions>);
    renderPage();
    expect(
      screen.getByText("Failed to load execution data"),
    ).toBeInTheDocument();
  });

  it("renders empty state", () => {
    vi.mocked(useExecutions).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    } as unknown as ReturnType<typeof useExecutions>);
    renderPage();
    expect(screen.getByText("No executions yet")).toBeInTheDocument();
  });
});
