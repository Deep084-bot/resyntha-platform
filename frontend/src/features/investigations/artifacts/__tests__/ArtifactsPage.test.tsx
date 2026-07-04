import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ArtifactsPage } from "../pages/ArtifactsPage";

afterEach(cleanup);

vi.mock("@/hooks/useArtifacts", () => ({
  useArtifacts: vi.fn(),
}));

import { useArtifacts } from "@/hooks/useArtifacts";

const MOCK_ARTIFACTS = [
  {
    id: "a1",
    investigation_id: "inv1",
    artifact_type: "final_report",
    version: 1,
    status: "ready",
    payload: { content: "# Final Report" },
    created_at: "2025-01-15T10:00:00Z",
    updated_at: "2025-01-15T12:00:00Z",
  },
];

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/investigations/inv1/artifacts"]}>
      <Routes>
        <Route
          path="/investigations/:id/artifacts"
          element={<ArtifactsPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ArtifactsPage", () => {
  beforeEach(() => {
    vi.mocked(useArtifacts).mockReturnValue({
      data: MOCK_ARTIFACTS,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useArtifacts>);
  });

  it("renders section header", () => {
    renderPage();
    expect(screen.getByText("Artifacts")).toBeInTheDocument();
  });

  it("renders artifact count", () => {
    renderPage();
    expect(screen.getByText("1 artifact generated")).toBeInTheDocument();
  });

  it("renders artifact list", () => {
    renderPage();
    expect(screen.getByText("Final Report")).toBeInTheDocument();
  });

  it("renders preview placeholder initially", () => {
    renderPage();
    expect(
      screen.getByText("Select an artifact to preview"),
    ).toBeInTheDocument();
  });

  it("selects artifact and shows preview on click", async () => {
    const user = userEvent.setup();
    renderPage();
    const btn = screen.getByRole("button", { name: /final report artifact/i });
    await user.click(btn);
    // After selection, the preview section shows the artifact content
    const previewRegion = screen.getByLabelText("Artifact markdown preview");
    expect(previewRegion).toBeInTheDocument();
  });

  it("renders loading state", () => {
    vi.mocked(useArtifacts).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useArtifacts>);
    renderPage();
    expect(screen.getByText("Artifacts")).toBeInTheDocument();
  });

  it("renders error state", () => {
    vi.mocked(useArtifacts).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("Failed"),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useArtifacts>);
    renderPage();
    expect(
      screen.getByText("Failed to load artifacts"),
    ).toBeInTheDocument();
  });

  it("renders empty state", () => {
    vi.mocked(useArtifacts).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useArtifacts>);
    renderPage();
    expect(screen.getByText("No artifacts yet")).toBeInTheDocument();
  });
});
