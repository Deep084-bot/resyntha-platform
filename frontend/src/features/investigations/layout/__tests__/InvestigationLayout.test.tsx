import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Investigation } from "@/types";

afterEach(cleanup);

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

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

const mockMutate = vi.fn();
const mockReset = vi.fn();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let invResult: Record<string, any> = { data: mockInvestigation, isLoading: false, isError: false };

vi.mock("@/hooks/useInvestigations", () => ({
  useInvestigation: vi.fn(() => invResult),
  useDeleteInvestigation: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
    isError: false,
    error: null,
    reset: mockReset,
  })),
  useTimeline: vi.fn(() => ({
    data: [],
    isLoading: false,
  })),
}));

vi.mock("@/hooks/useExecutions", () => ({
  useExecutions: vi.fn(() => ({ data: [], isLoading: false })),
  useExecutionStages: vi.fn(() => ({ data: [], isLoading: false })),
  useRunInvestigation: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
  })),
}));

vi.mock("@/features/investigations/layout/InvestigationRunContext", () => ({
  InvestigationRunContextProvider: ({ children }: { children: React.ReactNode }) => children,
  useInvestigationRun: vi.fn(() => ({
    running: false,
    latestExecution: null,
    stages: [],
    run: vi.fn(),
    isStarting: false,
    error: null,
  })),
}));

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/investigations/inv-1"]}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
}

async function renderLayout(initialPath = "/investigations/inv-1") {
  const { InvestigationLayout } = await import("../InvestigationLayout");
  return render(
    <Wrapper>
      <Routes>
        <Route path="/investigations/:id" element={<InvestigationLayout />}>
          <Route index element={<div data-testid="child-content">Child Content</div>} />
        </Route>
      </Routes>
    </Wrapper>,
  );
}

describe("InvestigationLayout", () => {
  it("renders investigation title", async () => {
    await renderLayout();
    expect(screen.getByText("Test Investigation")).toBeInTheDocument();
  });

  it("renders investigation topic", async () => {
    await renderLayout();
    expect(screen.getByText("Machine Learning")).toBeInTheDocument();
  });

  it("renders tabs", async () => {
    await renderLayout();
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Papers")).toBeInTheDocument();
    expect(screen.getByText("Landscape")).toBeInTheDocument();
    expect(screen.getByText("Artifacts")).toBeInTheDocument();
    expect(screen.getByText("Executions")).toBeInTheDocument();
  });

  it("renders child route content via Outlet", async () => {
    await renderLayout();
    expect(screen.getByTestId("child-content")).toBeInTheDocument();
    expect(screen.getByText("Child Content")).toBeInTheDocument();
  });

  it("shows skeleton during loading state", async () => {
    invResult = { data: undefined, isLoading: true, isError: false };

    const { InvestigationLayout } = await import("../InvestigationLayout");
    const { container } = render(
      <Wrapper>
        <Routes>
          <Route path="/investigations/:id" element={<InvestigationLayout />} />
        </Routes>
      </Wrapper>,
    );

    const pulseEls = container.querySelectorAll(".animate-pulse");
    expect(pulseEls.length).toBeGreaterThanOrEqual(5);
  });

  it("shows error state when loading fails", async () => {
    invResult = { data: undefined, isLoading: false, isError: true };

    const { InvestigationLayout } = await import("../InvestigationLayout");
    render(
      <Wrapper>
        <Routes>
          <Route path="/investigations/:id" element={<InvestigationLayout />} />
        </Routes>
      </Wrapper>,
    );

    expect(
      screen.getByText("Failed to load investigation"),
    ).toBeInTheDocument();
  });

  it("shows not found state when data is falsy but not error", async () => {
    invResult = { data: null, isLoading: false, isError: false };

    const { InvestigationLayout } = await import("../InvestigationLayout");
    render(
      <Wrapper>
        <Routes>
          <Route path="/investigations/:id" element={<InvestigationLayout />} />
        </Routes>
      </Wrapper>,
    );

    expect(screen.getByText("Investigation not found")).toBeInTheDocument();
  });
});
