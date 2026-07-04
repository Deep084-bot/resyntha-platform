import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Artifact } from "@/types";

import { ArtifactList } from "../components/ArtifactList";

afterEach(cleanup);

const MOCK_ARTIFACTS: Artifact[] = [
  {
    id: "a1",
    investigation_id: "inv1",
    artifact_type: "final_report",
    version: 1,
    status: "ready",
    payload: null,
    created_at: "2025-01-15T10:00:00Z",
    updated_at: "2025-01-15T12:00:00Z",
  },
  {
    id: "a2",
    investigation_id: "inv1",
    artifact_type: "paper_collection",
    version: 2,
    status: "generating",
    payload: null,
    created_at: "2025-01-14T10:00:00Z",
    updated_at: "2025-01-14T12:00:00Z",
  },
];

describe("ArtifactList", () => {
  it("renders all artifacts", () => {
    render(
      <ArtifactList
        artifacts={MOCK_ARTIFACTS}
        selectedId={undefined}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByText("Final Report")).toBeInTheDocument();
    expect(screen.getByText("Paper Collection")).toBeInTheDocument();
  });

  it("has list role", () => {
    render(
      <ArtifactList
        artifacts={MOCK_ARTIFACTS}
        selectedId={undefined}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByRole("list")).toBeInTheDocument();
  });

  it("has list items", () => {
    render(
      <ArtifactList
        artifacts={MOCK_ARTIFACTS}
        selectedId={undefined}
        onSelect={vi.fn()}
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
  });

  it("highlights selected artifact", () => {
    render(
      <ArtifactList
        artifacts={MOCK_ARTIFACTS}
        selectedId="a1"
        onSelect={vi.fn()}
      />,
    );
    const buttons = screen.getAllByRole("button");
    const a1Btn = buttons.find((b) => b.textContent?.includes("Final Report"));
    expect(a1Btn).toHaveAttribute("aria-pressed", "true");
  });
});
