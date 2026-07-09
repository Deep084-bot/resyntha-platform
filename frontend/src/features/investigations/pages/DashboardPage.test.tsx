import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Investigation } from "@/types";

afterEach(cleanup);

/* ── Mock investigation hooks ────────────────────────────────── */

const mockInvestigations: Investigation[] = [
  {
    id: "inv-1",
    title: "Alpha Project",
    topic: "Machine Learning",
    status: "completed",
    paper_limit: 10,
    created_at: "2025-01-15T10:00:00Z",
    updated_at: "2025-01-20T14:30:00Z",
    metadata: null,
  },
  {
    id: "inv-2",
    title: "Beta Research",
    topic: "NLP",
    status: "retrieving",
    paper_limit: 5,
    created_at: "2025-02-01T08:00:00Z",
    updated_at: "2025-02-05T12:00:00Z",
    metadata: null,
  },
  {
    id: "inv-3",
    title: "Gamma Study",
    topic: "Computer Vision",
    status: "failed",
    paper_limit: 20,
    created_at: "2024-12-01T09:00:00Z",
    updated_at: "2024-12-10T16:00:00Z",
    metadata: null,
  },
];

const mockMutate = vi.fn();
const mockReset = vi.fn();

vi.mock("@/hooks/useInvestigations", () => ({
  useInvestigations: vi.fn(() => ({
    data: mockInvestigations,
    isLoading: false,
    isError: false,
  })),
  useCreateInvestigation: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
    isError: false,
    error: null,
    reset: mockReset,
  })),
  useDeleteInvestigation: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
    isError: false,
    error: null,
    reset: mockReset,
  })),
}));

/* ── Lazy import so mocks apply before React hooks run ───────── */

async function renderPage() {
  const { DashboardPage } = await import("./DashboardPage");
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  );
}

describe("DashboardPage", () => {
  beforeEach(() => {
    mockMutate.mockReset();
    mockReset.mockReset();
  });

  it("renders welcome header", async () => {
    await renderPage();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(
      screen.getByText(/welcome to resyntha/i),
    ).toBeInTheDocument();
  });

  it("renders New Investigation button", async () => {
    await renderPage();
    expect(
      screen.getByRole("button", { name: /new investigation/i }),
    ).toBeInTheDocument();
  });

  it("renders QuickStats with correct counts", async () => {
    await renderPage();
    // 3 total: 1 completed, 1 running (retrieving counts as running), 1 failed
    expect(screen.getByText("Total Investigations")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders investigation cards", async () => {
    await renderPage();
    const alphaItems = screen.getAllByText("Alpha Project");
    expect(alphaItems.length).toBeGreaterThanOrEqual(1);
    const betaItems = screen.getAllByText("Beta Research");
    expect(betaItems.length).toBeGreaterThanOrEqual(1);
    const gammaItems = screen.getAllByText("Gamma Study");
    expect(gammaItems.length).toBeGreaterThanOrEqual(1);
  });

  it("renders search input", async () => {
    await renderPage();
    expect(
      screen.getByRole("searchbox"),
    ).toBeInTheDocument();
  });

  it("filters investigations by search", async () => {
    const user = userEvent.setup();
    await renderPage();

    const searchInput = screen.getByRole("searchbox");
    await user.type(searchInput, "Alpha");

    const alphaItems = screen.getAllByText("Alpha Project");
    expect(alphaItems.length).toBeGreaterThanOrEqual(1);
    const betaItems = screen.getAllByText("Beta Research");
    expect(betaItems.length).toBe(1);
    const gammaItems = screen.getAllByText("Gamma Study");
    expect(gammaItems.length).toBe(1);
  });

  it("renders Recent Activity section with investigation items", async () => {
    await renderPage();
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    const alphaItems = screen.getAllByText("Alpha Project");
    expect(alphaItems.length).toBeGreaterThanOrEqual(1);
    const betaItems = screen.getAllByText("Beta Research");
    expect(betaItems.length).toBeGreaterThanOrEqual(1);
  });

  it("renders empty activity state when no investigations exist", async () => {
    vi.mocked(
      (await import("@/hooks/useInvestigations")).useInvestigations,
    ).mockReturnValueOnce({
      data: [],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof import("@/hooks/useInvestigations").useInvestigations>);
    await renderPage();
    expect(
      screen.getByText(/recent activity will appear here/i),
    ).toBeInTheDocument();
  });
});
